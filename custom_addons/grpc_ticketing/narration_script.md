# Panduan & Naskah Video Demo — Modul gRPC pada Odoo

> **Target durasi:** ± 4–5 menit  
> **Sesuai ketentuan tugas:**
> - **Case 1:** gRPC **dalam Odoo** (`native_server.py` → port `50052`)
> - **Case 2:** gRPC pada **middleware di luar Odoo** sebagai konektivitas ke Odoo (`middleware_server.py` → port `50051`)

---

## 1. PERSIAPAN SEBELUM REKAM (WAJIB)

Pastikan semua langkah ini sudah siap sebelum mulai record layar:

1. **Odoo sudah berjalan** di terminal utama (biarkan tetap terbuka):
   ```powershell
   cd E:\ODOO-KELOMPOK
   E:\ODOO-KELOMPOK\venv\Scripts\python.exe odoo-bin --config odoo.conf
   ```
   Tunggu sampai muncul log: `HTTP service (werkzeug) running on 0.0.0.0:8069`.

2. **Browser sudah login Odoo (`http://localhost:8069`)** sebagai **admin**, dan buka menu modul **Bureaucracy Ticketing** (daftar tiket terlihat di layar).
3. **Data awal sudah ada:** minimal 1 employee di HR (ID `1` / Administrator) dan minimal 1 kategori tiket (otomatis/existing) agar demo lancar.
4. **Siapkan 3 jendela PowerShell** (ukuran font dibesarkan jadi 18–20 biar kebaca di video):
   - **Terminal 1** → Untuk **Case 1: Native gRPC Server (dalam Odoo)**
   - **Terminal 2** → Untuk **Case 2: Middleware gRPC Server (di luar Odoo)**
   - **Terminal 3** → Untuk **Client Testing (`client.py`)**

---

## 2. NASKAH NARASI & LANGKAH DEMO

### BAGIAN 1 — INTRO & KONSEP (0:00 – 0:45)

**[LAYAR: Tampilkan browser Odoo pada halaman daftar tiket Bureaucracy Ticketing]**

> "Halo, pada video kali ini saya akan mendemonstrasikan hasil pembuatan modul integrasi **gRPC pada Odoo** untuk studi kasus sistem pelaporan fasilitas kampus, yaitu modul custom **Bureaucracy Ticketing**.
>
> Secara singkat, **gRPC** adalah framework komunikasi antar-aplikasi berbasis *Remote Procedure Call* yang menggunakan **Protocol Buffers** sebagai kontrak datanya—jadi client dan server bisa bertukar data jauh lebih cepat dan terstruktur dibanding REST API biasa.
>
> Di sini saya mengimplementasikan **dua pendekatan** sesuai ketentuan tugas:
> 1. **Case 1 — gRPC di dalam Odoo (Native):** server gRPC langsung mem-bootstrap environment Odoo dan mengakses **ORM Odoo** secara langsung tanpa perantara HTTP.
> 2. **Case 2 — gRPC pada Middleware di luar Odoo:** server gRPC berdiri sendiri di luar Odoo sebagai perantara (*API Gateway*), lalu meneruskan request ke Odoo menggunakan protokol **XML-RPC**.
>
> Pada kedua case tersebut, saya akan mendemonstrasikan operasi **CRUD lengkap**—Create, Read, Update, dan Delete—serta memverifikasi hasilnya langsung di database Odoo."

---

### BAGIAN 2 — STRUKTUR FILE & KONTRAK PROTO (0:45 – 1:20)

