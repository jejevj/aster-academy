# UX Spec — Bank Soal, Kategori, dan Blueprint Tryout

**Tujuan:** membuat pengelolaan soal SKD mudah dipahami dan aman untuk bank bersama, penilaian berbobot, serta sesi tryout. Spesifikasi ini memakai komponen web standar dan dependensi gratis/open-source saja; tidak memerlukan akun layanan desain berbayar. Tidak mencakup OCR.

## Review singkat kondisi saat ini

- Form soal yang ada masih berupa textarea untuk pertanyaan/pembahasan dan input teks untuk opsi. Kategori, editor gambar, dan pengelolaan bank tujuan belum tampak di form.
- Halaman bank menampilkan daftar paket, tetapi alur kategori dan blueprint belum terlihat sebagai bagian navigasi.
- Daftar saat ini belum menunjukkan kontrol DataTables maupun pengurutan soal yang bisa dipahami pengguna.

**Dampak:** pengelola belum bisa memastikan sebuah soal masuk kategori yang tepat, bobotnya sesuai, atau tersedia di bank/blueprint yang akan dipakai. Jadikan alur di bawah target implementasi.

## Struktur navigasi admin

Di dalam **Bank Soal**, gunakan tab/submenu konsisten:

1. **Bank** — hierarki bank dan jumlah soal.
2. **Semua soal** — pencarian, filter, urutan, dan tindakan soal.
3. **Kategori & bobot** — kategori induk TWK/TIU/TKP, subkategori, dan aturan nilai.
4. **Blueprint tryout** — profil aturan, urutan kategori, kuota, randomisasi, dan validasi.

Judul halaman selalu menyebut lokasi aktif, misalnya `Bank Soal / Kategori & bobot`. Tombol utama berada di kanan judul, filter di atas tabel, dan aksi per baris tidak bercampur dengan teks isi.

## 1. Kategori dan bobot

### Alur pengelolaan

- Halaman kategori menampilkan daftar bertingkat dengan kolom **Kategori**, **Kode**, **Kategori induk**, **Bobot/aturan skor**, **Status**, **Jumlah soal**, dan **Aksi**.
- Sediakan preset awal **TWK**, **TIU**, dan **TKP** sebagai kategori induk. Subkategori dapat ditambahkan/diubah oleh pengelola; labelnya ditandai sebagai taksonomi belajar kecuali distribusi resminya memang ditetapkan aturan yang dipilih.
- Form tambah/edit berisi nama, kode unik, induk opsional, status aktif, dan aturan skor. Untuk SKD, tampilkan sumber/tahun profil aturan agar nilai tidak terlihat sebagai ketentuan universal.
- Tampilkan ringkasan aturan 2026 sesuai profil yang tercatat di PLAN: TWK dan TIU benar 5, salah/kosong 0; TKP tiap opsi bernilai 1–5, kosong 0. Tampilkan jumlah dan ambang sebagai atribut profil blueprint, jangan menyamarkannya sebagai bobot kategori.
- Jika kategori sudah dipakai soal/blueprint, nonaktifkan kategori (soft disable) dan jelaskan konsekuensinya. Jangan menghapus atau mengubah hasil attempt lama; skor lama memakai snapshot aturan saat ujian dimulai.

### Form soal

- Pilih kategori wajib dengan dropdown bertingkat `TWK → subkategori`; tampilkan ringkasan bobot setelah pilihan dibuat.
- Jika kategori nonaktif atau sudah dihapus dari pilihan, tampilkan nilai lama sebagai terkunci dan minta pengelola memilih kategori aktif sebelum menyimpan perubahan.
- Validasi menandai field kategori dan bobot dengan pesan spesifik; jangan hanya menampilkan toast umum.

## 2. Daftar soal, bank, dan reuse

### Tabel soal

