# Naskah Video Demo — Integrasi gRPC pada Odoo (3–4 menit)

---

## PERSIAPAN SEBELUM REKAM ( checklist )

- [ ] Odoo sudah jalan di terminal terpisah:
      `E:\ODOO-KELOMPOK\venv\Scripts\python.exe odoo-bin --config odoo.conf`
- [ ] Sudah login sebagai **admin** di `http://localhost:8069`, modul **Bureaucracy Ticketing** sudah terinstall
- [ ] Ada minimal 1 employee di HR dan beberapa tiket existing di Odoo (biar list-nya gak kosong)
- [ ] Siapkan **3 terminal** PowerShell:
  - Terminal 1 → untuk Middleware server
  - Terminal 2 → untuk Native server
  - Terminal 3 → untuk Client (testing)
- [ ] Buka browser Odoo di tab lain untuk verifikasi data masuk

---

## NASKAH (ngomong santai, ini cuma panduan — boleh improvisasi)

---

### BAGIAN 1 — INTRO (0:00 – 0:35)

*(tampilkan tampilan Odoo di browser, terlihat list tiket)*

> "Halo, di video ini gua mau nunjukkin hasil tugas praktik Integrasi gRPC pada Odoo.
>
> Sebelumnya, gua udah punya custom module di Odoo namanya **Bureaucracy Ticketing** —
> sistemnya buat pelaporan kerusakan fasilitas kampus, kayak proyektor rusak, AC mati, dan sebagainya.
> Ini yang keliatan di Odoo sekarang.
>
> Nah, di tugas ini gua diminta bikin integrasi menggunakan **gRPC**.
> Gampangnya, gRPC itu cara dua program saling 'ngobrol' lewat jaringan — mirip API,
> tapi lebih cepat dan lebih terstruktur.
>
> Gua bikin dua pendekatan berbeda:
> satu sebagai **Middleware** — ada server perantara di luar Odoo,
> satu lagi **Native** — servernya langsung nyambung ke dalam Odoo.
>
> Dan untuk tiap pendekatan, gua bakal nunjukkin semua operasi **CRUD** —
> Create, Read, Update, dan Delete — semuanya lewat gRPC."

---

### BAGIAN 2 — TUNJUKIN FILE SEBENTAR (0:35 – 1:00)

*(buka folder `custom_addons/grpc_ticketing/` di File Explorer atau terminal)*

> "Ini file-file yang gua bikin.
>
> `ticket.proto` itu ibarat 'daftar menu' — dia yang nentuin operasi apa aja yang bisa dipakai:
> ada CreateTicket, GetTicket, ListTickets, UpdateTicket, sama DeleteTicket.
>
> `middleware_server.py` untuk Case 1 — server yang jadi perantara.
> `native_server.py` untuk Case 2 — server yang langsung nyambung ke Odoo.
> `client.py` untuk testing kedua server tadi.
>
> File `ticket_pb2.py` itu generate otomatis dari file proto — gak perlu diotak-atik."

---

### BAGIAN 3 — CASE 1: MIDDLEWARE (1:00 – 2:10)

#### Jalankan server middleware

*(buka Terminal 1, ketik perintah ini)*

```
cd E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing
E:\ODOO-KELOMPOK\venv\Scripts\python.exe middleware_server.py
```

> "Ini Case 1 — Middleware. Gua jalanin servernya dulu.
>
> Lihat di terminal — muncul tulisan:
> *'Berhasil login Odoo sebagai uid=2'* dan *'Middleware gRPC server berjalan di port 50051'*.
> Artinya server ini udah konek ke Odoo dan siap nerima request.
>
> Cara kerjanya gini: client kirim request ke server gRPC ini, lalu server ini yang 'nerjemahin'
> dan nerusin ke Odoo lewat protokol namanya XML-RPC. Jadi ada orang tengah di sini."

#### Jalankan client ke middleware

*(buka Terminal 3, ketik perintah ini)*

```
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --target localhost:50051
```

