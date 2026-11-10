# Spesifikasi UX — Super Admin “Akses & Role”

**Status:** spesifikasi UI/UX untuk implementasi; mengikuti addendum RBAC di `outputs/plan.md`.
**Cakupan:** halaman pengaturan hak akses untuk empat role inti Aster Academy. Dokumen ini tidak mengubah perilaku aplikasi atau skema database.

## 1. Tujuan dan prinsip

Super Admin dapat memahami dan mengubah menu serta aksi yang diizinkan bagi Admin, Teacher / Mentor, dan Student / Mentee. Perubahan harus mudah ditinjau, tidak mengejutkan pengguna yang sedang bekerja, serta menjelaskan perbedaan izin eksplisit, izin efektif, dan pembatasan lingkup data.

- Otorisasi berlaku di server untuk navigasi, URL, dan setiap aksi tulis. Menyembunyikan menu saja bukan kontrol akses.
- **Deny-by-default:** izin yang tidak tercatat, modul baru, aksi baru, role yang tidak dikenal, atau data tanpa scope eksplisit ditolak. UI menampilkan “Tidak diberikan”; bukan menganggap akses tersedia.
- Role inti tidak saling mewarisi hak. Tidak ada implikasi “Admin mewarisi Super Admin” atau “Teacher mewarisi Admin”. Hak efektif adalah hak yang secara eksplisit diberikan ke role itu, setelah batas scope dan aturan sistem diterapkan.
- Hanya Super Admin dapat membuka dan menyimpan matriks. Super Admin sistem memiliki bypass pemulihan yang dilindungi dan tidak dapat diubah dari matriks.
- Hak diberikan sesempit yang diperlukan; hak destruktif dan aksi khusus tidak otomatis ikut bersama `view`, `create`, `update`, atau `delete`.
- Bahasa antarmuka Indonesia. Role tetap ditulis dengan nama inti di atas agar konsisten dengan plan.

## 2. Struktur halaman

### 2.1 Shell dan navigasi

Gunakan shell admin Aster saat ini: sidebar putih lebar sekitar 264 px, konten utama berlatar biru-keabu-abuan muda, garis pemisah tipis, judul biru navy, aksen biru Aster, panel putih beradius sekitar 16–20 px, dan bayangan tipis. Pertahankan topbar “Administrasi Aster Academy”, batas lebar konten, footer, dan perilaku responsifnya.

Di grup sidebar **RUANG PENGELOLA**, tambahkan tautan **Akses & Role** dengan ikon sederhana dan status aktif (`aria-current="page"`). Tempatkan dekat Ikhtisar/Profil sebagai fungsi administrasi global, bukan di dalam Bank Soal. Hanya Super Admin melihat tautan ini. Di topbar atau tepat di bawah judul, tampilkan breadcrumb `Ikhtisar / Akses & Role` dan label status sesi `Super Admin`.

### 2.2 Header halaman

- Kicker: `PENGATURAN AKSES`.
- H1: `Akses & Role`.
- Deskripsi: `Tentukan menu dan tindakan yang tersedia untuk setiap role.`
- Bantuan singkat: `Perubahan berlaku untuk semua pengguna dengan role tersebut setelah disimpan.`
- Badge ringkasan: jumlah role inti, jumlah menu/area yang dikonfigurasi, serta jumlah perubahan belum disimpan. Jangan tampilkan KPI dekoratif.
- Tautan sekunder `Pelajari matriks izin` membuka bagian penjelasan inline, bukan memindahkan ke halaman lain.

### 2.3 Pemilih role

Tampilkan empat tab/pilihan role sebagai panel ringkas, bukan kartu dashboard besar:

1. **Super Admin** — badge `Dilindungi sistem`; tab dapat dibuka untuk melihat hak efektif tetapi kontrol edit nonaktif.
2. **Admin** — deskripsi “Operasional akademi sesuai izin”.
3. **Teacher / Mentor** — deskripsi “Mengajar dan mengelola kegiatan belajar yang ditugaskan”.
4. **Student / Mentee** — deskripsi “Belajar dan mengelola progres milik sendiri”.