Gunakan DataTables untuk search, sort, paging, dan filter; pertahankan label kontrol berbahasa Indonesia. Kolom yang disarankan: **Soal (cuplikan)**, **Kategori**, **Bank pemilik**, **Bank lain**, **Status**, **Dipakai di sesi**, **Diperbarui**, **Aksi**. Filter kategori induk/subkategori, bank, status, dan pemakaian. Teks panjang dipotong dengan cuplikan; buka detail untuk melihat isi penuh.

Pengurutan manual bank memakai drag handle yang jelas dan aksi keyboard **Pindah ke atas / Pindah ke bawah** sebagai alternatif. Setelah simpan, beri konfirmasi urutan tersimpan. Jangan menyamakan urutan manual dengan urutan acak pada tryout.

### Kepemilikan dan reuse lintas bank

- Di form buat soal, bank aktif menjadi **Bank pemilik**. Pilihan tambahan diberi label **Masukkan soal ini ke bank lain** dan berbentuk multi-select/checkbox dengan pencarian.
- Di tabel/detail, tunjukkan pemilik dengan label `Pemilik` dan bank lain dengan label `Dipakai di`. Satu soal tetap satu entitas; reuse tidak membuat duplikat.
- Aksi **Keluarkan dari bank ini** menghapus keanggotaan saja. Aksi **Hapus soal permanen** terpisah, hanya untuk pemilik dan jika tidak ada riwayat sesi yang melindungi soal.
- Jika soal telah dipakai attempt, tampilkan status terkunci dan jelaskan bahwa penghapusan dari bank tidak mengubah riwayat; larang penghapusan permanen atau perubahan yang merusak snapshot.

## 3. Editor teks kaya dan gambar

Sediakan editor pada batang soal, setiap opsi, serta pembahasan. Toolbar minimum: tebal, miring, daftar, tautan aman, hapus format, dan sisipkan gambar. Editor dan tombol tetap bisa dipakai dengan keyboard; toolbar memiliki label aksesibel dan fokus terlihat.

- Gambar dapat diunggah atau ditempel ke area editor. Validasi PNG/JPEG/WebP/GIF, maksimum 5 MB, tampilkan progres, pratinjau, ukuran, dan aksi **Ganti / Hapus** sebelum menyimpan.
- Wajibkan teks alternatif untuk gambar informatif; sediakan pilihan “gambar dekoratif” bila relevan. Pesan validasi menyebut jenis/ukuran yang diterima.
- Pratinjau soal merender teks dan gambar seperti tampilan peserta, termasuk gambar di opsi dan pembahasan.
- Jika unggah gagal, pertahankan isi editor dan beri tombol **Coba lagi**. Jika editor gagal dimuat, tampilkan textarea fallback dan peringatan bahwa format kaya tidak tersedia saat ini.
- UI tidak menjanjikan OCR atau konversi otomatis gambar menjadi teks.

## 4. Blueprint tryout: urutan, jumlah, dan randomisasi

### Alur pembuatan

1. Pilih nama blueprint, profil aturan/tahun, durasi, dan bank sumber (satu atau lebih).
2. Tambahkan kategori yang diuji. Tiap baris memiliki drag handle dan kontrol pindah atas/bawah, nama kategori, jumlah soal diminta, jumlah tersedia, bobot/ringkasan nilai, serta sakelar **Acak soal dalam kategori ini**.
3. Urutan baris adalah urutan kategori yang dilihat peserta. Randomisasi hanya mengubah pilihan/urutan soal di dalam kategori tersebut, bukan posisi kategori. Tampilkan opsi global **Acak urutan kategori** terpisah dan mati secara default; bila aktif, beri penjelasan bahwa blueprint tidak lagi mempertahankan urutan kategori yang disusun.
4. Panel ringkasan memperlihatkan total soal, total durasi, jumlah tersedia vs diminta per kategori, aturan skor/ambang, dan kekurangan yang menghalangi publikasi.
5. Simpan sebagai draft kapan saja. **Terbitkan** aktif hanya saat profil aturan lengkap, kategori valid, dan pool tiap kategori mencukupi kuota.

