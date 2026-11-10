# Aster Academy

MVP platform persiapan sekolah kedinasan: katalog program, pendaftaran akses oleh admin, pelajaran YouTube Unlisted, tryout singkat, jadwal, artikel, dan panel admin. Dibangun dengan Python standard library, SQLite, HTML, dan Tailwind CDN—tanpa Node atau framework JavaScript.

## Menjalankan secara lokal

1. Pastikan Python 3 tersedia.
2. Dari folder ini, buat Super Admin pertama: `python3 app.py --create-admin`.
3. Jalankan situs: `python3 app.py`.
4. Buka `http://127.0.0.1:8000` dan masuk admin melalui `/masuk`.

Database `aster.sqlite3` dan data contoh dibuat otomatis. Jika port 8000 sudah digunakan, jalankan dengan `PORT=8765 python3 app.py`.

## Alur admin

- Buat atau terbitkan program melalui `/admin`.
- Tambahkan modul, lalu pelajaran. Untuk video, masukkan ID video YouTube Unlisted; contoh ID adalah bagian setelah `v=` pada tautan YouTube.
- Permintaan akses pelajar muncul di dashboard admin. Pilih **Beri akses** untuk membuka materi bagi pelajar.
- Kelola paket tryout dan soal di `/admin/bank-soal`; buat paket, susun soal pilihan ganda A–E, pembahasan, dan status publikasi. Paket harus memiliki soal sebelum diterbitkan.
- Kelola kategori TWK, TIU, TKP, dan subkategori melalui `/admin/kategori-soal`; atur jumlah, bobot, dan ambang menurut profil aturan SKD 2026 atau profil lain.
- Saat mengelola bank, pilih tautan **Blueprint** untuk mengatur durasi, urutan kategori, jumlah soal per kategori, dan pengambilan manual atau acak. Timer mengikuti durasi blueprint dan berakhir di server. Attempt menyimpan soal, bobot, ambang, dan urutannya agar hasil acak tetap sama; hasil merangkum skor per kategori dan pencapaian ambang profil.
- Saat membuat/mengubah soal, pilih kategori, isi rich text, masukkan gambar melalui unggah/paste, dan pilih bank lain untuk penggunaan ulang tanpa duplikasi. Soal lama yang belum diberi kategori ditandai **Belum diklasifikasikan** agar kategori aslinya tidak ditebak.
- Editor soal memakai [Quill](https://quilljs.com/) gratis dan open source (BSD 3-Clause). Tabel bank, kategori, dan soal memakai DataTables serta RowReorder open source; semua dimuat dari CDN tanpa Node.
- Perbarui nama, email, dan kata sandi admin di `/profil`; tombol keluar tersedia di navigasi admin.
- Kelola izin role di `/admin/akses-role` sebagai Super Admin. Matriks mengatur izin lihat, buat, ubah, hapus, publikasi, dan persetujuan per menu/modul; server memeriksa izin untuk setiap URL dan aksi.
- Role tersedia: Super Admin, Admin, Teacher / Mentor, dan Student / Mentee. Akun lama dengan role `admin` tetap Admin; role legacy seperti `mentor` dan `mentee` dipetakan ke role kanonis saat aplikasi dimulai.
- Akses awal memakai persetujuan admin; pembayaran belum tersedia di MVP.

## Halaman

- `/` — beranda.
- `/program` — katalog dan pencarian program.
- `/program/{slug}` — detail dan kurikulum.
- `/tryout` — katalog latihan; `/tryout/{slug}` — detail latihan.
- `/jadwal` — jadwal kelas live.
- `/artikel` — artikel persiapan.
- `/dashboard` — ruang belajar pelajar.
- `/admin` — kelola program, modul, pelajaran, dan permintaan akses.
- `/admin/bank-soal` — kelola paket tryout dan soal.
- `/admin/kategori-soal` — kelola kategori/subkategori dan bobot per profil.
- `/admin/bank-soal/{id}/blueprint` — urutan, kuota, durasi, serta randomisasi sesi.
- `/profil` — pengaturan akun admin.

## Relasi data bank soal

- `question_sets` memiliki banyak `questions` dan banyak `attempts`.
- `users` memiliki banyak `attempts`.
- `attempts` memiliki banyak `attempt_answers`; setiap jawaban mengacu pada satu `questions`.
- `attempt_answers` memakai kunci gabungan `(attempt_id, question_id)` agar satu soal hanya punya satu jawaban per percobaan.
- Setelah paket pernah dipakai dalam percobaan, paket dan soalnya dikunci dari edit/hapus agar skor dan pembahasan historis tetap konsisten.
- `question_categories` mengelompokkan soal ke TWK/TIU/TKP dan subkategori; `category_scoring_rules` menyimpan jumlah, bobot benar/salah/kosong, nilai maksimum, ambang dan mode skor per profil.
- `question_banks` memiliki struktur induk-anak; `question_bank_memberships` memungkinkan soal yang sama dipakai di beberapa bank. `media_assets` dan `question_media` menyimpan metadata dan relasi gambar.
- `exam_blueprints` dan `exam_blueprint_categories` menyimpan profil aturan, urutan, kuota, dan mode pengambilan soal; `attempt_questions` menyimpan snapshot agar hasil sesi lama tidak berubah.

## Akses berbasis role

Tabel `roles`, `permissions`, dan `role_permissions` menyimpan role dan izin. Migrasi berjalan idempotent saat aplikasi dimulai, menambahkan izin baru tanpa menimpa konfigurasi izin yang sudah disimpan. Super Admin selalu memiliki akses penuh dan menjadi satu-satunya role yang dapat mengubah matriks. Izin yang tidak ada atau tidak diberikan ditolak oleh pemeriksaan server.

Matriks sudah mencakup izin untuk dashboard, program, modul, pelajaran, bank soal, soal, permintaan akses, artikel, sesi live, pengguna, role, dan profil. Halaman pengelolaan artikel, sesi live, dan pengguna belum termasuk kemampuan CRUD dalam MVP saat ini.

## Batas MVP

Tryout contoh bawaan masih satu soal; admin dapat mengelola paket multi-soal dan blueprint. Pengelolaan jadwal live dan artikel belum tersedia. Tailwind, Quill, dan DataTables memakai CDN sehingga editor/tabel interaktif memerlukan internet; bila Quill tidak termuat, form menyediakan fallback teks tetapi sisip gambar memerlukan koneksi pulih. Server lokal memakai HTTP dan disetel ke `127.0.0.1`; sebelum deployment publik, tambahkan HTTPS, cookie Secure, perlindungan login terhadap percobaan berulang, serta server produksi.


## Opaque URL contract

Resource identifiers must not be exposed in URL paths or query strings. Templates use opaque, unguessable route tokens for resource routes; backend handlers must resolve and authorize each token before loading the resource. Internal numeric IDs may remain in POST bodies for compatibility, but must never be interpolated into URLs.

Required template placeholders and route shapes:

- `SET_TOKEN`: `/admin/bank-soal/{SET_TOKEN}`, `/admin/bank-soal/{SET_TOKEN}/edit`, `/admin/bank-soal/{SET_TOKEN}/blueprint`, `/admin/bank-soal/{SET_TOKEN}/soal/baru`.
- `COURSE_TOKEN`: `/admin/kursus/{COURSE_TOKEN}/edit` and `/admin/kursus/{COURSE_TOKEN}/modul/baru`.
- `MODULE_TOKEN`: `/admin/modul/{MODULE_TOKEN}/pelajaran/baru`.
- `LESSON_TOKEN`: `/pelajaran/{LESSON_TOKEN}/selesai`.
- `TRYOUT_TOKEN`: `/tryout/{TRYOUT_TOKEN}/mulai`.
- `ATTEMPT_TOKEN`: `/tryout/{ATTEMPT_TOKEN}/jawab` and `/tryout/{ATTEMPT_TOKEN}/selesai`.

Server-generated row fragments (`ADMIN_COURSE_ROWS`, `BANK_ROWS`, `QUESTION_ROWS`, catalog cards, and lesson links) must follow the same opaque-token contract. GET filters must not contain resource IDs. Hidden form fields carrying legacy internal IDs are POST body values and are intentionally unchanged; the server must validate authorization independently.
