# Plan: Mengubah Aster Menjadi Website Kursus Online

## Addendum rencana: arsitektur MVC, navigasi, dan RBAC dinamis

**Status:** perencanaan; belum diimplementasikan. Fitur Aster yang sudah berjalan tetap dipertahankan selama refactor.

### Tujuan

- Pisahkan aplikasi Python ke pola MVC berlapis: `models/`, `repositories/`, `services/`, `controllers/`, `routes/`, `templates/`, dan `static/`. Tetap gunakan SQLite dan framework minimal yang sesuai; jangan berpindah framework besar tanpa kebutuhan teknis yang jelas.
- Jadikan satu registri route/menu sebagai sumber konsisten untuk rute, label, izin, dan navigasi.
- Sediakan konfigurasi menu yang dapat dikelola Super Admin: label, route, parent, urutan, grup, ikon, status aktif, serta izin yang diperlukan.
- Tampilkan konfigurasi akses per role dalam bentuk checklist menu; pilihan menu parent/child jelas dan dapat diatur tanpa mengubah kode.
- Sediakan drag-and-drop ordering menu. Urutan menentukan posisi menu; relasi parent disunting eksplisit dan tervalidasi agar tidak terjadi parent hilang, siklus, atau menu tak terjangkau.
- Setelah login, navbar publik menampilkan tombol profil menuju halaman profil pengguna.
- Sidebar admin dikelompokkan dengan judul grup yang konsisten. Pada mobile, sidebar menjadi drawer geser dengan tombol buka/tutup, backdrop, dan navigasi yang tetap mudah diakses; menu tidak turun menjadi navbar bertumpuk.
- Gunakan pustaka dan alat UI/UX open source; tidak menggunakan AIDesigner.

### Model data dan aturan akses

- Tambahkan `menu_items` (`id`, `key`, `label`, `route_name`, `parent_id`, `group_name`, `sort_order`, `icon`, `is_active`) dan hubungan route-permission yang tervalidasi dari registri aplikasi.
- Pertahankan `roles`, `permissions`, `role_permissions` atau migrasikan bertahap ke relasi role-menu-action; migrasi idempotent dan tidak menghapus izin tersimpan.
- Halaman Akses & Role berorientasi **pilih role → checklist menu → simpan**. Menu parent dapat memberi akses turunan hanya menurut aturan eksplisit; server tetap memeriksa izin untuk setiap route dan aksi CRUD.
- Super Admin selalu punya akses pemulihan penuh, termasuk bank soal, menu, route, dan konfigurasi izin. Hanya Super Admin yang dapat mengubah akses role/menu.
- Route yang tidak terdaftar, menu tidak aktif, dan izin yang tidak dikenal ditolak secara default. Menyembunyikan menu bukan pengganti pemeriksaan server.

### Tahapan implementasi

1. Inventarisasi route, query, template, permission, dan perilaku aplikasi saat ini; tetapkan peta modul dan kontrak migrasi tanpa mengubah perilaku.
2. Refactor MVC secara bertahap: mulai dari model/database dan repository, pindahkan logika bisnis ke service, lalu controller/route; pertahankan entrypoint lama sebagai adaptor sementara.
3. Buat registri route/menu, tabel konfigurasi menu, migrasi SQLite idempotent, dan validasi parent/order.
4. Bangun ulang halaman Akses & Role menjadi per-role checklist menu dan aksi; tambahkan kontrol reorder serta pengaturan parent/group dan validasi izin server.
5. Perbarui navbar publik untuk status login dan tombol profil; rapikan sidebar admin dengan grouping serta drawer geser untuk mobile.
6. Jalankan pemeriksaan migrasi pada salinan DB, cek import/startup dan rute utama, uji matriks akses tiap role, lalu tinjau tampilan desktop/mobile. Perbarui README dan ZIP sesudah integrasi lulus.

### Pembagian subagent dan batas kerja

