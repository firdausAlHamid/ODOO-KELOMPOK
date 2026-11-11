# -*- coding: utf-8 -*-
"""
============================================================
 gRPC NATIVE SERVER  (Pendekatan 2: Built-in / Environment Bootstrap)
============================================================

Script ini berjalan DI DALAM proses Odoo (in-process). Ia melakukan
Environment Bootstrap sehingga bisa menjalankan gRPC server dan sekaligus
mengakses database Odoo secara langsung melalui ORM (self.env / env),
TANPA menggunakan XML-RPC sama sekali.

Keuntungan:
  * Akses langsung ke ORM Odoo -> lebih cepat, type-safe, dan bisa
    memanggil method bisnis (action_submit, dst) langsung.
  * Tidak perlu autentikasi XML-RPC terpisah.

Cara kerja bootstrap:
    1. Inisialisasi konfigurasi Odoo (odoo.tools.config)
    2. Buka registry untuk database yang dituju
    3. Untuk tiap RPC, ambil cursor baru -> bangun Environment
       dengan SUPERUSER_ID -> akses env['bureaucracy.ticket']

Jalankan (dari root repo E:\\ODOO-KELOMPOK):
    python native_server.py

Catatan: jalankan dengan venv Odoo yang sama (venv\\Scripts\\python),
karena modul odoo harus tersedia.
"""

import os
import sys

# Tambahkan direktori grpc_ticketing ke sys.path agar stub bisa diimport
# saat script dijalankan dari root repo
sys.path.insert(0, os.path.dirname(__file__))

import logging
from concurrent import futures

import grpc

# Stub gRPC
import ticket_pb2
import ticket_pb2_grpc

# =============================================
# Konfigurasi
# =============================================
ODOO_CONF   = os.path.join(os.path.dirname(__file__), "..", "..", "odoo.conf")
ODOO_DB     = "odoo19"
GRPC_PORT   = 50052   # berbeda dari middleware (50051) agar bisa jalan bareng

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [NATIVE] %(levelname)s %(message)s",
)
_logger = logging.getLogger(__name__)


# =============================================
# Odoo Bootstrap
# =============================================
def _bootstrap_odoo():
    """
    Inisialisasi Odoo config + registry. Harus dipanggil sekali
    sebelum server menerima request.
    """
    import odoo
    from odoo.tools import config

    # Parse odoo.conf (berisi db_host, db_port, db_user, db_password, addons_path)
    conf_path = os.path.abspath(ODOO_CONF)
    _logger.info("Bootstrap Odoo dari config: %s", conf_path)

    # Inisialisasi config dari file odoo.conf + pilih database
    config.parse_config(["--config", conf_path])
    config["db_name"] = ODOO_DB

    # Bangun registry (load model definitions dari database, tanpa start HTTP server)
    registry = odoo.modules.registry.Registry(ODOO_DB)

    # Verifikasi modul terpasang
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        installed = env["ir.module.module"].search([
            ("name", "=", "bureaucracy_ticketing"),
            ("state", "=", "installed"),
        ])
        _logger.info("Bootstrap OK. Modul 'bureaucracy_ticketing' terpasang: %s",
                     bool(installed))
    return registry


def _env():
    """
    Buka cursor baru dan bangun Environment sebagai SUPERUSER.
    Dipanggil di awal tiap RPC. Jangan lupa commit/close cursor
    (context manager `with registry.cursor()` sudah menangani).
    """
    import odoo
    registry = odoo.modules.registry.Registry(ODOO_DB)
    cr = registry.cursor()
    return cr, odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})


# Label mappings (sama dengan yang ada di model)
_PRIORITY_LABELS = {"0": "Rendah", "1": "Sedang", "2": "Tinggi", "3": "Sangat Mendesak"}
_STATE_LABELS = {
    "draft": "Draft", "submitted": "Diajukan", "in_progress": "Sedang Diproses",
    "resolved": "Selesai", "cancelled": "Dibatalkan",
}


def _ticket_to_pb(t) -> ticket_pb2.TicketData:
    """Ubah recordset bureaucracy.ticket menjadi TicketData protobuf."""
    return ticket_pb2.TicketData(
        id              = t.id,
        name            = t.name or "",
        title           = t.title or "",
        description     = (t.description or ""),
        location        = t.location or "",
        priority        = t.priority or "1",
        priority_label  = _PRIORITY_LABELS.get(t.priority, ""),
        state           = t.state or "draft",
        state_label     = _STATE_LABELS.get(t.state, ""),
        category_name   = t.category_id.name or "" if t.category_id else "",
        employee_name   = t.employee_id.name or "" if t.employee_id else "",
        department_name = t.department_id.name or "" if t.department_id else "",
        report_date     = str(t.report_date) if t.report_date else "",
    )


