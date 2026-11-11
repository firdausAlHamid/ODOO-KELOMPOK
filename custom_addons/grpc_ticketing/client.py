# -*- coding: utf-8 -*-
"""
============================================================
 gRPC TEST CLIENT  -  Bureaucracy Ticketing
============================================================

Client untuk menguji kedua server (middleware & native).
Secara default connect ke MIDDLEWARE (port 50051), tapi bisa
dialihkan ke NATIVE (port 50052) lewat argumen --target.

Cara pakai:
    python client.py                       # demo penuh ke middleware
    python client.py --target localhost:50052   # demo penuh ke native
    python client.py --list                # hanya list tiket
    python client.py --categories         # hanya list kategori
    python client.py --create "Judul"     # buat tiket baru
"""

import sys
import argparse
import logging

import grpc

import ticket_pb2
import ticket_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CLIENT] %(levelname)s %(message)s",
)
_logger = logging.getLogger(__name__)


# Default target
DEFAULT_TARGET = "localhost:50051"   # middleware


def _connect(target):
    channel = grpc.insecure_channel(target)
    stub = ticket_pb2_grpc.TicketServiceStub(channel)
    return channel, stub


# =============================================
# Operasi
# =============================================
def list_categories(stub):
    _logger.info("==> RPC ListCategories")
    resp = stub.ListCategories(ticket_pb2.ListCategoriesRequest())
    print("\n=== KATEGORI TIKET ===")
    if not resp.categories:
        print("  (belum ada kategori)")
    for c in resp.categories:
        print(f"  [{c.id}] {c.name} ({c.code}) - {c.description}  [{c.ticket_count} tiket]")
    print(f"Total kategori: {len(resp.categories)}\n")
    return resp


def list_tickets(stub, state=""):
    _logger.info("==> RPC ListTickets state=%r", state)
    resp = stub.ListTickets(ticket_pb2.ListTicketsRequest(state=state, limit=20))
    print("\n=== DAFTAR TIKET ===")
    if not resp.tickets:
        print("  (belum ada tiket)")
    for t in resp.tickets:
        print(f"  [{t.id}] {t.name} | {t.title}")
        print(f"       Kategori : {t.category_name}")
        print(f"       Lokasi   : {t.location}")
        print(f"       Prioritas: {t.priority_label} | Status: {t.state_label}")
        print(f"       Pelapor  : {t.employee_name} ({t.department_name})")
        print(f"       Tgl Lapor: {t.report_date}")
        print()
    print(f"Total tiket ditampilkan: {resp.total}\n")
    return resp


def get_ticket(stub, ticket_id):
    _logger.info("==> RPC GetTicket id=%s", ticket_id)
    try:
        t = stub.GetTicket(ticket_pb2.GetTicketRequest(id=ticket_id))
        print("\n=== DETAIL TIKET ===")
        print(f"  ID         : {t.id}")
        print(f"  Nomor      : {t.name}")
        print(f"  Judul      : {t.title}")
        print(f"  Kategori   : {t.category_name}")
        print(f"  Lokasi     : {t.location}")
        print(f"  Prioritas  : {t.priority_label}")
        print(f"  Status     : {t.state_label}")
        print(f"  Pelapor    : {t.employee_name} ({t.department_name})")
        print(f"  Tgl Lapor  : {t.report_date}")
        print(f"  Deskripsi  : {t.description[:200]}\n")
        return t
    except grpc.RpcError as e:
        _logger.error("GetTicket gagal: %s (%s)", e.code(), e.details())
        return None


def create_ticket(stub, title, category_id=0, location="Gedung A - Lantai 2",
                  priority="1", description="", employee_id=0):
    _logger.info("==> RPC CreateTicket title=%r", title)
    req = ticket_pb2.CreateTicketRequest(
        title=title,
        description=description or f"Laporan otomatis via gRPC: {title}",
        category_id=category_id,
        location=location,
        priority=priority,
        employee_id=employee_id,
    )
    try:
        resp = stub.CreateTicket(req)
        print("\n=== CREATE TIKET ===")
        print(f"  Success   : {resp.success}")
        print(f"  Message   : {resp.message}")
        print(f"  Ticket ID: {resp.ticket_id}")
        print(f"  Ticket No: {resp.ticket_name}\n")
        return resp
    except grpc.RpcError as e:
        _logger.error("CreateTicket gagal: %s (%s)", e.code(), e.details())
        return None


def update_ticket(stub, ticket_id, action, assigned_to=0):
    _logger.info("==> RPC UpdateTicket id=%s action=%s", ticket_id, action)
    req = ticket_pb2.UpdateTicketRequest(
        id=ticket_id,
        action=action,
        assigned_to=assigned_to,
    )
    try:
        resp = stub.UpdateTicket(req)
        print("\n=== UPDATE TIKET ===")
        print(f"  Success    : {resp.success}")
        print(f"  Message    : {resp.message}")
        print(f"  State Baru : {resp.new_state}\n")
        return resp
    except grpc.RpcError as e:
        _logger.error("UpdateTicket gagal: %s (%s)", e.code(), e.details())
        return None