Preset SKD 2026 menampilkan 30 TWK, 35 TIU, 45 TKP (110 total) dan durasi 100 menit dari profil. Kuota tersebut dapat disesuaikan untuk blueprint lain tanpa mengubah preset resmi. Untuk TKP, tampilkan bahwa skor bergantung pada opsi; jangan melakukan shuffle opsi secara default.

Saat peserta memulai sesi, soal terpilih, urutan kategori/soal, versi bobot, dan versi konten disnapshot sekali. Refresh/reopen attempt memakai urutan snapshot sama; jangan mengacak ulang.

## 5. Status kosong, error, dan terkunci

| Kondisi | Tampilan dan tindakan |
|---|---|
| Belum ada bank | Empty state menjelaskan fungsi bank; CTA **Buat bank pertama** jika izin tersedia. |
| Bank kosong | Tampilkan nama bank dan CTA **Tambah soal**; beri tautan **Buat kategori** bila kategori aktif belum ada. |
| Hasil pencarian kosong | “Tidak ada soal yang cocok.” Tawarkan **Hapus filter**; jangan tampilkan sebagai kegagalan sistem. |
| Belum ada kategori aktif | Beri penjelasan bahwa soal belum dapat dikategorikan; CTA tambah kategori hanya jika pengguna punya izin. |
| Jumlah soal kurang dari kuota | Tandai kategori yang kurang, mis. `Tersedia 18 dari 30`; blokir terbitkan, tawarkan **Kelola soal di kategori ini**. |
| Gambar terlalu besar/format salah | Pesan dekat kontrol upload menyebut batas 5 MB atau format PNG/JPEG/WebP/GIF; pertahankan draf. |
| Gagal simpan/unggah | Tampilkan pesan yang bisa ditindaklanjuti, pertahankan input, beri **Coba lagi**. Jangan menghapus draft diam-diam. |
| Soal dipakai attempt | Badge **Dipakai dalam riwayat**; edit/perubahan kategori jelaskan dampak versi; hapus permanen terkunci. |
| Akses menu/aksi ditolak | Halaman 403 menyebut izin yang dibutuhkan secara manusiawi; jangan hanya menyembunyikan tombol sementara URL tetap terbuka. |
| Izin hanya baca | Form tampil sebagai ringkasan read-only dan tombol simpan/ubah tidak tersedia; jelaskan hubungi Super Admin. |
| Randomisasi aktif | Badge **Urutan soal diacak per peserta**; pratinjau admin menunjukkan contoh, bukan urutan pasti attempt. |

## 6. Akses per role dan aksesibilitas

- **Super Admin:** mengelola kategori, bobot, bank, soal, blueprint, dan izin role.
- **Admin:** akses mengikuti izin yang diberikan; tombol dan route/action sama-sama harus menegakkan izin.
- **Teacher / Mentor:** dapat diberi akses lihat/tambah/edit soal dan bank sesuai cakupan; tidak otomatis dapat menerbitkan blueprint atau mengubah aturan.
- **Student / Mentee:** hanya melihat sesi yang tersedia dan mengerjakan attempt; tidak melihat kunci, bobot opsi TKP, atau kontrol admin sebelum attempt selesai sesuai kebijakan pembahasan.

Gunakan kontras teks yang terbaca, label eksplisit, fokus keyboard, tombol sentuh memadai, dan jangan mengandalkan warna saja untuk status. Semua operasi drag-and-drop wajib memiliki padanan kontrol keyboard.

## Kontrak implementasi UX

Nama navigasi dan label yang perlu konsisten: **Bank Soal**, **Kategori & bobot**, **Blueprint tryout**, **Bank pemilik**, **Masukkan soal ini ke bank lain**, **Urutan manual**, **Acak soal dalam kategori ini**, **Tersedia / Diminta**, **Simpan draft**, dan **Terbitkan**. Untuk editor kategori, kontrak dropdown form soal adalah `CATEGORY_OPTIONS`. Fitur gambar menampilkan alt text dan status upload; data kosong/error/locked mengikuti tabel status di atas.

