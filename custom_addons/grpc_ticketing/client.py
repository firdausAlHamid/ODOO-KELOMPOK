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


# =============================================
# Demo penuh (urutan khas untuk video)
# =============================================
def demo_full(stub, target):
    print("\n" + "=" * 60)
    print(f"  DEMO gRPC Client  ->  {target}")
    print("=" * 60)

    # 1. List kategori (READ)
    cats = list_categories(stub)
    cat_id = cats.categories[0].id if cats.categories else 0

    # 2. List tiket existing (READ)
    list_tickets(stub)

    # 3. Buat tiket baru (CREATE)
    new_title = f"[gRPC Demo] Tiket uji dari {target}"
    new_resp = create_ticket(
        stub,
        title=new_title,
        category_id=cat_id,
        location="Lab Komputer - Ruang 204",
        priority="2",
        description="<p>Tiket ini dibuat dari gRPC client untuk keperluan demo.</p>",
    )

    # 4. Ambil tiket yang baru dibuat (READ konfirmasi)
    if new_resp and new_resp.ticket_id:
        get_ticket(stub, new_resp.ticket_id)

    # 5. List tiket setelah create (READ)
    list_tickets(stub)

    print("=" * 60)
    print("  DEMO SELESAI")
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
        else:
            demo_full(stub, args.target)
    finally:
        channel.close()


if __name__ == "__main__":
    main()