def delete_ticket(stub, ticket_id):
    _logger.info("==> RPC DeleteTicket id=%s", ticket_id)
    try:
        resp = stub.DeleteTicket(ticket_pb2.DeleteTicketRequest(id=ticket_id))
        print("\n=== DELETE TIKET ===")
        print(f"  Success : {resp.success}")
        print(f"  Message : {resp.message}\n")
        return resp
    except grpc.RpcError as e:
        _logger.error("DeleteTicket gagal: %s (%s)", e.code(), e.details())
        return None



def demo_full(stub, target):
    print("\n" + "=" * 60)
    print(f"  DEMO gRPC CRUD Client  ->  {target}")
    print("=" * 60)

    # 1. READ — List kategori
    cats = list_categories(stub)
    cat_id = cats.categories[0].id if cats.categories else 0

    # 2. READ — List tiket existing
    list_tickets(stub)

    # 3. CREATE — bikin tiket baru
    # NOTE: ubah nilai variabel di bawah ini untuk ganti data tiket demo
    new_title    = f"[gRPC Demo] Tiket uji dari {target}"
    new_category = cat_id
    new_location = "Lab Komputer - Ruang 207"
    new_priority = "3"
    new_desc     = "<p>Tiket ini dibuat dari gRPC client untuk keperluan demo.</p>"

    print(f"\n[INFO] Membuat tiket baru: lokasi={new_location}")
    new_resp = create_ticket(
        stub,
        title=new_title,
        category_id=new_category,
        location=new_location,
        priority=new_priority,
        description=new_desc,
    )

    # 4. READ konfirmasi — ambil tiket yang baru dibuat
    if new_resp and new_resp.ticket_id:
        get_ticket(stub, new_resp.ticket_id)

        # 5. UPDATE — submit tiket (draft -> submitted)
        update_ticket(stub, new_resp.ticket_id, "submit")

        # 6. UPDATE — proses tiket (submitted -> in_progress), butuh PIC
        #    pakai employee id=1 (Administrator) sebagai PIC
        update_ticket(stub, new_resp.ticket_id, "in_progress", assigned_to=1)

        # 7. UPDATE — selesai (in_progress -> resolved)
        update_ticket(stub, new_resp.ticket_id, "resolve")

        # 8. READ — lihat tiket setelah semua update status
        print("\n[INFO] Tiket setelah seluruh update status:")
        get_ticket(stub, new_resp.ticket_id)

        # 9. DELETE — demo hapus tiket
        # Bikin tiket baru lagi lalu hapus (karena tiket resolved tidak bisa hapus)
        print("\n[INFO] Membuat tiket kedua untuk demo DELETE:")
        del_resp = create_ticket(
            stub,
            title=f"[gRPC Demo DELETE] Tiket hapus dari {target}",
            category_id=new_category,
            location="Ruang Demo Hapus",
            priority="0",
            description="<p>Tiket ini akan dihapus untuk demo DELETE.</p>",
        )
        if del_resp and del_resp.ticket_id:
            delete_ticket(stub, del_resp.ticket_id)

    # 10. READ final — list tiket setelah semua operasi
    list_tickets(stub)

    print("=" * 60)
    print("  DEMO CRUD SELESAI: Create, Read, Update, Delete")
    print("=" * 60 + "\n")


# =============================================
# CLI
# =============================================
def main():
    parser = argparse.ArgumentParser(description="gRPC Test Client - Ticketing")
    parser.add_argument("--target", default=DEFAULT_TARGET,
                        help="gRPC target, mis. localhost:50051 (middleware) "
                             "atau localhost:50052 (native)")
    parser.add_argument("--list", action="store_true",
                        help="Hanya list tiket")
    parser.add_argument("--categories", action="store_true",
                        help="Hanya list kategori")
    parser.add_argument("--get", type=int, metavar="ID",
                        help="Ambil detail tiket by ID")
    parser.add_argument("--create", nargs="+", metavar="TITLE",
                        help="Buat tiket baru (title wajib). "
                             "Opsional: category_id location priority")
    parser.add_argument("--update", nargs=2, metavar=("ID", "ACTION"),
                        help="Update status tiket: ID action (submit|in_progress|resolve|cancel|reset)")
    parser.add_argument("--delete", type=int, metavar="ID",
                        help="Hapus tiket by ID (hanya draft/cancelled)")
    args = parser.parse_args()

    channel, stub = _connect(args.target)
    _logger.info("Terhubung ke %s", args.target)

    try:
        if args.list:
            list_tickets(stub)
        elif args.categories:
            list_categories(stub)
        elif args.get is not None:
            get_ticket(stub, args.get)
        elif args.create:
            title = args.create[0]
            cat_id = int(args.create[1]) if len(args.create) > 1 else 0
            location = args.create[2] if len(args.create) > 2 else "Gedung A - Lt.2"
            priority = args.create[3] if len(args.create) > 3 else "1"
            create_ticket(stub, title, category_id=cat_id,
                          location=location, priority=priority)
        elif args.update:
            update_ticket(stub, int(args.update[0]), args.update[1])
        elif args.delete is not None:
            delete_ticket(stub, args.delete)
        else:
            demo_full(stub, args.target)
    finally:
        channel.close()


if __name__ == "__main__":
    main()