Setiap tab menyebut jumlah izin yang aktif, mis. `8 dari 14 area`, dan menandai perubahan belum disimpan. Gunakan elemen tab semantik (`tablist`, `tab`, `tabpanel`) bila hanya satu role terlihat per waktu. Jika memilih tampilan perbandingan semua role, gunakan tombol radio/segmented control yang jelas dan jangan menyamarkan tabel menjadi tab.

### 2.4 Ringkasan role terpilih

Sebelum matriks, tampilkan panel ringkas berisi nama role, deskripsi, jumlah akun dengan role tersebut (bila tersedia), cakupan data standar, dan status konfigurasi. Untuk Admin/Teacher/Student jelaskan bahwa hak berlaku pada semua pengguna role itu. Jangan tampilkan identitas pengguna jika tidak relevan.

### 2.5 Matriks izin

Desktop memakai tabel berheader sticky dan label aksi tetap terlihat. Kolom kiri berisi nama area/menu serta keterangan scope. Kelompokkan kolom aksi:

- **Lihat** (`view`)
- **Buat** (`create`)
- **Ubah** (`update`)
- **Hapus** (`delete`)
- **Aksi khusus** (label per aksi, misalnya `Terbitkan`, `Setujui akses`, `Kelola role`)

Satu baris per area/objek, bukan satu baris per URL. Area dikelompokkan: Akademi, Tryout, Pengguna & akses, Konten, Pengaturan. Nama aksi khusus ditampilkan sebagai kolom tersendiri atau menu `Aksi khusus` yang dapat diperluas; kontrol tetap memiliki label yang bisa dibaca pembaca layar. Tidak boleh menggabungkan `Hapus` dengan `Ubah`.

Setiap sel berupa checkbox/native button yang dapat difokuskan, dilabeli lengkap (contoh: `Izinkan Admin mengubah Program`), dan memiliki tiga tampilan:

- `Diberikan` — centang biru Aster.
- `Tidak diberikan` — tidak dicentang.
- `Dibatasi sistem` — terkunci, bukan toggle; tooltip/teks pendamping menjelaskan alasan.

Jangan memakai warna sebagai satu-satunya tanda. Tampilkan teks atau ikon dengan nama aksesibel. Jika `view` tidak aktif, kontrol create/update/delete dan aksi khusus area tersebut dinonaktifkan, nilainya tetap terlihat dan tidak otomatis dibuang. Beri keterangan: `Aksi ini tidak efektif sampai izin Lihat diberikan.` Jika toggle `view` dimatikan dan ada hak turunan aktif, konfirmasi bahwa hak tersebut tetap tersimpan sebagai konfigurasi namun menjadi tidak efektif; rekomendasi aman adalah menonaktifkan hak turunan bersama-sama setelah konfirmasi eksplisit. Implementasi harus memilih satu perilaku konsisten; spesifikasi ini menetapkan **hak turunan dipertahankan tetapi nonaktif secara efektif**, supaya perubahan `view` tidak menghapus konfigurasi tanpa sengaja.

Tabel panjang harus menyediakan pencarian nama menu/aksi, filter `Semua area` / grup, tombol `Buka semua grup` dan `Tutup semua grup`, serta legenda. Pencarian tidak mengubah hak dan tidak menyimpan otomatis. Tampilkan hasil pencarian kosong dengan tombol `Hapus pencarian`.

### 2.6 Sticky action bar

Saat ada perubahan lokal, tampilkan bar tindakan menempel di bawah viewport (di atas konten, tidak menutupi fokus):

- `Ada perubahan yang belum disimpan` dan jumlah perubahan.
- Tombol primer `Simpan perubahan`.
- Tombol sekunder `Batalkan perubahan`.
- Tautan ringkas `Tinjau perubahan` yang membuka ringkasan diff.

Saat tidak ada perubahan, action bar disembunyikan atau menampilkan status `Semua perubahan tersimpan` tanpa mengganggu isi matriks. Saat menyimpan, tombol nonaktif dan teks berubah `Menyimpan…`; cegah submit ganda.

