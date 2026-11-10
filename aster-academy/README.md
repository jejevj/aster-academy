# Aster Academy

Aster Academy adalah platform manajemen pembelajaran (LMS) dan simulasi ujian Computer Assisted Test (CAT) mandiri untuk persiapan seleksi sekolah kedinasan (Polstat STIS, PKN STAN, IPDN, STMKG, dan kementerian/lembaga terkait).

Platform ini dibangun di atas prinsip **Zero Heavy Dependency**: murni menggunakan Python Standard Library dan SQLite di sisi server, serta HTML modern berbasis Tailwind CSS, Quill, dan DataTables melalui CDN di sisi klien—tanpa memerlukan Node.js, framework JavaScript kompleks, atau paket eksternal pihak ketiga.

---

## Daftar Isi

1. [Fitur Utama](#fitur-utama)
2. [Arsitektur Sistem](#arsitektur-sistem)
3. [Keamanan & Kontrak Opaque URL](#keamanan--kontrak-opaque-url)
4. [Struktur Direktori](#struktur-direktori)
5. [Panduan Menjalankan Sistem](#panduan-menjalankan-sistem)
6. [Alur Operasional Admin](#alur-operasional-admin)
7. [Matriks Peran & Hak Akses (RBAC)](#matriks-peran--hak-akses-rbac)
8. [Struktur Data & Relasi Bank Soal](#struktur-data--relasi-bank-soal)
9. [Batasan MVP & Roadmap Teknis](#batasan-mvp--roadmap-teknis)
10. [Tim Pengembang (Aster Crew)](#tim-pengembang-aster-crew)

---

## Fitur Utama

- **Katalog Program Belajar**: Penyusunan program komprehensif berjenjang menurut instansi target, modul pembelajaran, materi video (YouTube Unlisted), dan tracking progres belajar siswa.
- **Bank Soal Terstandarisasi SKD 2026**: Manajemen bank soal hierarkis (TWK, TIU, TKP) dengan dukungan rich text, formula matematika, dan penyematan gambar media.
- **Mesin Ujian CAT & Blueprint Tryout**: Penyusunan komposisi tryout fleksibel dengan penentuan durasi, kuota per kategori, mode acak/manual, penghitungan timer server-side, dan snapshot hasil ujian yang *immutable*.
- **Profil Penilaian Resmi**: Preset kalkulasi bobot nilai SKD sesuai KepmenPANRB No. 406 Tahun 2026 (Kategori Umum dan Afirmasi) dengan validasi ambang batas (*passing grade*) dinamis.
- **Manajemen Akses & Persetujuan Pelajar**: Alur pendaftaran mandiri dengan verifikasi dan persetujuan manual oleh admin.
- **Sistem Peran Fleksibel (RBAC)**: Matriks hak akses terperinci untuk 4 peran kanonis (Super Admin, Admin, Mentor/Guru, dan Siswa) yang diaudit di setiap rute dan aksi HTTP.

---

## Arsitektur Sistem

Aplikasi menerapkan pola arsitektur berlapis (MVC) modular:

```text
aster-academy/
├── app.py                      Entry point server HTTP (ThreadingHTTPServer)
├── controllers/
│   └── http_controller.py      Pusat penanganan HTTP, parsing request, routing, dan template rendering
├── services/                   Domain logic terisolasi
│   ├── authentication.py       Hashing PBKDF2, verifikasi kredensial, dan proteksi sesi
│   ├── formatting.py           Sanitasi string, HTML entity encoding, dan format mata uang
│   ├── menu_service.py         Resolusi menu sidebar dinamis berdasarkan izin RBAC
│   ├── public_references.py    Penerjemah token opaque eksternal ke internal database ID
│   ├── question_service.py     Kalkulasi scoring, timer ujian, snapshot attempt, dan blueprint tryout
│   └── rich_text.py            Sanitasi whitelist HTML (Quill output) & pencegahan XSS
├── repositories/               Layer persistensi SQLite
│   ├── database.py             Konfigurasi path dan timeout koneksi SQLite
│   ├── public_reference_repository.py  Registry token opaque URL
│   ├── question_repository.py  Akses persistensi bank soal dan kategori
│   └── sqlite_repository.py    Factory koneksi SQLite dengan row-factory dan foreign keys
├── models/                     Data transfer object dan konfigurasi basis data
├── templates/                  Template HTML murni dengan substitusi token template
└── core.py                     Legacy compatibility layer, konstanta global, dan skema bootstrap
```

---

## Keamanan & Kontrak Opaque URL

Sistem menerapkan prinsip *Defensive Security by Design*:

### 1. Kontrak Opaque URL (Anti Resource Enumeration)
Pengenal numerik basis data internal (`id` bertipe integer) **dilarang keras** diekspos pada rute URL publik maupun query string. Seluruh rute publik dan pengelola wajib menggunakan token acak terenkripsi yang aman (*opaque URL tokens*).

Pola rute terproteksi yang wajib dipatuhi:
- Bank Soal: `/admin/bank-soal/{SET_TOKEN}`, `/admin/bank-soal/{SET_TOKEN}/edit`, `/admin/bank-soal/{SET_TOKEN}/blueprint`, `/admin/bank-soal/{SET_TOKEN}/soal/baru`
- Kursus/Program: `/admin/kursus/{COURSE_TOKEN}/edit`, `/admin/kursus/{COURSE_TOKEN}/modul/baru`
- Modul: `/admin/modul/{MODULE_TOKEN}/pelajaran/baru`
- Pelajaran: `/pelajaran/{LESSON_TOKEN}/selesai`
- Sesi Tryout: `/tryout/{TRYOUT_TOKEN}/mulai`, `/tryout/{ATTEMPT_TOKEN}/jawab`, `/tryout/{ATTEMPT_TOKEN}/selesai`, `/tryout/result/{ATTEMPT_TOKEN}`

Server secara aktif menolak request yang mencoba menyuntikkan ID integer langsung pada segmen rute ini dengan respons HTTP 404/403.

### 2. Autentikasi dan Proteksi Sesi
- Password dienkripsi menggunakan algoritma `PBKDF2-HMAC-SHA256` dengan 240.000 iterasi dan salt kriptografis unik 16-byte.
- Sesi menggunakan token berdaya acak tinggi yang disimpan dalam basis data sebagai digest SHA-256 dengan atribut cookie `HttpOnly` dan `SameSite=Lax`.
- Setiap transaksi formulir POST divalidasi menggunakan token CSRF unik yang terikat pada sesi pengguna.

---

## Panduan Menjalankan Sistem

### Prasyarat
- Python 3.10 atau versi yang lebih baru (tanpa instalasi `pip` tambahan).
- Koneksi internet untuk memuat Tailwind CDN, Quill, dan DataTables pada browser pengelola.

### Langkah Menjalankan
1. Masuk ke direktori proyek:
   ```bash
   cd aster/aster-academy
   ```
2. Buat akun Super Admin pertama:
   ```bash
   python3 app.py --create-admin
   ```
   Ikuti instruksi di terminal: masukkan email, nama, dan kata sandi minimal 12 karakter.
3. Jalankan server:
   ```bash
   python3 app.py
   ```
4. Buka peramban web pada alamat:
   - Portal Publik: `http://127.0.0.1:8000`
   - Panel Masuk: `http://127.0.0.1:8000/masuk`
   - Panel Administrasi: `http://127.0.0.1:8000/admin`

*Catatan Port:* Apabila port `8000` sedang dipakai oleh aplikasi lain, tentukan port alternatif melalui environment variable:
```bash
PORT=8765 python3 app.py
```

---

## Alur Operasional Admin

1. **Penerbitan Program Belajar**:
   - Buka `/admin` -> Tambah Program.
   - Buat struktur Modul, lalu tambahkan Pelajaran. Masukkan ID video YouTube Unlisted (string karakter setelah parameter `v=`).
2. **Persetujuan Akses Pelajar**:
   - Pendaftaran peserta baru akan masuk dengan status `pending`.
   - Admin memeriksa dan menekan tombol **Beri akses** di dashboard admin untuk mengaktifkan materi bagi siswa.
3. **Penyusunan Bank Soal**:
   - Buka menu `/admin/bank-soal`.
   - Buat paket/bank baru, input pertanyaan menggunakan rich text editor Quill, sisipkan gambar (otomatis dikelola pada direktori `media/`), serta tentukan pilihan jawaban A–E beserta pembahasannya.
4. **Konfigurasi Kategori & Ambang Batas**:
   - Buka `/admin/kategori-soal` untuk mengelola kategori TWK, TIU, TKP beserta subkategori belajar.
   - Tetapkan bobot benar, salah, kosong, serta ambang kelulusan berdasarkan regulasi target.
5. **Penyusunan Blueprint Ujian**:
   - Pada bank soal terkait, pilih **Blueprint Tryout** (`/admin/bank-soal/{SET_TOKEN}/blueprint`).
   - Tentukan durasi pengerjaan, kuota soal per kategori, profil aturan nilai, serta pilih mode pengambilan soal (**Manual** sesuai urutan terdaftar atau **Acak** dalam kategori).

---

## Matriks Peran & Hak Akses (RBAC)

Sistem membedakan empat peran pengguna kanonis:

| Modul / Domain | Super Admin | Admin | Mentor / Guru | Siswa / Mentee |
| :--- | :---: | :---: | :---: | :---: |
| **Dashboard Admin** | Penuh | Penuh | Terbatas | Tidak Ada Akses |
| **Program & Modul** | CRUD + Terbitkan | CRUD + Terbitkan | Kelola Materi Ditugaskan | Lihat yang Terdaftar |
| **Bank Soal & Soal** | CRUD + Terbitkan | CRUD + Terbitkan | Buat & Edit Soal | Mengikuti Tryout |
| **Kategori & Blueprint**| CRUD | CRUD | Lihat Blueprint | Tidak Ada Akses |
| **Persetujuan Akses** | Kelola & Setujui | Kelola & Setujui | Hanya Lihat | Mengajukan Akses |
| **Akses Matriks Peran** | Penuh (Eksklusif) | Tidak Ada Akses | Tidak Ada Akses | Tidak Ada Akses |

*Catatan:* Konfigurasi matriks hak akses dapat dimutakhirkan secara dinamis oleh Super Admin melalui antarmuka `/admin/akses-role`.

---

## Struktur Data & Relasi Bank Soal

```text
[question_banks] 1 ──< n [question_bank_memberships] n >── 1 [questions]
       │                                                         │
       v                                                         v
[exam_blueprints] 1 ──< n [exam_blueprint_categories]     [question_options (A-E)]
       │                           │                             │
       │                           v                             v
       │               [question_categories]       [question_option_scores]
       v                           │
[attempts] 1 ──< n [attempt_questions (Snapshot)]
       │                           │
       └──< n [attempt_answers] ───┘
```

- **Integritas Historis**: Begitu sebuah bank soal digunakan dalam sesi tryout (`attempts`), bank dan butir soalnya terkunci dari modifikasi destruktif agar kalkulasi skor dan evaluasi historis siswa tetap valid.
- **Snapshot Immutability**: Tabel `attempt_questions` menyimpan salinan instan butir soal, opsi jawaban, dan bobot skor pada detik pertama ujian dimulai, sehingga perubahan materi di kemudian hari tidak mempengaruhi rekaman nilai peserta.

---

## Batasan MVP & Roadmap Teknis

### Batasan Versi Saat Ini
- Transaksi pembayaran masih dinonaktifkan (akses diberikan manual oleh admin).
- Modul pengelolaan jadwal kelas live dan artikel publik masih bersifat tampilan statis/baca saja (CRUD admin sedang dalam tahap penyelesaian).
- Dependency antarmuka interaktif (Quill dan DataTables) mengandalkan CDN resmi; fallback input formulir sederhana otomatis aktif saat peramban berada dalam kondisi luring.
- Server lokal beroperasi pada protokol HTTP dengan pengikatan `127.0.0.1`.

### Roadmap Menuju Produksi
1. Perbaikan arsitektur modular: Mengurai `controllers/http_controller.py` menjadi modul pengendali domain independen.
2. Suite Pengujian Otomatis: Implementasi unit dan regression test komprehensif untuk validasi migrasi skema, kontrak opaque token, dan kalkulasi ujian.
3. Hardening Keamanan Produksi: Penerapan cookie Secure HTTPS, throttling/rate-limiting upaya login, dan integrasi WSGI/ASGI runner berkemampuan produksi.

---

## Tim Pengembang (Aster Crew)

Proyek ini dikawal oleh lima spesialis rekayasa perangkat lunak:

1. **Bimo (Jawa) — Backend Engineer**  
   Pengawal arsitektur Python stdlib, pembagian layer service/repository, refactoring controller, dan integritas alur HTTP.
2. **Wayan (Bali & Nusa Tenggara) — Frontend Engineer**  
   Perancang antarmuka ramah pengguna berbasis Tailwind CDN, editor rich text Quill, interaktivitas DataTables, dan formulir aksesibel.
3. **Sutan (Sumatera) — Database & Schema Engineer**  
   Penjaga integritas skema SQLite, migrasi idempotent non-destruktif, manajemen blueprint, dan kepatuhan profil ujian kedinasan.
4. **Daeng (Sulawesi) — QA & Test Engineer**  
   Pemburu bug dan blocker kompilasi, perancang test suite otomatis, verifikator kontrak opaque token, dan penjamin kualitas scoring.
5. **Pace (Papua & Maluku) — Security & Deployment Engineer**  
   Benteng pertahanan autentikasi, proteksi sesi dan CSRF, audit matriks hak akses (RBAC), serta kesiapan deployment produksi.
