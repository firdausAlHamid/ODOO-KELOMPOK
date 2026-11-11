# gRPC Ticketing - Integrasi gRPC pada Odoo

Implementasi dua pendekatan arsitektur gRPC untuk berinteraksi dengan sistem tiket birokrasi Odoo.

---

## Struktur Direktori

```
custom_addons/grpc_ticketing/
├── ticket.proto           ← definisi service & message gRPC
├── ticket_pb2.py          ← generated: message classes (protobuf)
├── ticket_pb2_grpc.py     ← generated: service stub & servicer
├── middleware_server.py   ← Pendekatan 1: gRPC → XML-RPC → Odoo
├── native_server.py       ← Pendekatan 2: gRPC + Odoo ORM langsung
├── client.py              ← test client untuk kedua server
└── README.md
```

---

## Urutan Menjalankan (PENTING — ikuti urutan ini)

### Step 1 — Jalankan Odoo dulu (wajib, selalu pertama)

Buka terminal baru, jalankan dari root repo:

```bash
cd E:\ODOO-KELOMPOK
E:\ODOO-KELOMPOK\venv\Scripts\python.exe odoo-bin --config odoo.conf
```

Tunggu sampai muncul baris ini di terminal Odoo:
```
INFO odoo19 odoo.service.server: HTTP service (werkzeug) running on 0.0.0.0:8069
```
Kalau sudah muncul baris itu, Odoo siap. Jangan tutup terminal ini.

---

### Step 2 — Jalankan Middleware Server (port 50051)

Buka terminal **baru** (jangan tutup Odoo), jalankan:

```bash
cd E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing
E:\ODOO-KELOMPOK\venv\Scripts\python.exe middleware_server.py
```

Kalau berhasil, terminal ini akan menampilkan:
```
2026-xx-xx [MIDDLEWARE] INFO Berhasil login Odoo sebagai uid=2
2026-xx-xx [MIDDLEWARE] INFO Middleware gRPC server berjalan di port 50051
2026-xx-xx [MIDDLEWARE] INFO Meneruskan request ke Odoo XML-RPC: http://localhost:8069
```
Artinya server middleware sudah aktif dan siap menerima request gRPC.
Jangan tutup terminal ini.

---

### Step 3 — Jalankan Native Server (port 50052)

Buka terminal **baru lagi**, jalankan dari root repo:

```bash
cd E:\ODOO-KELOMPOK
E:\ODOO-KELOMPOK\venv\Scripts\python.exe custom_addons/grpc_ticketing/native_server.py
```

Kalau berhasil, terminal ini akan menampilkan:
```
2026-xx-xx [NATIVE] INFO Bootstrap Odoo dari config: E:\ODOO-KELOMPOK\odoo.conf
2026-xx-xx [NATIVE] INFO Bootstrap OK. Modul 'bureaucracy_ticketing' terpasang: True
2026-xx-xx [NATIVE] INFO Native gRPC server berjalan di port 50052
```
Jangan tutup terminal ini.

---

### Step 4 — Jalankan Client (untuk testing)

Buka terminal **baru lagi**, jalankan:

```bash
cd E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing

# Test ke middleware (port 50051)
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py

# Test ke native (port 50052)
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --target localhost:50052
```

Client akan otomatis:
1. Baca daftar kategori (READ)
2. Baca daftar tiket (READ)
3. Buat tiket baru (CREATE)
4. Baca tiket yang baru dibuat untuk konfirmasi (READ)
5. Baca daftar tiket lagi — tiket baru harus muncul (READ)

---

## Perintah Client Lainnya

```bash
cd E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing

# Hanya list kategori
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --categories

# Hanya list tiket
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --list

# Ambil tiket by ID
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --get 1

# Buat tiket dengan parameter: "judul" category_id lokasi priority
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --create "AC Rusak" 2 "Gedung B" 2
```

---

## Regenerate Stubs (jika ticket.proto diubah)

```bash
cd E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing
E:\ODOO-KELOMPOK\venv\Scripts\python.exe -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. ticket.proto
```

---

## Perbedaan Kedua Pendekatan

| Aspek                 | Middleware (port 50051)        | Native (port 50052)              |
|-----------------------|-------------------------------|----------------------------------|
| Cara akses Odoo       | Lewat HTTP XML-RPC (port 8069) | Langsung ke database (ORM)       |
| Butuh Odoo HTTP jalan | Ya, wajib                      | Tidak wajib                      |
| Kecepatan             | Sedikit lebih lambat           | Lebih cepat (direct DB)          |
| Kompleksitas          | Lebih simpel                   | Perlu bootstrap Odoo environment |