### 2.7 Riwayat perubahan (opsional jika data tersedia)

Di bawah matriks, tampilkan panel sederhana `Perubahan terakhir`: waktu, Super Admin pelaku, role sasaran, jumlah izin yang diubah, dan tautan `Lihat rincian`. Ini informasional; jangan menampilkan perubahan yang tidak bisa diverifikasi. Jika belum ada data, tampilkan empty state ringan.

## 3. Matriks izin awal

Matriks berikut adalah **preset least-privilege yang disarankan**, bukan sumber kebenaran di browser. Sel `—` berarti izin tidak diberikan secara default. Nilai harus dikonfirmasi terhadap modul yang benar-benar ada saat implementasi; aksi untuk fitur yang belum dibuat dapat disiapkan sebagai kategori masa depan, tetapi tidak membuat akses fiktif.

Singkatan: `V` lihat, `C` buat, `U` ubah, `D` hapus. Aksi khusus ditulis lengkap. Scope yang bukan global harus ditegakkan pada setiap query/aksi server.

| Area/menu (permission key contoh) | Super Admin | Admin | Teacher / Mentor | Student / Mentee |
|---|---|---|---|---|
| Ikhtisar (`dashboard`) | Semua | V | V (ringkasan yang ditugaskan) | V (dashboard sendiri) |
| Program (`courses`) | Semua | V/C/U/D; `publish` | V; U hanya program yang ditugaskan bila fitur mengajar mengizinkan | V program yang tersedia/diikuti; tanpa CRUD |
| Modul & pelajaran (`curriculum`) | Semua | V/C/U/D; `publish` | V/C/U; hanya kursus yang ditugaskan; D — default | V materi dengan akses; tanpa CRUD |
| Permintaan akses (`access_requests`) | Semua | V/U; `approve_access`, `reject_access` | — | C permintaan sendiri; V status sendiri |
| Pengguna/pelajar (`users`) | Semua | V/C/U terbatas ke data akademik; D — default; `assign_access` sesuai kebutuhan | V daftar peserta yang ditugaskan; U progres/catatan pengajaran hanya jika ada modul tersebut | V/U profil sendiri; tidak dapat melihat akun lain |
| Bank soal (`question_banks`) | Semua | V/C/U/D sesuai batas riwayat; `publish` | V/C/U pada bank/soal yang ditugaskan; D — default | — |
| Blueprint & sesi ujian (`exam_blueprints`) | Semua | V/C/U/D; `publish`, `start_session` bila relevan | V/C/U blueprint yang ditugaskan jika diizinkan; D — default | V sesi tersedia; `start_attempt` hanya untuk peserta yang berhak |
| Hasil & attempt (`attempts`) | Semua | V laporan; U/D — | V hasil peserta di kelas yang ditugaskan hanya bila kebijakan mengizinkan | V hasil dan pembahasan milik sendiri setelah dibuka |
| Jadwal kelas live (`live_sessions`) | Semua | V/C/U/D; `publish` | V/C/U sesi yang ditugaskan; D — default | V sesi yang tersedia/diikuti |
| Artikel (`articles`) | Semua | V/C/U/D; `publish` | V; C/U hanya jika diberi tugas editorial; D — | V artikel terbit |
| Pengaturan akun / profil (`profile`) | Semua | V/U profil sendiri | V/U profil sendiri | V/U profil sendiri |
| Akses & Role (`role_permissions`) | Lihat penuh; bypass sistem; matriks read-only | — | — | — |
| Sesi / logout (`session`) | `logout` | `logout` | `logout` | `logout` |

### 3.1 Tafsir “Semua” Super Admin dan batas sistem

“Semua” pada tabel adalah hak efektif penuh untuk menu dan aksi aplikasi yang dikenal, **kecuali batas proteksi berikut**:

- Tidak ada kontrol untuk menghapus/menonaktifkan role Super Admin sistem, mengganti `role_permissions` milik Super Admin, mencabut bypass, atau menurunkan role akun Super Admin yang sedang aktif.
- Konfigurasi role Super Admin selalu tampak `Dibatasi sistem`/`Dilindungi sistem`; tidak dapat di-toggle, dihapus, atau diedit melalui UI ini.
- Minimal satu akun Super Admin aktif harus tetap ada. Perubahan yang berpotensi menghilangkan seluruh Super Admin ditolak. Pengelolaan penetapan role Super Admin, bila kelak dibutuhkan, adalah alur terpisah dengan audit dan verifikasi ekstra; jangan menambahkannya sebagai checkbox permission biasa.
- Super Admin tetap tunduk pada validasi bisnis/integritas data (mis. hasil attempt historis tidak boleh rusak karena penghapusan soal). Bypass otorisasi bukan bypass konsistensi data.
- Admin, Teacher, dan Student tidak dapat mengubah permission atau role pengguna kecuali ada aksi khusus eksplisit dan endpoint yang bersesuaian. Preset awal tidak memberikan `manage_roles` kepada selain Super Admin.

### 3.2 Izin efektif, scope, dan indikator

Tidak ada inheritance antar-role pada model inti. UI menampilkan untuk setiap role:

- **Izin role:** nilai yang tersimpan secara eksplisit di matriks.
- **Efektif:** izin role setelah cek dependensi (mis. aksi membutuhkan `view`), scope data, serta proteksi sistem diterapkan.
- **Sumber/batas:** badge `Role`, `Scope: kursus yang ditugaskan`, `Data milik sendiri`, atau `Dilindungi sistem`.

Role dapat memiliki `U` tanpa `V` tersimpan, tetapi `U` tidak efektif dan UI menjelaskannya. Data milik sendiri/kelas yang ditugaskan adalah batas cakupan, bukan hak tambahan yang memberi akses pada data lain. Jangan menyebut hak dari label “Admin” atau “Teacher”; hak berasal dari matriks dan scope eksplisit.

## 4. Alur interaksi dan penyimpanan

1. Super Admin membuka **Akses & Role**. Server memeriksa sesi dan permission sistem. Pengguna tanpa izin ditolak; antarmuka tidak sekadar menyembunyikan tautan.
2. Halaman memuat snapshot izin aktif dan penanda versi/terakhir diperbarui. Jika gagal dimuat, tampilkan error dan jangan merender kontrol seolah-olah semua akses ditolak atau diizinkan.
3. Super Admin memilih role non-protected, mencari area, memperluas grup, dan mengubah checkbox. Perubahan hanya lokal (staged); belum berlaku ke pengguna.
4. Toggle izin aksi saat `view` tidak diberikan tetap tersimpan, namun nonaktif efektif; jelaskan keadaan tersebut. Jika antarmuka memilih auto-clear sebagai opsi implementasi, itu bertentangan dengan spesifikasi ini kecuali mengonfirmasi dan mencantumkan seluruh izin yang akan dihapus.
5. `Tinjau perubahan` menampilkan diff: role, izin yang ditambah/dihapus, jumlah, dan efek khusus (contoh: `Menghapus Lihat Program membuat Buat/Ubah Program tidak efektif`). Tidak mengubah data.
6. `Simpan perubahan` membuka dialog konfirmasi bila perubahan memengaruhi akses (selalu untuk save role). Dialog menyatakan role sasaran, ringkasan tambah/cabut, dampak berlaku untuk semua akun role, dan waktu efektif. Tombol: `Kembali meninjau` (default fokus) dan `Konfirmasi & simpan` (tindakan jelas). Jangan memakai confirmshaming.
7. Submit menyertakan versi konfigurasi terakhir. Server memvalidasi ulang pelaku Super Admin, role yang boleh diubah, permission key yang dikenal, dependensi, dan guard self-lockout; simpan seluruh perubahan role dalam satu transaksi.
8. Bila versi sudah berubah oleh sesi admin lain, tolak overwrite, tampilkan `Izin diperbarui oleh Super Admin lain. Muat ulang untuk melihat perubahan terbaru.` Beri tombol `Muat ulang`; jangan merge diam-diam.
9. Jika berhasil, simpan dan terapkan hak baru pada pemeriksaan request berikutnya. Tampilkan status sukses dan diff singkat; jangan memaksa logout semua pengguna tanpa kebijakan sesi yang jelas. Data request berikutnya harus memakai permission baru.
10. Jika dibatalkan, kembali ke matriks tanpa mengubah konfigurasi server. Jika ada staged changes, `Batalkan perubahan` atau navigasi keluar memicu dialog `Buang perubahan yang belum disimpan?` dengan pilihan `Lanjut mengedit` dan `Buang perubahan`.

