# -*- coding: utf-8 -*-
"""
gRPC NATIVE SERVER  —  Pendekatan 2: Built-in / Environment Bootstrap

Server ini langsung bootstrap Odoo (baca odoo.conf, load registry),
lalu melayani request gRPC dengan akses ORM langsung tanpa XML-RPC.

Jalankan dari MANA SAJA pakai path lengkap:
    E:\\ODOO-KELOMPOK\\venv\\Scripts\\python.exe E:\\ODOO-KELOMPOK\\custom_addons\\grpc_ticketing\\native_server.py
"""

import os
import sys

# --- Path setup: harus sebelum import apapun ---
_THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))

# stub gRPC ada di direktori ini
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

# modul odoo ada di root repo (E:\ODOO-KELOMPOK\odoo\)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import logging
from concurrent import futures

import grpc
import ticket_pb2
import ticket_pb2_grpc

# =============================================
# Konfigurasi
# =============================================
ODOO_CONF  = os.path.join(_REPO_ROOT, "odoo.conf")
ODOO_DB    = "odoo19"
GRPC_PORT  = 50052

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [NATIVE] %(levelname)s %(message)s",
)
_logger = logging.getLogger(__name__)

# Registry global — di-load sekali saat startup, dipakai semua thread
_registry = None


# =============================================
# Bootstrap
# =============================================
def _bootstrap_odoo():
    global _registry

    _logger.info("Bootstrap Odoo dari config: %s", ODOO_CONF)
    if not os.path.exists(ODOO_CONF):
        raise FileNotFoundError(f"File konfigurasi tidak ditemukan: {ODOO_CONF}")

    import odoo
    from odoo.tools import config as odoo_config

    odoo_config.parse_config(["--config", ODOO_CONF])
    odoo_config["db_name"] = ODOO_DB

    # Load registry (singleton per db — kalau sudah ada, langsung return cache)
    _registry = odoo.modules.registry.Registry(ODOO_DB)

    # Verifikasi
    with _registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        mod = env["ir.module.module"].search([
            ("name", "=", "bureaucracy_ticketing"),
            ("state", "=", "installed"),
        ])
        _logger.info("Bootstrap OK — modul bureaucracy_ticketing terpasang: %s", bool(mod))
        cats = env["bureaucracy.ticket.category"].search([])
        _logger.info("Kategori tersedia: %s", [(c.id, c.name) for c in cats])


def _get_env():
    """Buat cursor + Environment baru. Caller wajib close cursor setelah selesai."""
    import odoo
    cr = _registry.cursor()
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    return cr, env


# =============================================
# Label helpers
# =============================================
_PRIORITY_LABELS = {"0": "Rendah", "1": "Sedang", "2": "Tinggi", "3": "Sangat Mendesak"}
_STATE_LABELS = {
    "draft": "Draft", "submitted": "Diajukan",
    "in_progress": "Sedang Diproses", "resolved": "Selesai", "cancelled": "Dibatalkan",
}


def _to_pb(t):
    return ticket_pb2.TicketData(
        id=t.id, name=t.name or "", title=t.title or "",
        description=t.description or "", location=t.location or "",
        priority=t.priority or "1",
        priority_label=_PRIORITY_LABELS.get(t.priority, ""),
        state=t.state or "draft",
        state_label=_STATE_LABELS.get(t.state, ""),
        category_name=t.category_id.name if t.category_id else "",
        employee_name=t.employee_id.name if t.employee_id else "",
        department_name=t.department_id.name if t.department_id else "",
        report_date=str(t.report_date) if t.report_date else "",
    )