# =============================================
# Service Implementation
# =============================================
class TicketingNativeServicer(ticket_pb2_grpc.TicketServiceServicer):
    """
    Implementasi service gRPC yang mengakses ORM Odoo langsung.
    """

    # ---------- CREATE ----------
    def CreateTicket(self, request, context):
        _logger.info("CreateTicket: title=%r", request.title)
        cr, env = None, None
        try:
            if not request.title:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Field 'title' wajib diisi.")
                return ticket_pb2.CreateTicketResponse(success=False, message="title kosong")

            cr, env = _env()
            Ticket = env["bureaucracy.ticket"]

            vals = {
                "title":       request.title,
                "description": request.description,
                "location":    request.location,
                "priority":    request.priority or "1",
            }
            if request.category_id:
                vals["category_id"] = request.category_id
            if request.employee_id:
                vals["employee_id"] = request.employee_id

            new_ticket = Ticket.create(vals)
            cr.commit()
            _logger.info("Tiket dibuat id=%s name=%s", new_ticket.id, new_ticket.name)
            return ticket_pb2.CreateTicketResponse(
                success     = True,
                message     = "Tiket berhasil dibuat via Native (ORM langsung)",
                ticket_id   = new_ticket.id,
                ticket_name = new_ticket.name,
            )
        except Exception as e:
            if cr:
                cr.rollback()
            _logger.exception("CreateTicket gagal")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ticket_pb2.CreateTicketResponse(success=False, message=f"Error: {e}")
        finally:
            if cr:
                cr.close()

    # ---------- READ: GET satu tiket ----------
    def GetTicket(self, request, context):
        _logger.info("GetTicket id=%s", request.id)
        cr, env = None, None
        try:
            cr, env = _env()
            ticket = env["bureaucracy.ticket"].browse(request.id)
            if not ticket.exists():
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Tiket id={request.id} tidak ditemukan.")
                return ticket_pb2.TicketData()
            return _ticket_to_pb(ticket)
        except Exception as e:
            _logger.exception("GetTicket gagal")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ticket_pb2.TicketData()
        finally:
            if cr:
                cr.close()

    # ---------- READ: LIST tiket ----------
    def ListTickets(self, request, context):
        _logger.info("ListTickets state=%s", request.state)
        cr, env = None, None
        try:
            cr, env = _env()
            Ticket = env["bureaucracy.ticket"]
            domain = []
            if request.state:
                domain.append(("state", "=", request.state))

            recs = Ticket.search(domain, limit=request.limit or None,
                                  offset=request.offset or 0,
                                  order="id desc")
            return ticket_pb2.ListTicketsResponse(
                tickets=[_ticket_to_pb(t) for t in recs],
                total=len(recs),
            )
        except Exception as e:
            _logger.exception("ListTickets gagal")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ticket_pb2.ListTicketsResponse()
        finally:
            if cr:
                cr.close()

    # ---------- READ: LIST kategori ----------
    def ListCategories(self, request, context):
        _logger.info("ListCategories")
        cr, env = None, None
        try:
            cr, env = _env()
            cats = env["bureaucracy.ticket.category"].search([])
            return ticket_pb2.ListCategoriesResponse(
                categories=[
                    ticket_pb2.CategoryData(
                        id=c.id,
                        name=c.name or "",
                        code=c.code or "",
                        description=c.description or "",
                        ticket_count=c.ticket_count,
                    ) for c in cats
                ],
            )
        except Exception as e:
            _logger.exception("ListCategories gagal")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ticket_pb2.ListCategoriesResponse()
        finally:
            if cr:
                cr.close()


# =============================================
# Main
# =============================================
def serve():
    _bootstrap_odoo()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ticket_pb2_grpc.add_TicketServiceServicer_to_server(
        TicketingNativeServicer(), server
    )
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    server.start()
    _logger.info("Native gRPC server berjalan di port %s (db=%s, ORM langsung)",
                 GRPC_PORT, ODOO_DB)
    server.wait_for_termination()


if __name__ == "__main__":
    try:
        serve()
    except KeyboardInterrupt:
        _logger.info("Server dihentikan oleh user.")
        sys.exit(0)
