# -*- coding: utf-8 -*-
"""
============================================================
 gRPC MIDDLEWARE SERVER  (Pendekatan 1: API Gateway)
============================================================

Server gRPC standalone ini bertindak sebagai Middleware / API Gateway.
Ia menerima request gRPC dari client, lalu meneruskan data request
tersebut ke instance Odoo lokal menggunakan protokol standar XML-RPC,
dan mengembalikan response-nya kembali ke client.

Alur:
    gRPC Client  -->  [Middleware gRPC Server]  -->  Odoo XML-RPC (port 8069)
    gRPC Client  <--  [Middleware gRPC Server]  <--  Odoo XML-RPC

Jalankan:
    python middleware_server.py
"""

import sys
import logging
from concurrent import futures

import xmlrpc.client
import grpc

# Generated stubs
import ticket_pb2
import ticket_pb2_grpc

# =============================================
# Konfigurasi koneksi Odoo (XML-RPC)
# =============================================
ODOO_URL    = "http://localhost:8069"
ODOO_DB     = "odoo19"
ODOO_USER   = "admin"
ODOO_PASS   = "admin"

# Port gRPC server
GRPC_PORT   = 50051

# Model Odoo
MODEL_TICKET  = "bureaucracy.ticket"
MODEL_CATEGORY = "bureaucracy.ticket.category"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MIDDLEWARE] %(levelname)s %(message)s",
)
_logger = logging.getLogger(__name__)


# =============================================
# Helper XML-RPC
# =============================================
def _common():
    """Return ServerProxy ke endpoint /xmlrpc/2/common."""
    return xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")


def _object():
    """Return ServerProxy ke endpoint /xmlrpc/2/object."""
    return xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")


def _authenticate() -> int:
    """Autentikasi user ke Odoo, return user id (uid)."""
    uid = _common().authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
    if not uid:
        raise RuntimeError(f"Autentikasi Odoo gagal untuk user '{ODOO_USER}'")
    _logger.info("Berhasil login Odoo sebagai uid=%s", uid)
    return uid


# Mapping priority (int) -> label
_PRIORITY_LABELS = {
    "0": "Rendah",
    "1": "Sedang",
    "2": "Tinggi",
    "3": "Sangat Mendesak",
}

# Mapping state -> label
_STATE_LABELS = {
    "draft":       "Draft",
    "submitted":   "Diajukan",
    "in_progress": "Sedang Diproses",
    "resolved":    "Selesai",
    "cancelled":   "Dibatalkan",
}


def _ticket_to_pb(rec) -> ticket_pb2.TicketData:
    """Ubah dict record XML-RPC menjadi TicketData protobuf."""
    return ticket_pb2.TicketData(
        id              = rec.get("id", 0),
        name            = rec.get("name", "") or "",
        title           = rec.get("title", "") or "",
        description     = rec.get("description", "") or "",
        location        = rec.get("location", "") or "",
        priority        = rec.get("priority", "1") or "1",
        priority_label  = _PRIORITY_LABELS.get(rec.get("priority", "1"), ""),
        state           = rec.get("state", "draft") or "draft",
        state_label     = _STATE_LABELS.get(rec.get("state", "draft"), ""),
        category_name   = (rec.get("category_id") or [0, ""])[1] if rec.get("category_id") else "",
        employee_name   = (rec.get("employee_id") or [0, ""])[1] if rec.get("employee_id") else "",
        department_name = (rec.get("department_id") or [0, ""])[1] if rec.get("department_id") else "",
        report_date     = rec.get("report_date") or "",
    )


