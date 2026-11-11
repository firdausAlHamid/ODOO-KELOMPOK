# Naskah Video Demo — Integrasi gRPC pada Odoo (3–4 menit)

Tugas Praktik: Integrasi gRPC pada Odoo — Pendekatan Middleware & Native (Built-in).

---

## 0. PERSIAPAN SEBELUM REKAM ( checklist )

- [ ] Odoo sudah jalan di `http://localhost:8069`, database `odoo19`, modul `bureaucracy_ticketing` sudah terinstall.
- [ ] Pastikan ada minimal **1 kategori** tiket dan **1 employee** (HR) di Odoo (buat manual lewat UI kalau belum).
- [ ] venv aktif: `E:\ODOO-KELOMPOK\venv\Scripts\activate`
- [ ] Buka **3 terminal**:
  - Terminal 1 → `python grpc_ticketing/middleware_server.py`
  - Terminal 2 → `python grpc_ticketing/native_server.py` (jalankan dari root repo)
  - Terminal 3 → untuk client, di direktori `grpc_ticketing/`
- [ ] Buka browser Odoo di tab lain (untuk verifikasi tiket masuk ke database).

---

## 1. INTRO  (0:00 – 0:30)

> Halo. Di video ini saya akan mendemonstrasikan Tugas Praktik Integrasi gRPC pada Odoo.
> Saya sudah punya modul custom bernama `bureaucracy_ticketing` yang berisi model
> `bureaucracy.ticket` untuk pelaporan kerusakan fasilitas kampus.
>
> Tugas ini minta dua pendekatan:
> 1. **Pendekatan Middleware gRPC** — server Python standalone yang jadi API Gateway,
>    menerima gRPC lalu meneruskan ke Odoo via XML-RPC.
> 2. **Pendekatan Native / Built-in** — script yang bootstrap Odoo Environment
>    dan akses ORM langsung tanpa XML-RPC.
>
> Untuk tiap pendekatan, saya akan buktikan operasi **Create** dan **Read** berhasil
> masuk dan terbaca di database Odoo.

*(Tampilkan slide / teks judul "gRPC + Odoo — Middleware vs Native")*

---

## 2. STRUKTUR PROJECT  (0:30 – 1:00)

*(Buka folder `grpc_ticketing/` di editor / terminal, tunjukkan isi file)*

> Ini struktur project-nya. Ada satu file `ticket.proto` yang mendefinisikan
> service `TicketService` dengan empat RPC:
> - `CreateTicket` untuk membuat tiket (POST),
> - `GetTicket` untuk ambil satu tiket by ID (GET),
> - `ListTickets` untuk list semua tiket (GET),
> - `ListCategories` untuk list kategori.
>
> Dari proto ini saya generate stub `ticket_pb2.py` dan `ticket_pb2_grpc.py`
> pakai `grpc_tools.protoc`. Stubs ini dipakai oleh kedua server dan client.
>
> Ada dua server: `middleware_server.py` dan `native_server.py`, plus satu
> `client.py` yang bisa konek ke salah satunya lewat flag `--target`.

---

## 3. PENDEKATAN 1 — MIDDLEWARE  (1:00 – 2:00)

### 3a. Tunjuk kode `middleware_server.py` (10 detik)

> Pendekatan pertama, Middleware. Di `middleware_server.py`, class
> `TicketingMiddlewareServicer` mengimplementasi service gRPC.
> Di setiap method, saya pakai `xmlrpc.client.ServerProxy` untuk manggil
> endpoint Odoo `/xmlrpc/2/common` buat autentikasi, dan `/xmlrpc/2/object`
> buat `execute_kw`. Jadi data gRPC diterjemahkan jadi XML-RPC call.

### 3b. Jalankan middleware server

```bash
python grpc_ticketing/middleware_server.py
```

> Saya jalankan server middleware di port 50051. Log menandakan
> berhasil login ke Odoo sebagai uid=2 dan server berjalan.

### 3c. Jalankan client demo ke middleware

```bash
python grpc_ticketing/client.py --target localhost:50051
```

