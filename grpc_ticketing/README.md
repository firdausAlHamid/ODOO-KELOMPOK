# gRPC Ticketing - Integrasi gRPC pada Odoo

Implementasi dua pendekatan arsitektur gRPC untuk berinteraksi dengan sistem tiket birokrasi Odoo.

---

## Struktur Direktori

```
grpc_ticketing/
├── ticket.proto           ← definisi service & message gRPC
├── ticket_pb2.py          ← generated: message classes (protobuf)
├── ticket_pb2_grpc.py     ← generated: service stub & servicer
├── middleware_server.py   ← Pendekatan 1: gRPC → XML-RPC → Odoo
├── native_server.py       ← Pendekatan 2: gRPC + Odoo ORM langsung
├── client.py              ← test client untuk kedua server
└── README.md
```

---

## Pendekatan 1 — Middleware gRPC (port 50051)

```
gRPC Client  ──►  middleware_server.py  ──►  Odoo XML-RPC (8069)
```

Server Python standalone yang bertindak sebagai API Gateway.
Setiap request gRPC diteruskan ke Odoo melalui `xmlrpc.client`.

**Jalankan (dari direktori `grpc_ticketing/`):**

```bash
# Aktifkan venv Odoo
E:\ODOO-KELOMPOK\venv\Scripts\activate

python middleware_server.py
```

Log sukses:
```
[MIDDLEWARE] INFO  Berhasil login Odoo sebagai uid=2
[MIDDLEWARE] INFO  Middleware gRPC server berjalan di port 50051
```

---

## Pendekatan 2 — Native gRPC / Built-in ORM (port 50052)

```
gRPC Client  ──►  native_server.py  ──►  Odoo ORM (env['bureaucracy.ticket'])
```

Script yang menginisialisasi Odoo secara in-process (Environment Bootstrap),
kemudian menjalankan gRPC server. Mengakses database **langsung via ORM**,
tanpa XML-RPC.

**Jalankan (dari root repo `E:\ODOO-KELOMPOK\`):**

```bash
# Aktifkan venv Odoo
E:\ODOO-KELOMPOK\venv\Scripts\activate

# Pastikan working directory adalah root repo agar odoo.conf terbaca
cd E:\ODOO-KELOMPOK
python grpc_ticketing/native_server.py
```

Log sukses:
```
[NATIVE] INFO  Bootstrap Odoo dari config: E:\ODOO-KELOMPOK\odoo.conf
[NATIVE] INFO  Native gRPC server berjalan di port 50052
```

---

## Test Client

```bash
cd E:\ODOO-KELOMPOK\grpc_ticketing
E:\ODOO-KELOMPOK\venv\Scripts\activate

# Demo penuh ke middleware (default)
python client.py

# Demo penuh ke native
python client.py --target localhost:50052

# Operasi spesifik
python client.py --categories                        # list kategori
python client.py --list                              # list tiket
python client.py --get 1                             # get tiket id=1
python client.py --create "AC Rusak" 2 "Gedung B" 2  # create tiket
```

---

## Regenerate Stubs (jika .proto diubah)

```bash
cd E:\ODOO-KELOMPOK\grpc_ticketing
E:\ODOO-KELOMPOK\venv\Scripts\python.exe -m grpc_tools.protoc \
  -I. --python_out=. --grpc_python_out=. ticket.proto
```

---

## Perbedaan Utama Kedua Pendekatan

| Aspek                   | Middleware (XML-RPC)         | Native (ORM Bootstrap)         |
|-------------------------|------------------------------|--------------------------------|
| Transport ke Odoo       | HTTP + XML-RPC (port 8069)   | Direct database (PostgreSQL)   |
| Autentikasi             | username/password XML-RPC    | SUPERUSER_ID (in-process)      |
| Memanggil method bisnis | ❌ Tidak langsung            | ✅ `ticket.action_submit()`   |
| Port gRPC               | 50051                        | 50052                          |
| Ketergantungan          | Odoo HTTP server harus jalan | venv + odoo.conf               |
| Kompleksitas setup      | Ringan                       | Harus install Odoo deps        |