# =============================================
# Service Implementation
# =============================================
class TicketingMiddlewareServicer(ticket_pb2_grpc.TicketServiceServicer):
    """
    Implementasi service gRPC yang meneruskan setiap call
    ke Odoo melalui XML-RPC.
    """

    def __init__(self):
        self.uid = _authenticate()

    # ---------- CREATE ----------
    def CreateTicket(self, request, context):
        _logger.info("CreateTicket: title=%r category_id=%s", request.title, request.category_id)
        try:
            # Validasi minimal
            if not request.title:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Field 'title' wajib diisi.")
                return ticket_pb2.CreateTicketResponse(success=False, message="title kosong")

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

            new_id = _object().execute_kw(
                ODOO_DB, self.uid, ODOO_PASS,
                MODEL_TICKET, "create", [vals],
            )
            # Ambil nomor tiket
            rec = _object().execute_kw(
                ODOO_DB, self.uid, ODOO_PASS,
                MODEL_TICKET, "read",
                [[new_id], ["name"]],
            )
            ticket_name = rec[0]["name"] if rec else ""

            _logger.info("Tiket dibuat id=%s name=%s", new_id, ticket_name)
            return ticket_pb2.CreateTicketResponse(
                success     = True,
                message     = "Tiket berhasil dibuat via Middleware (XML-RPC)",
                ticket_id   = new_id,
                ticket_name = ticket_name,
            )
        except Exception as e:
            _logger.exception("CreateTicket gagal")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ticket_pb2.CreateTicketResponse(success=False, message=f"Error: {e}")

    # ---------- READ: GET satu tiket ----------
    def GetTicket(self, request, context):
        _logger.info("GetTicket id=%s", request.id)
        try:
            recs = _object().execute_kw(
                ODOO_DB, self.uid, ODOO_PASS,
                MODEL_TICKET, "read",
                [[request.id],
                 ["id", "name", "title", "description", "location", "priority",
                  "state", "category_id", "employee_id", "department_id", "report_date"]],
            )
            if not recs:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Tiket id={request.id} tidak ditemukan.")
                return ticket_pb2.TicketData()
            return _ticket_to_pb(recs[0])
        except Exception as e:
            _logger.exception("GetTicket gagal")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ticket_pb2.TicketData()

    # ---------- READ: LIST tiket ----------
    def ListTickets(self, request, context):
        _logger.info("ListTickets state=%s limit=%s", request.state, request.limit)
        try:
            domain = []
            if request.state:
                domain.append(("state", "=", request.state))
            kwargs = {}
            if request.limit:
                kwargs["limit"]  = request.limit
            if request.offset:
                kwargs["offset"] = request.offset

            ids = _object().execute_kw(
                ODOO_DB, self.uid, ODOO_PASS,
                MODEL_TICKET, "search", [domain], kwargs,
            )
            recs = _object().execute_kw(
                ODOO_DB, self.uid, ODOO_PASS,
                MODEL_TICKET, "read",
                [ids,
                 ["id", "name", "title", "description", "location", "priority",
                  "state", "category_id", "employee_id", "department_id", "report_date"]],
            )
            return ticket_pb2.ListTicketsResponse(
                tickets = [_ticket_to_pb(r) for r in recs],
                total   = len(recs),
            )
        except Exception as e:
            _logger.exception("ListTickets gagal")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ticket_pb2.ListTicketsResponse()

    # ---------- READ: LIST kategori ----------
    def ListCategories(self, request, context):
        _logger.info("ListCategories")
        try:
            ids = _object().execute_kw(
                ODOO_DB, self.uid, ODOO_PASS,
                MODEL_CATEGORY, "search", [[]],
            )
            recs = _object().execute_kw(
                ODOO_DB, self.uid, ODOO_PASS,
                MODEL_CATEGORY, "read",
                [ids, ["id", "name", "code", "description"]],
            )
            return ticket_pb2.ListCategoriesResponse(
                categories=[
                    ticket_pb2.CategoryData(
                        id=id, name=r.get("name", "") or "",
                        code=r.get("code", "") or "",
                        description=r.get("description", "") or "",
                    )
                    for r in recs for id in [r.get("id", 0)]
                ],
            )
        except Exception as e:
            _logger.exception("ListCategories gagal")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ticket_pb2.ListCategoriesResponse()


# =============================================
# Main
# =============================================
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ticket_pb2_grpc.add_TicketServiceServicer_to_server(
        TicketingMiddlewareServicer(), server
    )
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    server.start()
    _logger.info("Middleware gRPC server berjalan di port %s", GRPC_PORT)
    _logger.info("Meneruskan request ke Odoo XML-RPC: %s (db=%s)", ODOO_URL, ODOO_DB)
    server.wait_for_termination()


if __name__ == "__main__":
    try:
        serve()
    except KeyboardInterrupt:
        _logger.info("Server dihentikan oleh user.")
        sys.exit(0)
