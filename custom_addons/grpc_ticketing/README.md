# gRPC Ticketing — Integrasi gRPC pada Odoo

Implementasi dua pendekatan gRPC untuk berinteraksi dengan sistem tiket birokrasi Odoo.
Mendukung operasi **CRUD lengkap**: Create, Read, Update, Delete.

---

## Struktur File

```
custom_addons/grpc_ticketing/
├── ticket.proto           ← definisi operasi gRPC (kontrak antara client dan server)
├── ticket_pb2.py          ← generated otomatis dari proto (jangan diedit manual)
├── ticket_pb2_grpc.py     ← generated otomatis dari proto (jangan diedit manual)
├── middleware_server.py   ← Case 1: gRPC server yang nerusin request ke Odoo via XML-RPC
├── native_server.py       ← Case 2: gRPC server yang akses ORM Odoo langsung
├── client.py              ← test client untuk kedua server
├── narration_script.md    ← naskah narasi video demo
└── README.md
```

---

## Operasi yang Tersedia (CRUD)

| Operasi  | RPC              | Keterangan                                                        |
|----------|------------------|-------------------------------------------------------------------|
| Create   | `CreateTicket`   | Buat tiket pelaporan baru                                         |
| Read     | `ListTickets`    | Ambil daftar semua tiket (bisa filter by status)                  |
| Read     | `GetTicket`      | Ambil detail satu tiket by ID                                     |
| Read     | `ListCategories` | Ambil daftar kategori tiket                                       |
| Update   | `UpdateTicket`   | Ubah status tiket: `submit` → `in_progress` → `resolve` / `cancel` |
| Delete   | `DeleteTicket`   | Hapus tiket (hanya bisa kalau status masih `draft` atau `cancelled`) |

---

## Urutan Menjalankan (ikuti step ini)

### Step 1 — Jalankan Odoo (selalu pertama, wajib)

```bash
cd E:\ODOO-KELOMPOK
E:\ODOO-KELOMPOK\venv\Scripts\python.exe odoo-bin --config odoo.conf
```

Tunggu sampai terminal Odoo menampilkan:
```
INFO odoo19 odoo.service.server: HTTP service (werkzeug) running on 0.0.0.0:8069
```
Jangan tutup terminal ini.

---

### Step 2 — Jalankan Middleware Server (Case 1, port 50051)

Buka terminal baru:

```bash
cd E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing
E:\ODOO-KELOMPOK\venv\Scripts\python.exe middleware_server.py
```

Kalau berhasil, terminal menampilkan:
```
[MIDDLEWARE] INFO Berhasil login Odoo sebagai uid=2
[MIDDLEWARE] INFO Middleware gRPC server berjalan di port 50051
[MIDDLEWARE] INFO Meneruskan request ke Odoo XML-RPC: http://localhost:8069
```
Jangan tutup terminal ini.

---

### Step 3 — Jalankan Native Server (Case 2, port 50052)

Buka terminal baru lagi, **jalankan dari root repo**:

```bash
cd E:\ODOO-KELOMPOK
E:\ODOO-KELOMPOK\venv\Scripts\python.exe custom_addons/grpc_ticketing/native_server.py
```

Kalau berhasil:
```
[NATIVE] INFO Bootstrap OK — modul bureaucracy_ticketing terpasang: True
[NATIVE] INFO Native gRPC server AKTIF di port 50052
[NATIVE] INFO Database: odoo19 | Mode: ORM langsung (tanpa XML-RPC)
```
Jangan tutup terminal ini.

---

### Step 4 — Jalankan Client (testing)

Buka terminal baru, arahkan ke salah satu server:

```bash
cd E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing

# Demo CRUD lengkap ke Middleware (Case 1)
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --target localhost:50051

# Demo CRUD lengkap ke Native (Case 2)
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --target localhost:50052
```

Demo otomatis menjalankan urutan berikut:
1. **Read** — list kategori dan tiket yang ada
2. **Create** — buat tiket baru, nomor otomatis muncul
3. **Read** — baca tiket yang baru dibuat untuk konfirmasi
4. **Update** — submit tiket (Draft → Diajukan)
5. **Update** — proses tiket (Diajukan → Sedang Diproses)
6. **Update** — selesaikan tiket (Sedang Diproses → Selesai)
7. **Read** — lihat tiket setelah semua update
8. **Create + Delete** — buat tiket baru lalu hapus (demo Delete)
9. **Read** — list tiket akhir

---

## Perintah Client Lainnya

```bash
cd E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing

# Hanya list tiket
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --list

# Hanya list kategori
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --categories

# Ambil detail tiket by ID
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --get 5

# Buat tiket baru: "judul" category_id lokasi priority
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --create "AC Rusak" 1 "Gedung B Ruang 3" 2

# Update status tiket: ID action
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --update 5 submit
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --update 5 in_progress
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --update 5 resolve
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --update 5 cancel

# Hapus tiket (hanya draft/cancelled)
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --delete 5
```

---

## Perbedaan Dua Pendekatan

| Aspek                   | Case 1: Middleware (port 50051)       | Case 2: Native (port 50052)              |
|-------------------------|---------------------------------------|------------------------------------------|
| Cara akses Odoo         | Lewat HTTP + XML-RPC (port 8069)      | Langsung ke database via ORM             |
| Butuh Odoo HTTP jalan   | Ya, wajib                             | Tidak wajib (tapi PostgreSQL harus jalan)|
| Lokasi server           | Bisa di mesin berbeda dengan Odoo     | Harus di mesin yang sama dengan Odoo     |
| Kecepatan               | Sedikit lebih lambat (lewat HTTP)     | Lebih cepat (direct DB)                  |
| Bisa panggil fitur Odoo | Terbatas                              | Penuh — bisa akses semua method Odoo     |