- **UI/UX (open source):** spesifikasi interaksi navbar, grouping sidebar, checklist akses/menu, drag-and-drop, dan drawer mobile; tidak mengubah aturan bisnis backend.
- **Frontend:** template/CSS/JavaScript untuk navbar profil, sidebar grup, drawer mobile, dan form checklist/reorder; konsumsi kontrak backend yang disepakati.
- **Backend:** route registry, validasi route/action, layanan konfigurasi akses dan menu, serta proteksi endpoint.
- **Database/MVC:** migrasi SQLite, model/repository, pemisahan service/controller, dan kompatibilitas data lama.
- Orchestrator menetapkan kontrak bersama, membatasi subagent pada file berbeda, mengintegrasikan patch, dan melakukan pemeriksaan akhir. Jika batas subagent tercapai, lanjutkan pekerjaan lokal per divisi tanpa mengulang analisis yang sudah selesai.

### Aturan efisiensi token dan koordinasi

- Setiap tugas subagent harus berisi satu hasil yang dapat diperiksa, jalur file yang boleh disentuh, batasan, dan format laporan singkat.
- Kirim konteks minimum yang diperlukan; hindari meminta eksplorasi umum atau mengulang seluruh riwayat proyek.
- Delegasikan hanya tugas yang paralel dan tidak berbagi file; tunggu hasil saat integrasi memang bergantung padanya.
- Catat keputusan dan progres pada plan/README agar konteks pemulihan tetap ringkas. Laporkan hasil, file berubah, pemeriksaan, serta blocker secara singkat.

### Kriteria penerimaan addendum

- Pengguna login melihat tombol Profil pada navbar publik; pengunjung anonim tetap melihat aksi Masuk/Daftar.
- Sidebar admin mempunyai grup menu yang teratur dan pada lebar mobile terbuka sebagai drawer geser, bukan menu vertikal permanen.
- Super Admin dapat memilih role, mencentang menu/aksi yang boleh diakses, menyimpan, dan melihat hasilnya; konfigurasi bertahan setelah restart.
- Daftar menu berasal dari registri route, bisa diurutkan dengan drag-and-drop, dan memiliki parent/group yang tervalidasi.
- Akses URL langsung dan aksi POST konsisten dengan checklist; perubahan izin tidak hanya berpengaruh pada tampilan menu.
- Refactor mempertahankan fitur kursus, akun, bank soal, kategori, blueprint, dan attempt yang ada; migrasi tidak kehilangan data.
- Aset UI/UX yang ditambahkan berlisensi open source dan tidak memerlukan AIDesigner.

## Addendum rencana: bank soal, blueprint ujian, dan aturan penilaian

**Status:** implementasi inti tersedia di aplikasi. Rincian SKD di bawah memakai aturan yang berlaku pada 2026 dan disimpan sebagai profil versi, bukan angka permanen di kode.

### Acuan aturan SKD sekolah kedinasan