*(Biarkan client jalan, tunjukkan output)*

> Client menjalankan demo otomatis:
> 1. **ListCategories** — READ, ambil daftar kategori.
> 2. **ListTickets** — READ, daftar tiket yang ada.
> 3. **CreateTicket** — CREATE, bikin tiket baru berjudul "[gRPC Demo] ...".
> 4. **GetTicket** — READ, ambil tiket yang baru dibuat buat konfirmasi.
> 5. **ListTickets** lagi — READ, untuk lihat tiket baru muncul di daftar.

### 3d. Verifikasi di Odoo UI

*(Buka browser ke Odoo → menu Bureaucracy Ticketing → list tiket)*

> Sekarang saya buka Odoo di browser. Tiket yang baru dibuat via gRPC client
> **muncul di database Odoo**. Ini membuktikan CREATE via Middleware berhasil
> masuk, dan READ juga bisa baca data yang sama.

---

## 4. PENDEKATAN 2 — NATIVE / ORM BOOTSTRAP  (2:00 – 3:00)

### 4a. Tunjuk kode `native_server.py` (15 detik)

> Pendekatan kedua, Native. Bedanya: tidak ada XML-RPC sama sekali.
> Di `_bootstrap_odoo()` saya panggil `odoo.tools.config.parse_args` baca
> `odoo.conf`, lalu bangun registry untuk database `odoo19`.
> Tiap RPC bikin cursor baru dan `Environment(cr, SUPERUSER_ID, {})`,
> lalu akses `env['bureaucracy.ticket']` langsung — search, browse, create.
> Karena in-process, saya juga bisa langsung panggil method bisnis Odoo
> kalau perlu, seperti `action_submit()`.

### 4b. Jalankan native server

```bash
python grpc_ticketing/native_server.py
```

> Server native jalan di port 50052. Log menandakan bootstrap Odoo sukses
> dan modul ticketing terpasang.

### 4c. Jalankan client demo ke native

```bash
python grpc_ticketing/client.py --target localhost:50052
```

> Sama seperti sebelumnya — ListCategories, ListTickets, CreateTicket,
> GetTicket, dan ListTickets lagi. Bedanya, sekarang request itu
> diproses langsung oleh ORM Odoo, bukan diteruskan lewat XML-RPC.

### 4d. Verifikasi di Odoo UI

*(Refresh list tiket di browser)*

> Refresh Odoo. Tiket baru yang dibuat via Native gRPC **juga muncul** di
> database. Membuktikan CREATE & READ via Native ORM bootstrap juga berhasil.

---

## 5. PERBANDINGAN & PENUTUP  (3:00 – 3:30)

*(Tampilkan tabel perbandingan dari README)*

> Sebagai ringkasan, dua pendekatan ini sama-sama jalan di atas gRPC,
> tapi beda cara akses Odoo-nya:
>
> - **Middleware** pakai XML-RPC (HTTP), perlu Odoo HTTP server jalan,
>   lebih decoupled, cocok kalau client gRPC dan Odoo beda mesin.
> - **Native** pakai ORM langsung, lebih cepat karena in-process, bisa
>   panggil method bisnis Odoo, tapi server harus jalan di mesin yang
>   sama dengan Odoo dan punya akses ke database.
>
> Kedua pendekatan sudah saya buktikan Create dan Read berhasil masuk dan
> terbaca di database Odoo. Sekian, terima kasih.

---

## TIPS REKAM

- Rekam layar 1920x1080, font terminal diperbesar (18–20pt) supaya terbaca.
- Jalankan satu demo per terminal, jangan tutup terminal sampai verifikasi UI selesai.
- Kalau mau lebih ringkas, skip bagian "tunjuk kode" (3a, 4a) — cukup tunjuk terminal + browser.
- Pastikan tidak ada data sensitif (password) tertangkap layar. Password di kode pakai `admin/admin` untuk demo.
- Durasi target: 3–4 menit. Kalau kepanjangan, potong bagian struktur project (bagian 2).
