# Naskah Video Demo — Integrasi gRPC pada Odoo (3–4 menit)

---

## PERSIAPAN SEBELUM REKAM

- [ ] Odoo sudah jalan (`python odoo-bin --config odoo.conf`), bisa dibuka di `http://localhost:8069`
- [ ] Sudah login sebagai admin, modul Bureaucracy Ticketing sudah terinstall dan ada datanya (minimal 1 kategori, 1 tiket)
- [ ] Buka 2 terminal ekstra: satu untuk middleware server, satu untuk native server
- [ ] Terminal ketiga untuk client

---

## NASKAH (ngomong santai aja, ini cuma panduan)

---

### BAGIAN 1 — INTRO (0:00 – 0:40)

> "Halo, di video ini gua mau nunjukkin hasil tugas praktik integrasi gRPC pada Odoo.
>
> Jadi, gRPC itu basically adalah cara dua program berkomunikasi satu sama lain lewat jaringan.
> Mirip kayak kita kirim pesan ke server, tapi lebih cepat dan lebih terstruktur dibanding REST API biasa.
>
> Di tugas ini, gua diminta bikin dua cara berbeda untuk 'ngobrol' dengan database Odoo lewat gRPC:
>
> Yang pertama namanya **Middleware** — jadi ada server perantara di tengah-tengah.
> Client kirim request ke server gRPC, server itu nerjemahin dan nerusin ke Odoo.
>
> Yang kedua namanya **Native** atau Built-in — servernya langsung nyambung ke database Odoo,
> tanpa perantara tambahan.
>
> Gua udah punya custom module di Odoo namanya Bureaucracy Ticketing — sistem tiket pelaporan fasilitas.
> Nah, dua server gRPC ini yang bakal kita gunain buat baca dan bikin tiket di module itu."

*(sambil ngomong, tunjukin tampilan Odoo di browser — list tiket yang udah ada)*

---

### BAGIAN 2 — TUNJUKIN STRUKTUR SEBENTAR (0:40 – 1:10)

*(buka folder `custom_addons/grpc_ticketing/` di file explorer atau terminal)*

> "Ini file-file yang gua bikin untuk tugas ini.
>
> Ada `ticket.proto` — ini semacam 'kontrak' yang mendefinisikan operasi apa aja yang bisa dilakukan:
> bisa Create tiket baru, bisa Read / ambil data tiket.
>
> Ada `middleware_server.py` untuk pendekatan pertama,
> `native_server.py` untuk pendekatan kedua,
> dan `client.py` yang bakal gua pakai buat ngetes kedua server itu.
>
> Dua file `ticket_pb2.py` itu hasil generate otomatis dari file proto tadi — isinya kode yang dibutuhkan biar Python bisa 'ngerti' format gRPC-nya."

---

### BAGIAN 3 — DEMO MIDDLEWARE (1:10 – 2:10)

*(buka terminal, jalankan middleware server)*

```bash
cd E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing
E:\ODOO-KELOMPOK\venv\Scripts\python.exe middleware_server.py
```

> "Ini gua jalanin server pertama — Middleware.
>
> Cara kerjanya: kalau ada yang kirim request ke server ini,
> dia bakal neneruskan permintaan itu ke Odoo lewat yang namanya XML-RPC —
> protokol standar yang udah ada di Odoo dari dulu.
>
> Jadi kayak ada 'orang tengah' yang nerjemahin request gRPC ke bahasa yang dimengerti Odoo.
>
> Nah liat di terminal — muncul tulisan 'Berhasil login Odoo sebagai uid=2'
> dan 'Middleware gRPC server berjalan di port 50051'.
> Itu tandanya server middleware udah aktif dan siap nerima request."

*(buka terminal lain, jalankan client ke middleware)*

```bash
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --target localhost:50051
```

> "Sekarang gua jalanin client-nya ke server middleware.
>
> Client ini otomatis bakal lakuin beberapa hal:
> pertama dia baca daftar kategori — ini operasi Read.
> Terus dia baca daftar tiket yang ada — Read lagi.
> Terus dia **bikin tiket baru** — ini operasi Create.
> Dan terakhir dia baca lagi tiket yang baru dibuat buat konfirmasi."

*(tunggu output client selesai, tunjukin nomor tiket baru yang muncul)*

> "Nah keliatan tuh, tiket baru berhasil dibuat. Nomor tiketnya muncul di sini."

*(buka browser Odoo, refresh halaman list tiket)*

> "Dan kalau gua cek langsung di Odoo... tiket yang tadi dibuat via gRPC **sudah masuk ke database**.
> Ini buktiin bahwa operasi Create dan Read lewat Middleware berhasil."

---

### BAGIAN 4 — DEMO NATIVE (2:10 – 3:10)

*(buka terminal baru, jalankan native server dari root repo)*

```bash
cd E:\ODOO-KELOMPOK
E:\ODOO-KELOMPOK\venv\Scripts\python.exe custom_addons/grpc_ticketing/native_server.py
```

> "Sekarang server kedua — Native.
>
> Bedanya sama yang tadi: kalau Middleware itu 'nitip' ke Odoo lewat HTTP,
> server Native ini langsung masuk ke dalam Odoo-nya.
>
> Dia baca file konfigurasi Odoo, lalu akses database secara langsung
> lewat yang namanya ORM — Object Relational Mapper, cara Odoo ngobrol sama database.
>
> Jadi lebih langsung, lebih efisien, karena gak ada 'orang tengah' lagi.
>
> Di terminal kelihatan tulisan 'Bootstrap OK' dan 'Native gRPC server berjalan di port 50052' —
> server udah aktif."

*(jalankan client ke native server)*

```bash
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --target localhost:50052
```

> "Sama seperti tadi, client lakuin Read dan Create.
> Bedanya sekarang request-nya diproses langsung oleh ORM Odoo, bukan diteruskan via HTTP."

*(tunggu output, tunjukin tiket baru terbuat, cek di browser Odoo)*

> "Dan di Odoo, tiket dari Native server juga masuk. Dua-duanya berhasil."

---

### BAGIAN 5 — PENUTUP (3:10 – 3:30)

> "Jadi kesimpulannya, dua pendekatan ini sama-sama bisa dipakai untuk integrasi gRPC dengan Odoo.
>
> Middleware lebih fleksibel — bisa jalan di mesin yang beda dengan Odoo-nya,
> cocok buat sistem yang lebih besar dan terdistribusi.
>
> Native lebih simpel dan langsung — akses langsung ke database, lebih cepat,
> tapi harus jalan di tempat yang sama dengan Odoo.
>
> Keduanya sudah terbukti bisa Create dan Read data tiket di database Odoo.
> Sekian dari gua, terima kasih."

---

## TIPS BIAR LANCAR

- Gak perlu hafal kata per kata — ini cuma panduan. Ngomong natural aja.
- Kalau salah ngomong, diem 2 detik terus lanjut, nanti bisa di-cut di edit.
- Pastiin font terminal gede (klik kanan terminal → Properties → Font → ukuran 18-20).
- Urutan yang harus jalan sebelum rekam: **Odoo dulu** → baru middleware server → baru native server.
- Total target 3-4 menit, kalau kebanyakan potong aja bagian struktur file (Bagian 2).