Rujukan utama adalah [KepmenPANRB Nomor 406 Tahun 2026](https://jdih.menpan.go.id/dokumen-hukum/keputusan-menteri-pendayagunaan-aparatur-negara-dan-reformasi-birokrasi-nomor-406-tahun-2026-tentang-2121) dan [PermenPANRB Nomor 13 Tahun 2026](https://peraturan.bpk.go.id/Details/352447/permen-panrb-no-13-tahun-2026). Untuk blueprint latihan SKD sekolah kedinasan TA 2026, rencana awal mengikuti:

| Materi | Jumlah butir | Aturan skor per jawaban | Nilai maksimal | Ambang batas umum 2026 |
|---|---:|---|---:|---:|
| TWK | 30 | Benar 5; salah/kosong 0 | 150 | 65 |
| TIU | 35 | Benar 5; salah/kosong 0 | 175 | 80 |
| TKP | 45 | Pilihan bernilai 1–5; kosong 0 | 225 | 156 |
| **Total** | **110** | **100 menit** | **550** | Memenuhi setiap ambang kategori |

Aturan afirmasi daerah tertentu memiliki ambang khusus: nilai kumulatif minimal 281 dan TIU minimal 55. Penggunaan kategori afirmasi harus menjadi profil kelulusan tersendiri; jangan otomatis menerapkannya ke semua peserta. Angka ambang dan aturan per tahun disimpan sebagai konfigurasi bertanggal/sumber, agar profil 2027 atau seleksi instansi lain dapat berbeda. Durasi, jumlah dan urutan kategori juga harus dapat dikonfigurasi untuk format non-SKD.

Materi induk SKD adalah TWK, TIU, dan TKP. Subkategori awal mengikuti kisi-kisi resmi yang berlaku, lalu admin dapat mengelola tambahan subkategori untuk keperluan belajar. Subkategori untuk latihan tidak boleh disajikan sebagai distribusi jumlah resmi jika regulasi tidak menetapkan kuotanya.

### Struktur bank dan penggunaan ulang soal

- Bank soal memiliki struktur induk-anak (`parent_bank_id`) untuk mengelompokkan bank menurut organisasi, sekolah/jalur, mata uji, atau topik.
- Setiap soal memiliki satu bank pemilik/canonical sebagai asal dan pengelola utama.
- Satu soal dapat dimasukkan ke bank lain melalui relasi keanggotaan banyak-ke-banyak. Di form soal sediakan pilihan **“Masukkan soal ini ke bank …”**; penggunaan ulang menunjuk soal yang sama, bukan membuat salinan.
- Menghapus keanggotaan dari bank lain tidak menghapus soal pemilik. Hapus permanen memerlukan hak yang sesuai dan dilarang bila sudah dipakai oleh sesi/attempt historis.
- Kategori dan subkategori soal dikelola sebagai taksonomi yang dapat berversi/diaktifkan per profil seleksi, bukan kategori teks bebas yang sulit difilter.

### Blueprint sesi ujian

- Admin membuat blueprint/sesi ujian dari profil aturan dan memilih bank sumber.
- Daftar kategori memiliki urutan eksplisit, kuota jumlah soal per kategori, dan pengaturan acak per kategori. Kuota TWK/TIU/TKP untuk profil SKD 2026 diisi 30/35/45; sesi hanya dapat diterbitkan bila jumlah bank cukup untuk memenuhi semua kuota.
- Mode manual memakai urutan soal hasil drag-and-drop. Mode acak memilih soal secara acak dari pool per kategori tetapi tetap memenuhi kuota, dan tetap menampilkan kategori dalam urutan blueprint.
- Simpan hasil pemilihan soal dan urutan final pada saat attempt dimulai; reload halaman tidak boleh mengacak ulang soal. Randomisasi pilihan jawaban tidak menjadi default, khususnya untuk TKP yang memiliki bobot berbeda pada setiap opsi.
- Admin dapat menetapkan durasi, ambang kategori/total, profil peserta (umum/afirmasi bila berlaku), dan aturan skor dari profil regulasi. Validasi blueprint menampilkan jumlah tersedia, jumlah yang diminta, bobot, dan ambang sebelum publikasi.

### Editor soal dan media

- Form soal mendukung rich text untuk stem, setiap opsi, jawaban/pembahasan, dan instruksi. Opsi jawaban dapat berupa teks kaya, gambar, atau gabungan keduanya.
- Admin dapat menyisipkan gambar dengan unggah dan paste ke editor. Simpan metadata media di SQLite dan berkas gambar pada penyimpanan aplikasi; validasi MIME/ukuran, alt text, izin akses, serta nama berkas. Tidak termasuk OCR otomatis pada tahap ini.
- HTML editor harus disanitasi dengan allowlist; blok script, event handler, iframe sembarang, dan URL berbahaya. Gambar harus tetap dapat ditampilkan pada soal, opsi, pembahasan, dan snapshot attempt.
- Pilih editor ringan yang bisa dipasang tanpa Node/framework, serta siapkan strategi aset (CDN atau berkas lokal) dan fallback pesan bila editor gagal dimuat.

**Keputusan editor:** gunakan Quill 2, editor rich text open source berlisensi BSD 3-Clause. Pemasangan CDN gratis dan tidak memerlukan Node, sesuai dokumentasi resmi Quill; siapkan pesan fallback jika koneksi CDN tidak tersedia. [Lisensi Quill](https://github.com/slab/quill/blob/main/LICENSE) · [Panduan CDN resmi](https://quilljs.com/docs/installation/).

### Tabel pengelolaan

- Tabel bank dan daftar soal memakai DataTables untuk pencarian, pengurutan, paging, dan responsivitas.
- Aktifkan RowReorder atau kontrol drag-and-drop yang setara pada daftar soal; perubahan posisi harus disimpan ke urutan manual per bank/paket dan dikembalikan setelah muat ulang.
- Filter tabel: bank pemilik/anggota, kategori/subkategori, status, tingkat kesulitan, dan status penggunaan. Tampilkan juga jumlah soal tersedia dibandingkan kebutuhan blueprint.
- Saat blueprint mengaktifkan randomisasi, urutan manual tetap tersedia sebagai urutan dasar/pratinjau dan kategori tetap mengikuti urutan sesi.

### Rencana relasi SQLite yang ditambahkan

- `question_banks`: bank, `parent_bank_id`, pemilik, nama, status.
- `questions`: bank pemilik, kategori/subkategori, stem rich text, tipe jawaban, tingkat kesulitan, status, versi.
- `question_bank_memberships`: relasi bank-ke-soal untuk penggunaan ulang dan posisi manual; unik per pasangan bank-soal.
- `question_categories` dan `exam_rule_profiles`: taksonomi kategori dan versi aturan (tahun, sumber, periode berlaku, durasi, total butir, aturan kelulusan).
- `category_scoring_rules` / `question_option_scores`: bobot per kategori dan bobot tiap opsi (terutama TKP); jawaban kosong mendapat 0 sesuai profil.
- `exam_blueprints` dan `exam_blueprint_categories`: profil, bank sumber, urutan kategori, kuota, mode acak/manual, durasi, dan ambang.
- `exam_sessions`, `attempts`, `attempt_questions`, dan `attempt_answers`: sesi dan snapshot pemilihan soal/urutannya, isi/opsi/skor pada saat ujian, jawaban dan hasil historis yang tidak berubah saat bank diedit.
- `media_assets`: metadata gambar dan relasinya dengan soal/opsi/pembahasan; berkas disimpan di storage aplikasi.

Perubahan ini memperluas tabel `question_sets`, `questions`, `attempts`, dan `attempt_answers` yang sudah ada. Migrasi harus menjaga data lama, menautkan soal seed ke bank/kategori default, dan menyimpan versi/snapshot agar hasil attempt lama tetap benar.

### Tahapan implementasi lanjutan

1. Migrasi SQLite non-destruktif: bank hierarkis, keanggotaan ulang, kategori, profil aturan dan media.
2. Admin bank soal: DataTables, filter, CRUD, editor rich text, unggah/paste gambar, dan drag-and-drop urutan.
3. Admin blueprint: profil SKD 2026 sebagai preset, urutan/kuota kategori, validasi jumlah soal dan aturan skor, opsi randomisasi.
4. Runner ujian: memilih soal per kategori, menyimpan snapshot dan urutan sekali saat mulai, timer yang batas waktunya ditegakkan server, skor TWK/TIU/TKP, serta ambang umum/afirmasi sesuai profil.
5. Uji migrasi pada salinan DB, skenario skor per opsi TKP, randomisasi/kuota, soal digunakan lintas bank, media, dan perlindungan riwayat.

Halaman kategori dapat ditemukan dari menu **Bank Soal → Kategori Soal** di admin; kategori dipilih saat membuat/mengubah soal dan tersedia sebagai filter daftar.

Implementasi tersedia: taksonomi TWK/TIU/TKP dan subkategori; bobot serta ambang per profil; editor soal Quill untuk rich text dan gambar; DataTables untuk daftar bank, soal, dan kategori; drag-and-drop urutan soal; bank induk dan reuse soal; serta blueprint kategori berurutan dengan kuota dan pilihan manual/acak. Attempt menyimpan snapshot soal, opsi, skor, aturan, dan urutan saat sesi dimulai. Verifikasi deployment dan uji alur lintas browser masih menjadi pekerjaan rilis.

### Kriteria penerimaan fitur bank/ujian

- Soal memiliki bank pemilik, dapat dimasukkan ke beberapa bank lain tanpa duplikasi, dan setiap daftar bank menunjukkan asal soal.
- Admin dapat mengelola kategori/subkategori dan melihat bobot/aturan skor aktif beserta sumber dan tahun berlakunya.
- Preset SKD 2026 menetapkan 30 TWK, 35 TIU, 45 TKP; 100 menit; skor maksimal 550; ambang umum 65/80/156 dan profil afirmasi 281 total serta TIU 55.
- Blueprint tidak dapat diterbitkan jika kuota kategori melebihi soal yang tersedia atau konfigurasi skor tidak lengkap.
- Soal dan opsi menerima teks kaya serta gambar; HTML berbahaya ditolak/dibersihkan.
- Tabel DataTables mendukung pencarian, sorting, paging, dan drag-and-drop posisi yang persisten.
- Randomisasi memilih soal di dalam kuota setiap kategori, tidak mengubah urutan kategori, dan hasil pilihan serta urutan tetap sama sepanjang attempt.
- Snapshot memastikan perubahan bank atau penghapusan keanggotaan tidak mengubah soal, bobot, skor, maupun pembahasan attempt yang sudah dimulai.
- Durasi tersimpan pada snapshot dan batas waktu diperiksa server saat submit; preset sesi biasa juga memakai timer dari durasi bank.
- Ambang profil resmi hanya dibandingkan bila jumlah soal dan skor maksimum sesi sesuai profil penuh; latihan dengan kuota parsial menampilkan skor tanpa klaim lulus/gagal profil.

### Keputusan produk yang kini tercatat

- Rilis awal pemodelan aturan: **SKD Sekolah Kedinasan TA 2026**. Aturan tahun berikutnya disimpan sebagai profil baru setelah sumber resmi diperiksa.
- Sesi preset menampilkan TWK, TIU, lalu TKP sebagai urutan awal yang dapat diatur admin; jumlah soal dan bobot diambil dari profil aturan, bukan tebakan.
- Kategori tambahan di luar SKD (misalnya tes akademik atau seleksi khusus instansi) dibuat sebagai profil/kategori yang dapat dikonfigurasi, bukan disamakan dengan aturan SKD.

## Addendum rencana: akses berbasis peran (RBAC)

**Status:** mekanisme dasar diimplementasikan; rincian UX dan cakupan lanjutan tetap menjadi acuan pengembangan. Empat role inti:

| Role | Tujuan awal |
|---|---|
| Super Admin | Mengelola izin role, menu, dan aksi CRUD; akses penuh sebagai pemulihan administratif. |
| Admin | Mengelola operasi akademi sesuai izin yang diberikan Super Admin. |
| Teacher / Mentor | Mengelola kelas/materi/peserta sesuai izin yang diberikan; tidak mengelola role kecuali diberi izin khusus. |
| Student / Mentee | Mengakses program, materi, tryout, progres, dan profil miliknya. |

- Super Admin mendapat halaman **Akses & Role** dengan matriks role × menu/modul × aksi (`view`, `create`, `update`, `delete`, serta aksi khusus seperti `publish`, `approve access`, `manage users`). Perubahan izin berlaku pada pemeriksaan server, bukan hanya menyembunyikan menu.
- Menu tampil hanya bila role memiliki izin `view`; setiap URL dan POST juga mengecek izin aksi. Tolak secara default jika permission tidak dikenal atau tidak diberikan.
- Seed izin awal least-privilege: Super Admin penuh; Admin mendapat operasi akademi; Teacher/Mentor mendapat menu mengajar dan pengelolaan yang ditetapkan; Student/Mentee hanya akses belajar milik sendiri. Super Admin mengubah izin Admin/Teacher/Student. Hanya Super Admin yang dapat mengubah matriks role.
- Jangan izinkan role mengunci dirinya sendiri dari halaman pengaturan yang sedang dipakai: simpan perubahan secara transaksional, tampilkan konfirmasi/hasil, dan tetap pertahankan bypass Super Admin yang ditetapkan sistem. Pembuatan admin awal menyiapkan Super Admin.
- Data model aktif: `roles`, `permissions`, `role_permissions`; migrasi idempotent mempertahankan setelan izin, menautkan role lama, dan setup admin awal membuat Super Admin.
- Uji matriks akses untuk setiap role pada menu, URL langsung, aksi CRUD dan data milik pengguna; perubahan izin harus berlaku tanpa perlu menebak dari label role.

## Tujuan

Mengubah landing page Aster menjadi platform belajar online yang memungkinkan pengunjung menemukan kursus, membuat akun, mendaftar ke kursus, belajar per modul, dan melanjutkan progresnya. Admin dapat mengelola materi dari panel tanpa mengubah HTML secara manual.

## Arah produk

**Nama kerja:** Aster Academy  
**Audiens awal:** calon peserta sekolah kedinasan yang memerlukan belajar terarah, latihan CAT, pembahasan soal, dan bimbingan.  
**Bahasa antarmuka:** Bahasa Indonesia.  
**Pengalaman belajar:** kursus mandiri, tersusun dalam modul dan pelajaran, dapat dibuka di desktop maupun ponsel.

### Asumsi MVP

- Program belajar dapat dikelompokkan menurut sekolah/jalur seleksi; tryout menjadi salah satu fitur inti selain materi video dan kelas live.
- Pembayaran ditunda ke tahap berikutnya. MVP tidak memiliki checkout; akses program/paket dikelola admin.
- Video pelajaran menggunakan embed YouTube Unlisted; file video tidak diunggah ke server aplikasi.
- Daftar kursus dan materi awal belum ditentukan; implementasi awal menggunakan data contoh sampai konten final tersedia.
- Satu akun/peran admin mengelola kursus dan akses pelajar. Fitur instruktur mandiri dan pembayaran berada di tahap lanjutan.
- Tetap menggunakan Python standard library dan SQLite, tanpa Node atau framework JavaScript. Tailwind tetap melalui CDN.

## Struktur halaman

> Addendum bank soal di atas memperinci dan menggantikan bagian model data, tryout, dan admin lama jika ada perbedaan.

### Area publik

- `/` — Beranda Aster Academy: nilai utama, pencarian, kursus pilihan, kategori, dan ajakan mulai belajar.
- `/program` — Katalog bimbel per sekolah/jalur, dengan pencarian dan filter.
- `/program/{slug}` — Detail program: varian/paket, fasilitas, kurikulum, mentor, jadwal, ulasan, dan permintaan akses.
- `/tryout` dan `/tryout/{slug}` — Katalog paket tryout dan detail paket latihan.
- `/jadwal` — Jadwal kelas live, dapat difilter menurut jalur dan jenis materi.
- `/artikel` dan `/artikel/{slug}` — Pusat informasi dengan pencarian dan filter sekolah/jalur.
- `/schools/match` — Alat pencocokan sekolah (opsional; baru dibuat setelah kebutuhan dan tata kelola data disetujui).
- `/signup` dan `/login` — Pembuatan akun dan masuk.

### Area pelajar

- `/dashboard` — Program/paket aktif, progres belajar, skor tryout terakhir, jadwal kelas, dan tombol lanjut belajar.
- `/learn/{program-slug}/{lesson-id}` — Pemutar pelajaran, daftar modul, materi teks/tautan, serta navigasi pelajaran sebelumnya dan berikutnya.
- `/tryouts/{slug}/start` dan `/tryouts/{slug}/result` — Mengerjakan tryout bertimer dan melihat skor serta pembahasan setelah selesai.
- Aksi “Tandai selesai” dan simpan jawaban untuk melanjutkan progres.

### Area admin

- `/admin` — Ringkasan jumlah kursus dan pelajar.
- `/admin/courses` — Buat, ubah, terbitkan, arsipkan, dan atur urutan kursus.
- `/admin/courses/{id}/curriculum` — Kelola modul dan pelajaran, termasuk tautan video dan materi pendamping.
- `/admin/bank-soal` — Kelola bank hierarkis, soal lintas bank, kategori, media, dan urutan.
- `/admin/blueprints` — Kelola blueprint sesi: profil aturan, kategori, kuota, urutan, bobot, durasi, ambang, dan randomisasi.
- `/admin/akses-role` — Super Admin mengatur izin menu dan aksi tiap role.

## Fitur dan alur utama

1. Pengunjung menjelajahi katalog dan membuka detail kursus.
2. Pengunjung mendaftar atau masuk sebelum mendaftar ke kursus.
3. Kursus muncul di dashboard pelajar setelah pendaftaran berhasil.
4. Pelajar membuka pelajaran, menonton video atau membaca materi, lalu menandai pelajaran selesai.
5. Aster menyimpan progres dan menghitung persentase penyelesaian kursus.
6. Admin mengelola kursus, modul, dan pelajaran dari panel admin.

## Model data SQLite

- `users`: nama, email unik, hash kata sandi, role tertaut, waktu pembuatan.
- `roles`, `permissions`, `role_permissions`: role, izin menu/aksi, dan matriks hak akses yang dikelola Super Admin.
- `courses`: slug unik, judul, ringkasan, deskripsi, kategori, tingkat, durasi, URL gambar, harga, status publikasi, waktu pembaruan.
- `modules`: kursus, judul, dan urutan.
- `lessons`: modul, judul, isi teks, URL video, URL materi, durasi, dan urutan.
- `enrollments`: pelajar, kursus, status, tanggal pendaftaran; satu pendaftaran per pelajar per kursus.
- `lesson_progress`: pelajar, pelajaran, status selesai, waktu penyelesaian; satu catatan progres per pelajaran per pelajar.
- `institutions` dan `programs`: daftar sekolah/jalur serta program belajar yang ditawarkan.
- `packages` dan `enrollments`: paket, harga, status pembelian/pemberian akses, waktu mulai/berakhir.
- `question_banks`, `question_bank_memberships`, `question_categories`, dan `questions`: bank pemilik/hierarki, reuse antarbank, kategori, opsi rich text/gambar, bobot jawaban, dan versi soal. Detail relasi lihat addendum.
- `exam_rule_profiles`, `exam_blueprints`, `exam_blueprint_categories`, `exam_sessions`, `attempt_questions`, `attempts`, dan `attempt_answers`: aturan versi, kuota/urutan kategori, randomisasi, snapshot ujian, jawaban, skor, serta analisis hasil.
- `live_sessions`: topik, kategori materi, jadwal, durasi, mentor, tautan sesi, status.
- `articles` dan `testimonials`: konten informasi dan bukti sosial yang dikelola admin.
- Tabel `pages` dan `waitlist` yang sudah ada dipertahankan selama migrasi agar konten lama tidak hilang; penggunaannya setelah peluncuran ditentukan saat implementasi.

## Arah desain

- Ikuti hierarki informasi situs bimbingan persiapan seleksi: manfaat utama, bukti kepercayaan, pilihan program/tryout, cara belajar, kelas live, cerita alumni, dan CTA.
- Hapus arah glassmorphism. Gunakan antarmuka pendidikan yang terang, jelas, responsif, dan memprioritaskan keterbacaan.
- Pertahankan warna biru Aster sebagai aksen/identitas, tetapi gunakan bidang putih atau netral untuk konten dan kartu.
- Jangan menyalin logo, teks, foto, testimoni, atau aset kedinasan.id; gunakan struktur dan pola fitur umum saja.

## Rencana pengerjaan

### Tahap 1 — Fondasi aplikasi

- Petakan struktur paket Aster yang ada dan tetapkan halaman `/` sebagai beranda kursus.
- Tambahkan skema SQLite baru dengan migrasi yang tidak menghapus tabel atau data lama.
- Pisahkan penanganan data, autentikasi, dan render halaman dari satu file server agar fitur mudah dikembangkan.
- Siapkan data contoh untuk kursus, modul, dan pelajaran.

### Tahap 2 — Beranda dan katalog program

- Bangun beranda Aster Academy dengan CTA, program unggulan, fitur tryout/materi/live class, bukti sosial, dan FAQ.
- Bangun katalog program dan katalog tryout dinamis dari SQLite, dengan pencarian/filter sekolah atau jalur.
- Bangun detail program dan varian paket beserta fasilitas, kurikulum, mentor, jadwal, ulasan, harga informatif (jika berlaku), dan CTA permintaan akses.
- Tambahkan artikel informasi dan jadwal kelas live sebagai halaman publik.

### Tahap 3 — Akun dan pendaftaran kursus

- Buat pendaftaran akun, login, dan logout.
- Simpan kata sandi dalam bentuk hash; jangan pernah menyimpan kata sandi mentah.
- Tambahkan sesi login, pembatasan akses berdasarkan peran, dan perlindungan formulir.
- Simpan pendaftaran kursus dan tampilkan kursus pelajar di dashboard.

### Tahap 4 — Tryout dan pengalaman belajar

- Terapkan skema bank hierarkis dan relasi penggunaan ulang soal antarbank.
- Bangun pengelolaan soal dengan DataTables, kategori/subkategori, editor rich text, media gambar, dan pengurutan drag-and-drop.
- Sediakan preset aturan SKD 2026, blueprint sesi dengan kuota kategori dan skor, serta randomisasi soal yang mempertahankan urutan kategori dan snapshot attempt.
- Bangun halaman belajar dengan embed video, materi teks, tautan sumber, dan navigasi modul.
- Simpan status selesai setiap pelajaran dan tampilkan progres kursus.
- Bangun tryout bertimer berbasis blueprint dengan urutan dan kuota kategori, mode urutan manual atau randomisasi, snapshot attempt, bobot per profil aturan, skor, pembahasan, serta ringkasan area lemah.
- Pastikan pelajar hanya dapat membuka materi kursus yang diikutinya.

### Tahap 5 — Panel admin

- Buat alur CRUD untuk kursus, modul, pelajaran, bank soal, dan blueprint sesi.
- Tambahkan status draft/terbit agar materi dan sesi yang belum siap tidak tampil.
- Validasi isian, tautan video, kategori, kuota, bobot penilaian, dan media sebelum disimpan.

### Tahap 6 — Penyelesaian MVP

- Rapikan tampilan desktop dan ponsel, status kosong, pesan kesalahan, dan konfirmasi aksi.
- Perbarui README dengan cara menjalankan aplikasi, akun admin awal, struktur database, dan batasan deployment.
- Siapkan cara membuat cadangan database SQLite.

## Batas keamanan dan operasional

- Semua akses admin dan pelajar harus memeriksa sesi serta hak akses granular di server; menu yang disembunyikan tidak menggantikan otorisasi server.
- Gunakan query SQLite berparameter, validasi data masuk, dan escape teks saat dirender.
- Cookie sesi harus memiliki pengaturan keamanan yang sesuai; token formulir digunakan untuk mencegah permintaan lintas situs.
- Pengembangan lokal tetap dapat memakai server Python bawaan. Sebelum aplikasi dibuka ke internet, tentukan hosting HTTPS, autentikasi admin awal, backup database, dan server aplikasi yang sesuai.
- Pembayaran, sertifikat, forum/komentar, dan unggah video tidak termasuk MVP; tryout berbasis bank soal termasuk.

## Kriteria MVP siap ditinjau

- Pengunjung dapat menemukan program dan paket tryout, memakai filter jalur, dan melihat detail serta kurikulum.
- Pengguna dapat membuat akun, masuk, mendapat akses sesuai status paket, dan melihat programnya di dashboard.
- Pelajar dapat membuka materi, mengerjakan tryout, melihat hasil/pembahasan, menyimpan progres, dan melanjutkan belajar.
- Admin dapat membuat dan mengubah kursus, modul, pelajaran, bank, soal, dan blueprint sesuai permission. Super Admin dapat mengatur menu dan CRUD tiap role; akses langsung ke URL tanpa permission ditolak.
- Soal dapat digunakan lintas bank tanpa duplikasi; sesi manual/acak memenuhi kuota dan aturan skor kategori, dengan hasil historis tetap stabil.
- Data akun, kursus, pendaftaran, dan progres tetap tersimpan setelah server dimulai ulang.
- Konten dari database ditampilkan aman dan halaman utama tetap nyaman digunakan di ponsel.

## Keputusan untuk dikunci sebelum implementasi

1. Konten awal masih perlu ditentukan: judul program, sekolah/jalur, kategori, kurikulum, bank soal, dan video.
2. Mekanisme pembayaran dan penyedia payment gateway diputuskan untuk tahap setelah MVP.
3. Satu akun admin awal dibuat melalui proses setup lokal.
4. Versi aturan selain SKD Kedinasan 2026 perlu ditambahkan setelah sumber resmi masing-masing seleksi diverifikasi.

## Catatan referensi

Struktur halaman publik dan fitur Aster diperkaya dari pengamatan publik terhadap [kedinasan.id](https://kedinasan.id/), [paket bimbel](https://kedinasan.id/product), [contoh detail STIS](https://kedinasan.id/product/polstat-stis), [paket tryout](https://kedinasan.id/product-to), [jadwal kelas](https://kedinasan.id/jadwal-zoom), [alat cek sekolah](https://kedinasan.id/cek-sekdin), dan [artikel](https://kedinasan.id/blogs). Ringkasan bukti ada di [kedinasan-public-recon.md](kedinasan-public-recon.md), dan pertanyaan riset pengguna ada di [ux-research-plan.md](ux-research-plan.md). RES dipakai sebatas public recon; area login belum dipetakan.