> "Sekarang gua jalanin client-nya ke Middleware.
>
> Di output terminal keliatan urutannya:
> pertama **Read** — baca kategori dan daftar tiket yang ada.
> Terus **Create** — bikin tiket baru, nomornya otomatis keluar, misalnya TKT/2026/xxxx.
> Lanjut **Update** tiga kali — statusnya berubah: Draft jadi Diajukan, terus Sedang Diproses, terus Selesai.
> Terakhir **Delete** — satu tiket berhasil dihapus."

*(tunggu sampai output 'DEMO CRUD SELESAI' muncul)*

> "Semua operasi CRUD berhasil dijalankan via Middleware."

#### Verifikasi di Odoo

*(buka browser, refresh halaman tiket di Odoo)*

> "Sekarang gua cek di Odoo.
> Tiket yang tadi dibuat via gRPC **sudah masuk ke database** dan statusnya Selesai.
> Ini buktiin Create, Read, Update, Delete lewat Middleware semuanya berhasil."

---

### BAGIAN 4 — CASE 2: NATIVE (2:10 – 3:10)

#### Jalankan server native

*(buka Terminal 2, ketik perintah ini)*

```
cd E:\ODOO-KELOMPOK
E:\ODOO-KELOMPOK\venv\Scripts\python.exe custom_addons/grpc_ticketing/native_server.py
```

> "Ini Case 2 — Native. Bedanya dengan Middleware:
> kalau tadi ada 'orang tengah' yang nerusin request ke Odoo lewat HTTP,
> server ini langsung masuk ke dalam Odoo-nya tanpa perantara sama sekali.
>
> Lihat di terminal — muncul *'Bootstrap OK'* dan *'Native gRPC server AKTIF di port 50052'*.
> Bootstrap itu prosesnya dia baca file konfigurasi Odoo, terus akses databasenya langsung.
> Jadi lebih efisien."

#### Jalankan client ke native

*(di Terminal 3, ketik perintah ini)*

```
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --target localhost:50052
```

> "Sama seperti tadi — gua jalanin client yang sama, tapi sekarang diarahin ke Native server.
>
> Alurnya persis sama: Read, Create, Update status tiga kali, lalu Delete.
> Bedanya sekarang semua itu diproses **langsung oleh Odoo** di dalam prosesnya sendiri,
> tanpa lewat HTTP."

*(tunggu output 'DEMO CRUD SELESAI' muncul)*

#### Verifikasi di Odoo

*(refresh browser Odoo)*

> "Dan di Odoo, tiket dari Native server juga masuk dan statusnya juga berubah.
> Dua-duanya berhasil — CRUD penuh via gRPC, dua pendekatan berbeda."

---

### BAGIAN 5 — PENUTUP (3:10 – 3:30)

> "Jadi kesimpulannya:
>
> **Case 1 Middleware** — ada server gRPC yang berdiri sendiri di luar Odoo.
> Dia nerima request dari client, terus nerusin ke Odoo lewat protokol standar.
> Cocok kalau sistemnya tersebar di banyak tempat.
>
> **Case 2 Native** — server gRPC langsung hidup di dalam Odoo.
> Akses databasenya langsung, lebih cepat, dan bisa manggil fitur-fitur Odoo secara penuh.
>
> Dua-duanya udah terbukti bisa Create, Read, Update, dan Delete data tiket di Odoo.
> Sekian dari gua, terima kasih."

---

## TIPS BIAR LANCAR

- Gak perlu hafal kata per kata — ngomong natural aja, naskah ini cuma panduan arah.
- Kalau salah ngomong, diam 2 detik, lanjut lagi — nanti bisa di-cut pas edit.
- Pastiin font terminal keliatan besar: klik kanan titlebar terminal → Properties → Font → pilih ukuran 18 atau 20.
- **Urutan wajib sebelum rekam**: Odoo harus jalan dulu → baru Middleware server → baru Native server.
- Kalau mau lebih singkat, skip Bagian 2 (tunjuk file) — langsung lompat ke demo.
- Kalau waktu masih kurang dari 3 menit, perlambat sedikit pas tunjuk output terminal — biar penonton sempat baca.