### Pencegahan mengunci diri sendiri

- UI tidak menawarkan perubahan permission untuk role Super Admin sistem.
- Server menolak POST yang mengubah role/permission Super Admin, walaupun request dipalsukan.
- Server menolak perubahan yang menurunkan/menghilangkan hak Super Admin sesi aktif atau menghapus satu-satunya Super Admin aktif.
- Karena permission matrix hanya dapat diubah oleh Super Admin dan perubahan diarahkan ke role lain, simpan perubahan role Admin/Teacher/Student tidak memengaruhi hak pelaku Super Admin. Jika nanti pengelolaan penetapan role ditambahkan, lakukan di layar/alur terpisah dan lakukan pemeriksaan “masih ada Super Admin aktif” dalam transaksi yang sama.
- Saat guard menolak, tampilkan alasan secara spesifik dan pertahankan draft lokal untuk diperbaiki; jangan menyimpan sebagian.

## 5. Empty, error, loading, dan success states

### Loading

- Skeleton sederhana untuk header role dan baris matriks; warna latar putih/biru muda tema admin.
- Teks status aksesibel `Memuat pengaturan izin…` (`role="status"`, `aria-live="polite"`).
- Jangan menampilkan checkbox aktif default sebelum payload konfigurasi berhasil diterima.

### Belum ada konfigurasi / role

- Bila role inti belum memiliki konfigurasi: panel `Izin role belum dikonfigurasi` dengan deskripsi deny-by-default dan tindakan `Terapkan preset aman`.
- Menerapkan preset adalah perubahan staged; wajib melalui review dan konfirmasi yang sama dengan penyimpanan.
- Role inti selalu terlihat; jika data role hilang, jangan menyimpulkan izin dari nama role. Tampilkan error setup dan jangan izinkan penyimpanan parsial.
- Grup matriks tanpa item: `Belum ada menu pada area ini.` Ini bukan error dan tidak menambah hak.

### Hasil pencarian kosong

`Tidak ada menu atau aksi yang cocok.` Tombol `Hapus pencarian` mengembalikan seluruh baris tanpa mengubah checkbox.

### Error muat/simpan

- **Tidak berwenang:** `Halaman ini hanya dapat dikelola Super Admin.` Tautan kembali ke Ikhtisar; response server tetap 403.
- **Sesi habis:** `Sesi Anda berakhir. Masuk kembali untuk melanjutkan.` Draft lokal jangan dikirim otomatis setelah login baru.
- **Jaringan/server:** `Perubahan belum tersimpan. Coba lagi.` Pertahankan draft di halaman selama sesi hidup; tombol ulangi hanya mengirim setelah memeriksa versi terbaru.
- **Konflik versi:** tampilkan versi yang berubah dan tombol `Muat ulang`; sediakan opsi menyalin diff lokal secara tekstual jika memungkinkan, jangan merge diam-diam.
- **Permission key/role tidak valid:** `Ada izin yang tidak dikenali. Tidak ada perubahan yang disimpan.` Laporkan kode/area untuk diagnosa tanpa membuka detail sensitif.
- **Self-lockout/proteksi Super Admin:** jelaskan izin/aksi yang ditolak dan pertahankan draft. Semua perubahan transaksi gagal bersama-sama.
- Error ditempatkan sebelum matriks atau di dekat kontrol yang relevan; beri `role="alert"`, teks jelas, dan jangan hanya memberi toast sesaat.

### Sukses