# =============================================
# Service
# =============================================
class TicketingNativeServicer(ticket_pb2_grpc.TicketServiceServicer):

    def CreateTicket(self, request, context):
        _logger.info("CreateTicket: title=%r location=%r", request.title, request.location)
        if not request.title:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Field 'title' wajib diisi.")
            return ticket_pb2.CreateTicketResponse(success=False, message="title kosong")

        cr, env = _get_env()
        try:
            vals = {
                "title":       request.title,
                "description": request.description or "",
                "location":    request.location or "Tidak disebutkan",
                "priority":    request.priority or "1",
                # employee_id wajib — default ke employee id=1 (Administrator)
                # kalau client kirim employee_id spesifik, pakai itu
                "employee_id": request.employee_id if request.employee_id else 1,
            }
            if request.category_id:
                vals["category_id"] = request.category_id

            ticket = env["bureaucracy.ticket"].create(vals)
            cr.commit()
            _logger.info("Tiket BERHASIL dibuat: id=%s name=%s", ticket.id, ticket.name)
            return ticket_pb2.CreateTicketResponse(
                success=True,
                message="Tiket berhasil dibuat via Native ORM",
                ticket_id=ticket.id,
                ticket_name=ticket.name,
            )
        except Exception as e:
            cr.rollback()
            _logger.exception("CreateTicket ERROR: %s", e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ticket_pb2.CreateTicketResponse(success=False, message=f"Error: {e}")
        finally:
            cr.close()

    def GetTicket(self, request, context):
        _logger.info("GetTicket id=%s", request.id)
        cr, env = _get_env()
        try:
            t = env["bureaucracy.ticket"].browse(request.id)
            if not t.exists():
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Tiket id={request.id} tidak ditemukan.")
                return ticket_pb2.TicketData()
            return _to_pb(t)
        except Exception as e:
            _logger.exception("GetTicket ERROR: %s", e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ticket_pb2.TicketData()
        finally:
            cr.close()

    def ListTickets(self, request, context):
        _logger.info("ListTickets state=%r limit=%s", request.state, request.limit)
        cr, env = _get_env()
        try:
            domain = [("state", "=", request.state)] if request.state else []
            limit  = request.limit if request.limit > 0 else None
            recs   = env["bureaucracy.ticket"].search(
                domain, limit=limit, offset=request.offset or 0, order="id desc"
            )
            return ticket_pb2.ListTicketsResponse(
                tickets=[_to_pb(t) for t in recs],
                total=len(recs),
            )
        except Exception as e:
            _logger.exception("ListTickets ERROR: %s", e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ticket_pb2.ListTicketsResponse()
        finally:
            cr.close()

    def ListCategories(self, request, context):
        _logger.info("ListCategories")
        cr, env = _get_env()
        try:
            cats = env["bureaucracy.ticket.category"].search([])
            return ticket_pb2.ListCategoriesResponse(
                categories=[
                    ticket_pb2.CategoryData(
                        id=c.id, name=c.name or "", code=c.code or "",
                        description=c.description or "", ticket_count=c.ticket_count,
                    ) for c in cats
                ],
            )
        except Exception as e:
            _logger.exception("ListCategories ERROR: %s", e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ticket_pb2.ListCategoriesResponse()
        finally:
            cr.close()

    # ---------- UPDATE: ganti status tiket ----------
    def UpdateTicket(self, request, context):
        _logger.info("UpdateTicket id=%s action=%s", request.id, request.action)
        _ACTION_MAP = {
            "submit":      "action_submit",
            "in_progress": "action_in_progress",
            "resolve":     "action_resolve",
            "cancel":      "action_cancel",
            "reset":       "action_reset_draft",
        }
        method = _ACTION_MAP.get(request.action)
        if not method:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(
                f"Action '{request.action}' tidak valid. "
                "Pilihan: submit | in_progress | resolve | cancel | reset"
            )
            return ticket_pb2.UpdateTicketResponse(success=False, message="action tidak valid")

        cr, env = _get_env()
        try:
            ticket = env["bureaucracy.ticket"].browse(request.id)
            if not ticket.exists():
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Tiket id={request.id} tidak ditemukan.")
                return ticket_pb2.UpdateTicketResponse(success=False, message="Tiket tidak ditemukan")

            # Kalau in_progress, set assigned_to dulu
            if request.action == "in_progress" and request.assigned_to:
                ticket.assigned_to = request.assigned_to

            # Panggil method workflow Odoo langsung (keunggulan Native ORM)
            getattr(ticket, method)()
            cr.commit()

            _logger.info("Tiket id=%s state baru: %s", ticket.id, ticket.state)
            return ticket_pb2.UpdateTicketResponse(
                success=True,
                message=f"Tiket berhasil diupdate via Native ORM. Action: {request.action}",
                new_state=ticket.state,
            )
        except Exception as e:
            cr.rollback()
            _logger.exception("UpdateTicket ERROR: %s", e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ticket_pb2.UpdateTicketResponse(success=False, message=f"Error: {e}")
        finally:
            cr.close()

    # ---------- DELETE: hapus tiket ----------
    def DeleteTicket(self, request, context):
        _logger.info("DeleteTicket id=%s", request.id)
        cr, env = _get_env()
        try:
            ticket = env["bureaucracy.ticket"].browse(request.id)
            if not ticket.exists():
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Tiket id={request.id} tidak ditemukan.")
                return ticket_pb2.DeleteTicketResponse(success=False, message="Tiket tidak ditemukan")

            ticket_name = ticket.name
            state = ticket.state
            if state not in ("draft", "cancelled"):
                return ticket_pb2.DeleteTicketResponse(
                    success=False,
                    message=f"Tidak bisa hapus tiket {ticket_name} dengan status '{state}'. "
                            "Hanya tiket berstatus draft/cancelled yang bisa dihapus.",
                )

            ticket.unlink()
            cr.commit()
            _logger.info("Tiket %s berhasil dihapus", ticket_name)
            return ticket_pb2.DeleteTicketResponse(
                success=True,
                message=f"Tiket {ticket_name} berhasil dihapus via Native ORM",
            )
        except Exception as e:
            cr.rollback()
            _logger.exception("DeleteTicket ERROR: %s", e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ticket_pb2.DeleteTicketResponse(success=False, message=f"Error: {e}")
        finally:
            cr.close()


# =============================================
# Main
# =============================================
def serve():
    _bootstrap_odoo()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    ticket_pb2_grpc.add_TicketServiceServicer_to_server(TicketingNativeServicer(), server)
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    server.start()

    _logger.info("=" * 50)
    _logger.info("Native gRPC server AKTIF di port %s", GRPC_PORT)
    _logger.info("Database: %s | Mode: ORM langsung (tanpa XML-RPC)", ODOO_DB)
    _logger.info("=" * 50)

    server.wait_for_termination()


if __name__ == "__main__":
    try:
        serve()
    except KeyboardInterrupt:
        _logger.info("Server dihentikan.")
        sys.exit(0)