**[LAYAR: Tampilkan isi folder `E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing\` di VS Code atau File Explorer, lalu buka sekilas `ticket.proto`]**

> "Sebelum masuk ke demo, ini adalah struktur file modul gRPC yang saya buat di `custom_addons/grpc_ticketing`:
>
> - Pertama ada **`ticket.proto`**. Ini adalah kontrak layanan gRPC-nya. Di dalamnya didefinisikan service `TicketService` yang berisi RPC untuk **CRUD**: `CreateTicket`, `GetTicket`, `ListTickets`, `ListCategories`, `UpdateTicket`, dan `DeleteTicket`.
> - Dari file `.proto` ini, kita generate file stub **`ticket_pb2.py`** dan **`ticket_pb2_grpc.py`** secara otomatis.
> - Lalu ada **`native_server.py`** untuk **Case 1** (gRPC di dalam Odoo).
> - Ada **`middleware_server.py`** untuk **Case 2** (gRPC sebagai middleware di luar Odoo).
> - Dan terakhir **`client.py`** sebagai gRPC client untuk menguji kedua server tersebut."

---

### BAGIAN 3 — CASE 1: gRPC DALAM ODOO / NATIVE (1:20 – 2:45)

#### 3A. Jalankan Native Server (Terminal 1)

**[LAYAR: Pindah ke Terminal 1, jalankan perintah berikut]**

```powershell
cd E:\ODOO-KELOMPOK
E:\ODOO-KELOMPOK\venv\Scripts\python.exe custom_addons\grpc_ticketing\native_server.py
```

**[Tunggu sampai muncul output: `Bootstrap OK` dan `Native gRPC server AKTIF di port 50052`]**

> "Sekarang kita masuk ke **Case 1: gRPC di dalam Odoo**.
> Saya jalankan `native_server.py` dari root direktori Odoo.
>
> Bisa dilihat di terminal: muncul log **`Bootstrap OK — modul bureaucracy_ticketing terpasang: True`** dan **`Native gRPC server AKTIF di port 50052`**.
>
> Artinya, server gRPC ini langsung membaca konfigurasi `odoo.conf`, memuat registry dan ORM Odoo secara langsung ke dalam prosesnya, dan langsung terhubung ke database PostgreSQL tanpa melewati HTTP atau XML-RPC."

#### 3B. Jalankan Client ke Case 1 (Terminal 3)

**[LAYAR: Pindah ke Terminal 3, jalankan perintah berikut]**

```powershell
cd E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --target localhost:50052
```

**[Tunggu proses berjalan dan tunjukkan output di Terminal 3 saat muncul]**

> "Sekarang saya jalankan `client.py` dan mengarahkannya ke port **`50052`**, yaitu server Native.
>
> Di terminal terlihat alur demo CRUD-nya berjalan otomatis:
> 1. **Read awal:** client memanggil `ListCategories` dan `ListTickets` untuk membaca kategori serta daftar tiket yang sudah ada di Odoo.
> 2. **Create:** client memanggil `CreateTicket` untuk membuat tiket baru berjudul *'[gRPC Demo] Tiket uji dari localhost:50052'*. Nomor tiket otomatis ter-generate oleh sequence Odoo, dan langsung dibaca kembali lewat `GetTicket`.
> 3. **Update:** terjadi tiga kali transisi status lewat `UpdateTicket`—dari **Draft** menjadi **Diajukan (`submit`)**, lalu **Sedang Diproses (`in_progress`)** sekaligus assign PIC, hingga status **Selesai (`resolve`)**.
> 4. **Delete:** karena tiket yang sudah selesai tidak boleh dihapus oleh aturan bisnis Odoo, client membuat satu tiket uji kedua yang masih berstatus Draft, lalu menghapusnya menggunakan `DeleteTicket`.
> 5. **Read akhir:** menampilkan daftar tiket terbaru dan muncul keterangan **`DEMO CRUD SELESAI`**."

#### 3C. Verifikasi di Browser Odoo

**[LAYAR: Pindah ke browser Odoo, tekan Refresh / F5]**

> "Sekarang kita cek di UI Odoo. Setelah di-refresh, tiket baru dari `localhost:50052` sudah masuk ke database Odoo dengan status **Selesai**, sedangkan tiket kedua yang tadi di-delete sudah terhapus. Itu membuktikan **Case 1 (gRPC dalam Odoo)** berjalan dengan baik."

---

### BAGIAN 4 — CASE 2: gRPC MIDDLEWARE DI LUAR ODOO (2:45 – 4:10)

#### 4A. Jalankan Middleware Server (Terminal 2)

**[LAYAR: Pindah ke Terminal 2, jalankan perintah berikut]**

```powershell
cd E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing
E:\ODOO-KELOMPOK\venv\Scripts\python.exe middleware_server.py
```

**[Tunggu sampai muncul output: `Berhasil login Odoo sebagai uid=2` dan `Middleware gRPC server berjalan di port 50051`]**

> "Lanjut ke **Case 2: gRPC pada middleware di luar Odoo**.
> Saya jalankan `middleware_server.py` di terminal terpisah.
>
> Di terminal muncul log **`Berhasil login Odoo sebagai uid=2`**, **`Middleware gRPC server berjalan di port 50051`**, dan **`Meneruskan request ke Odoo XML-RPC: http://localhost:8069`**.
>
> Bedanya dengan Case 1 tadi: server gRPC ini berdiri sebagai service terpisah di luar Odoo. Ia menerima request biner gRPC dari client di port `50051`, lalu bertindak sebagai penerjemah yang meneruskan perintah ke endpoint **XML-RPC Odoo** di port `8069`."

#### 4B. Jalankan Client ke Case 2 (Terminal 3)

**[LAYAR: Pindah ke Terminal 3 (sudah berada di `custom_addons\grpc_ticketing`), jalankan perintah berikut]**

```powershell
E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --target localhost:50051
```

**[Tunggu sampai output `DEMO CRUD SELESAI` muncul]**

> "Sekarang saya jalankan `client.py` yang sama persis, tapi targetnya diarahkan ke port **`50051`** milik Middleware.
>
> Alurnya sama: **Read** kategori dan daftar tiket, **Create** tiket baru berjudul *'[gRPC Demo] Tiket uji dari localhost:50051'*, **Update** status bertahap dari Draft sampai Selesai, **Delete** tiket uji kedua, lalu **Read** daftar tiket akhir.
>
> Di sisi server Terminal 2 juga terlihat log setiap RPC yang masuk dan diteruskan ke XML-RPC Odoo hingga semuanya sukses."

#### 4C. Verifikasi di Browser Odoo

**[LAYAR: Pindah ke browser Odoo, tekan Refresh / F5]**

> "Kita refresh lagi halaman Odoo-nya. Bisa dilihat tiket dari `localhost:50051` juga berhasil masuk dan tersimpan dengan status **Selesai**."

---

### BAGIAN 5 — PENUTUP & PERBANDINGAN (4:10 – 4:40)

**[LAYAR: Bisa tampilkan Odoo atau ringkasan terminal]**

> "Jadi kesimpulannya, kedua pendekatan gRPC berhasil diimplementasikan dengan operasi CRUD penuh:
>
> - **Case 1 (gRPC dalam Odoo / port 50052):** Akses langsung ke ORM dan database Odoo tanpa HTTP overhead—cocok untuk performa tinggi dan akses penuh ke method internal Odoo, namun harus berjalan di mesin yang sama dengan Odoo.
> - **Case 2 (gRPC Middleware di luar Odoo / port 50051):** Berdiri independen di luar Odoo dan berkomunikasi lewat XML-RPC—lebih fleksibel untuk arsitektur terdistribusi atau microservice karena middleware bisa ditaruh di server terpisah.
>
> Sekian demonstrasi integrasi gRPC pada Odoo dari saya. Terima kasih."

---

## 3. CHEAT SHEET COMMAND (UNTUK COPY-PASTE CEPAT)

| Peran | Terminal | Command |
| :--- | :---: | :--- |
| **Odoo Server** | Utama | `cd E:\ODOO-KELOMPOK`<br>`E:\ODOO-KELOMPOK\venv\Scripts\python.exe odoo-bin --config odoo.conf` |
| **Case 1: Native (dalam Odoo)** | Term 1 | `cd E:\ODOO-KELOMPOK`<br>`E:\ODOO-KELOMPOK\venv\Scripts\python.exe custom_addons\grpc_ticketing\native_server.py` |
| **Case 2: Middleware (luar Odoo)** | Term 2 | `cd E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing`<br>`E:\ODOO-KELOMPOK\venv\Scripts\python.exe middleware_server.py` |
| **Test Client → Case 1 (50052)** | Term 3 | `cd E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing`<br>`E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --target localhost:50052` |
| **Test Client → Case 2 (50051)** | Term 3 | `cd E:\ODOO-KELOMPOK\custom_addons\grpc_ticketing`<br>`E:\ODOO-KELOMPOK\venv\Scripts\python.exe client.py --target localhost:50051` |