- Banner hijau lembut `Izin untuk [role] berhasil disimpan.` dengan ringkasan seperti `3 izin diberikan · 1 izin dicabut` dan waktu simpan.
- Gunakan `role="status"` / `aria-live="polite"`; fokus tidak dipindahkan secara tiba-tiba.
- Bersihkan dirty state hanya setelah server mengonfirmasi sukses dan perbarui versi/snapshot lokal.
- Jika tidak ada perubahan, tombol simpan nonaktif dan helper `Tidak ada perubahan untuk disimpan.`

### Riwayat kosong

`Belum ada perubahan izin.` Beri keterangan perubahan pertama akan tampil setelah konfigurasi disimpan.

## 6. Keyboard dan aksesibilitas

- Semua kontrol dapat dijalankan dengan keyboard; urutan fokus mengikuti header → pemilih role → filter → matriks dari atas ke bawah → action bar.
- Tab role mengikuti pola WAI-ARIA: panah kiri/kanan memindahkan tab, `Home`/`End` ke tab pertama/terakhir, `Tab` masuk ke panel.
- Checkbox native: `Space` mengubah nilai. Bila memakai kontrol khusus, dukung `Space`/`Enter`, `role="checkbox"`, `aria-checked`, dan label yang mencakup role + area + aksi.
- Header tabel menggunakan `<th scope="col">`; kategori baris memakai header baris/heading yang berasosiasi dengan kontrol. Hindari tabel matriks yang kehilangan hubungan sel saat layar kecil.
- Kontras teks normal sekurangnya WCAG AA. Fokus keyboard terlihat jelas dengan outline biru terang; jangan menghapus outline.
- Dialog konfirmasi memiliki judul terhubung (`aria-labelledby`), deskripsi (`aria-describedby`), fokus awal pada tombol aman `Kembali meninjau`, trap fokus, `Escape` untuk kembali tanpa menyimpan, dan fokus dikembalikan ke tombol pemicu.
- Gunakan teks dan ikon selain warna untuk status diberikan, tidak diberikan, error, dan sukses. Sentuh minimal 44×44 px untuk target pada layar sentuh.
- Status loading/sukses diumumkan tanpa memindahkan fokus. Error validasi ditautkan ke kontrol dengan `aria-describedby` dan `aria-invalid`.
- Perubahan role yang dipilih dan jumlah staged changes tersedia sebagai teks, bukan hanya tab berwarna/badge visual.
- Hormati `prefers-reduced-motion`; jangan gunakan animasi untuk menandai bahwa izin berubah.

## 7. Responsive layout

### Lebar desktop (>1040 px)

- Sidebar tetap 264 px dan sticky sesuai shell admin; konten matriks mengisi lebar hingga batas konten sekitar 1440 px.
- Tabel memiliki header kolom sticky di dalam area scroll; kolom area/menu tetap di sisi kiri jika tidak mengganggu pembaca layar.
- Action bar sticky di viewport bawah, sejajar konten utama dan tidak menutupi footer/fokus.

### Tablet (601–1040 px)

- Ikuti pola template Aster saat ini: sidebar berubah menjadi navigasi atas yang membungkus baris, konten satu kolom.
- Pemilih role boleh menjadi tab scroll horizontal dengan indikator fokus; pastikan tab aktif terlihat dan dapat dicapai keyboard.
- Matriks mendapat area scroll horizontal yang diberi label “Geser tabel izin secara horizontal”; kolom menu tetap terlihat jika implementasi mendukung tanpa merusak urutan baca.
- Bar tindakan melebar di area konten; tombol tetap mudah disentuh.

### Ponsel (≤600 px)

- Padding konten 16 px, panel putih tidak melebar melewati viewport, sidebar tetap memakai navigasi bungkus Aster tanpa overflow tersembunyi.
- Role selector dapat menjadi daftar tombol/tab horizontal yang dapat digulir. Jangan menyusutkan nama role menjadi singkatan yang tidak dapat dipahami.
- Matriks tidak dipaksa menjadi tabel micro-font. Prefer tiap area sebagai panel bertumpuk: nama area + scope, lalu kontrol aksi sebagai grid 2 kolom berlabel penuh. Alternatif tabel horizontal harus memberi petunjuk scroll, fokus keyboard, dan header tetap terasosiasi.
- Tombol simpan dan batal menjadi dua tombol lebar, berurutan, dengan `Simpan perubahan` tetap primer. Konfirmasi memakai dialog hampir selebar viewport dengan margin 16 px dan tombol bertumpuk.
- Pencarian dan filter memenuhi lebar; ringkasan diff dapat dibuka/ditutup per grup.

## 8. Catatan penyelarasan dengan sidebar admin Aster

Template admin saat ini mengulang sidebar serupa di `admin_dashboard.html`, `admin_course_form.html`, `admin_module_form.html`, `admin_lesson_form.html`, `admin_question_bank.html`, `admin_question_set_form.html`, `admin_question_list.html`, `admin_question_form.html`, dan `admin_profile.html`. Pola aktualnya mencakup brand mark A biru gradien, label `RUANG PENGELOLA`, menu Ikhtisar/Program/Permintaan akses/Tambah program/Bank Soal/Profil, tautan Lihat situs, dan logout. Layout desktop memakai kolom sidebar 264 px; pada ≤1040 px sidebar menjadi navigasi atas dan footer/sidebar bawah disembunyikan.

Untuk penyelarasan implementasi:

- Tambahkan **Akses & Role** secara konsisten di semua shell admin, tetapi render hanya untuk Super Admin yang terotorisasi. Penentuan visibilitas dari server; tidak cukup CSS/JS.
- Gunakan kelas aktif yang sama (`is-active`) dan atribut `aria-current="page"`; jangan hardcode posisi profil aktif ketika role/menu berubah.
- Tambahkan group label terpisah jika menu global seperti Akses & Role bertambah, tetapi jaga panjang navigasi mobile; pada layar kecil sediakan wrapping/scroll yang tetap dapat diakses.
- Pertahankan warna navy `#142644`/`#15345d`, teks sekunder `#52657f`/`#64748b`, garis `#dce6f2`/`#e2eaf4`, latar `#f4f7fc`/`#f6f8fc`, aksen `#1d4ed8`/`#2563eb`, kartu putih dan radius 11–20 px yang telah dipakai template.
- Gunakan kembali pola `admin-topbar`, `admin-page`, `panel`, `btn`, `btn-secondary`, `field`, `.notice`, dan footer; buat komponen tabel/matriks baru yang mengadopsi padding header/cell lapang (`px-5 py-4` pada tabel bank soal), bukan sel rapat seperti tabel lama.
- Dashboard dan beberapa form lama masih memiliki utility `glass`/warna sisa desain gelap, walau override admin mengubah shell ke tema terang. Halaman baru harus memakai panel putih solid dengan kontras stabil, bukan efek glass atau teks pucat.
- Pastikan link logout POST, Profil, Lihat situs, dan tata letak logout mobile tetap konsisten; jangan memindahkan logout ke bar aksi permission.
- Sidebar global yang konsisten penting: halaman akses/role tidak boleh tampak seperti aplikasi terpisah dari admin Aster.

## 9. Kriteria review desain

- Super Admin segera melihat role mana yang sedang diedit, izin mana yang aktif, dan perubahan apa yang belum disimpan.
- Tidak ada interaksi yang dapat mengubah hak Super Admin sistem; kontrol proteksi terbaca sebagai terkunci, bukan checkbox mati tanpa penjelasan.
- Perubahan staged tidak berlaku sebelum konfirmasi server sukses.
- Perubahan yang mengurangi akses memperlihatkan dampak dan cakupan semua akun role.
- `view` dan aksi CRUD/spesial dapat dibedakan, scope data terlihat, izin efektif menjelaskan dependensi, dan item tak dikenal ditolak.
- Tabel dapat dikelola lewat keyboard dan layar kecil tanpa mengandalkan warna atau gesture drag.
- Tampilan dan sidebar konsisten dengan tema admin Aster terang, biru, padding lega, panel putih.
