# Spesifikasi UX — Bank Soal Aster Academy

**Status:** spesifikasi desain dan interaksi; belum diimplementasikan ke aplikasi.
**Cakupan:** kategori dan bobot, bank hierarkis dan reuse, editor teks/gambar, tabel soal, urutan manual, serta blueprint sesi ujian.
**Arah visual:** konsisten dengan admin Aster yang ada: sidebar putih, kanvas biru-abu sangat muda, panel putih ber-radius sedang, aksen biru, tipografi jelas, jarak lapang, dan aksi utama biru. Hindari halaman kosong lebar dan kartu tanpa isi.

## 1. Tujuan dan prinsip UX

Admin perlu dapat mengetahui dengan cepat: soal ini dimiliki bank mana, kategori dan bobotnya apa, di bank lain mana saja soal dipakai, serta apakah soal itu siap dimasukkan ke sesi. Semua operasi berisiko (hapus, cabut penggunaan, terbitkan sesi) harus menjelaskan dampaknya sebelum konfirmasi.

- Tampilkan asal data dan status secara konsisten; reuse tidak membuat salinan soal.
- Pisahkan **kategori materi** dari **kategori penilaian**. Bobot mengikuti profil aturan yang dipilih, bukan nilai hard-coded pada tampilan soal.
- Jangan memberi kesan bahwa subkategori mempunyai kuota resmi jika sumber aturan tidak menetapkannya.
- Simpan urutan kategori blueprint terpisah dari urutan soal di dalam kategori.
- Randomisasi berlaku pada pemilihan soal di dalam kategori dan tidak mengubah urutan kategori yang ditetapkan.
- Aksi dan navigasi mengikuti izin RBAC. Kontrol yang tidak boleh digunakan disembunyikan atau ditampilkan nonaktif dengan alasan yang dapat dipahami; server tetap menjadi otoritas izin.

## 2. Informasi arsitektur dan navigasi

Tambahkan bagian **Bank Soal** di sidebar admin dengan susunan:

1. **Ikhtisar bank** — ringkasan jumlah bank, soal aktif, draft, dan soal yang dipakai sesi.
2. **Bank soal** — daftar bank dan hierarki induk-anak.
3. **Semua soal** — katalog soal lintas bank, dengan filter dan label bank pemilik.
4. **Kategori & bobot** — taksonomi kategori, subkategori, dan aturan skor.
5. **Blueprint ujian** — profil aturan dan konfigurasi sesi.

Pada layar kecil, sidebar mengikuti pola admin Aster yang sudah ada dan menu menjadi baris navigasi yang dapat digeser/di-wrap. Judul halaman, breadcrumb, dan aksi utama tetap terlihat sebelum konten.

### Breadcrumbs

- Ikhtisar bank → Bank soal → `{Nama bank}` → `{Nomor/judul soal}`
- Ikhtisar bank → Kategori & bobot → `{Profil aturan}`
- Ikhtisar bank → Blueprint ujian → `{Nama blueprint}`

Setiap halaman detail menyediakan breadcrumb kembali dan tombol sekunder yang jelas. Jangan mengandalkan tombol browser untuk memahami konteks hirarki.

## 3. Halaman Ikhtisar Bank

Header berisi judul **Bank Soal**, deskripsi singkat, dan tombol **Buat bank**. Di bawahnya gunakan ringkasan padat (bank aktif, soal aktif, draft, dipakai sesi), kemudian tab **Bank** dan **Soal**.

### Tab Bank

DataTables menampilkan nama bank, induk, jumlah anggota soal, status, terakhir diperbarui, dan aksi. Bank induk dapat diperluas untuk menampilkan anak; gunakan indentasi dan ikon disclosure yang berlabel aksesibel. Tampilkan hierarki melalui breadcrumb saat pengguna masuk ke bank anak.

Form buat/edit bank memuat:

- Nama bank (wajib), deskripsi, status.
- Bank induk (opsional; pilih dari daftar, tidak boleh memilih dirinya atau turunannya).
- Ringkasan bank turunan dan jumlah soal.
- Aksi simpan dan batal.

Penghapusan bank harus menjelaskan bahwa menghapus bank tidak menghapus soal pemilik maupun penggunaan di bank lain. Jika bank masih dipakai blueprint, jelaskan relasinya dan minta pengguna menyelesaikan relasi tersebut terlebih dahulu.

### Tab Soal

DataTables dengan pencarian dan filter: bank yang dilihat, bank pemilik, kategori, subkategori, status, tingkat kesulitan, serta status penggunaan. Kolom awal: nomor/judul soal, cuplikan stem, kategori, kesulitan, pemilik, penggunaan lintas bank, status, aksi. Kolom tidak penting dapat dipindahkan ke detail responsif pada layar sempit.

Tombol **Tambah soal** membuka form dengan konteks bank aktif yang telah dipilih. Aksi setiap baris: lihat, edit, masukkan ke bank lain (bila tidak ada di bank tujuan), dan lepas dari bank ini (untuk anggota reuse). Hapus permanen hanya tersedia untuk bank pemilik dan hanya jika aman dari riwayat sesi.

## 4. Kategori, subkategori, dan bobot

Halaman **Kategori & bobot** diawali pemilih **Profil aturan** dan periode berlaku. Sertakan badge status (draft/aktif/arsip), tahun, sumber aturan, tanggal berlaku, serta tautan sumber yang tersimpan. Perubahan pada profil aktif harus membuat versi baru atau meminta konfirmasi eksplisit; jangan diam-diam mengubah hasil sesi lama.

### Taksonomi awal

- Materi induk SKD: **TWK**, **TIU**, **TKP**.
- Setiap materi memiliki subkategori/topik yang dapat dikelola. Label subkategori awal mengikuti kisi-kisi sumber yang berlaku; jumlah dan penamaan persisnya dikonfirmasi terhadap dokumen resmi sebelum publikasi.
- Admin dapat menambah subkategori pembelajaran dan menandainya **Topik internal** agar tidak disalahartikan sebagai pembagian kuota resmi.
- Profil non-SKD dapat memiliki kategori tersendiri, tanpa dipaksa mengikuti struktur TWK/TIU/TKP.

### Tampilan dan aksi

Gunakan tabel hierarkis dengan kolom kategori, subkategori, aturan skor, bobot/konfigurasi, profil, status, dan aksi. Baris induk TWK/TIU/TKP dapat diperluas. Tombol **Tambah kategori**, **Tambah subkategori**, **Atur bobot**, dan **Riwayat versi** diletakkan pada header/toolbar kontekstual.

Form kategori/subkategori memuat nama, kode stabil, induk, deskripsi, urutan, status aktif, dan penanda resmi/internal. Konfirmasi pengarsipan menampilkan jumlah soal terkait dan dampak terhadap blueprint.

### Panel aturan skor

Pilih profil dan kategori dahulu, lalu tampilkan rule dalam bahasa operasional:

| Profil SKD 2026 (nilai awal yang direncanakan) | Jumlah sesi | Skor tiap respons | Maksimum | Ambang umum |
|---|---:|---|---:|---:|
| TWK | 30 | Benar 5; salah/kosong 0 | 150 | 65 |
| TIU | 35 | Benar 5; salah/kosong 0 | 175 | 80 |
| TKP | 45 | Opsi bernilai 1–5; kosong 0 | 225 | 156 |

Tampilkan total 110 butir, 100 menit, maksimum 550, dan ambang tiap kategori di ringkasan profil. Profil afirmasi disajikan sebagai profil terpisah (rencana nilai awal: total minimal 281 dan TIU minimal 55), bukan toggle yang mengubah nilai peserta secara tak terlihat. Cantumkan label **Perlu verifikasi sumber resmi** sampai admin memeriksa dan mengaktifkan versi aturan. Aturan dapat berbeda untuk tahun atau seleksi lain.

Untuk TKP, editor bobot menampilkan daftar opsi dan skor tiap opsi; jangan gunakan satu pilihan “jawaban benar” yang menyembunyikan bobot bertingkat. Jelaskan bahwa mengacak urutan opsi tidak menjadi default karena skor melekat pada opsi.

## 5. Form buat/edit soal

Gunakan halaman berfokus satu kolom utama (lebar nyaman baca sekitar 880–1040 px) dan panel samping **Ringkasan & status** pada desktop. Di ponsel panel menjadi bagian di bawah form. Pertahankan padding yang konsisten, label selalu tampak, dan tiap kelompok field dipisah dengan heading serta jarak; hindari form panjang yang terasa seperti satu blok.

### Bagian A — Identitas dan klasifikasi

- Bank pemilik (wajib saat membuat soal; ditampilkan terkunci atau dapat diubah dengan peringatan saat edit).
- Kategori induk dan subkategori (dependent selects, wajib; topik internal diberi label).
- Tingkat kesulitan, kode/label internal opsional, status draft/siap ditinjau/terbit.
- **Masukkan soal ini ke bank…** multi-select bank. Pilihan pertama harus menyediakan pencarian, hierarki bank, dan jumlah soal. Bank pemilik tidak diulang sebagai target reuse. Bank tempat soal sudah terdaftar ditampilkan terpilih dan dapat dilepas sesuai izin.
- Keterangan bantuan: “Soal yang digunakan ulang tetap satu soal. Perubahan soal akan terlihat di semua bank yang menggunakannya.”

### Bagian B — Stem soal

Gunakan editor rich text Quill dengan toolbar terbatas: paragraf, heading sederhana bila diperlukan, bold, italic, underline, daftar bernomor/bullet, sub/superscript, tautan aman, serta sisipkan gambar. Teks soal mempunyai label jelas **Pertanyaan** dan penghitung karakter opsional. Tampilkan preview hasil render.

Unggah gambar melalui tombol, drag ke area editor, atau paste clipboard. Setiap gambar meminta teks alternatif; beri kontrol pratinjau, ganti, dan hapus. Tampilkan format/ukuran yang diterima sesuai konfigurasi aplikasi dan ukuran berkas saat ini. Progres unggah, kegagalan, dan coba lagi harus terlihat tanpa menghilangkan teks yang sedang ditulis.

### Bagian C — Opsi dan skor

Setiap opsi memakai label tetap (A, B, C, D, dst. sesuai format yang dipilih) dan editor ringkas yang mendukung teks serta gambar. Aksi tambah/hapus opsi terpisah dan punya label aksesibel. Untuk TWK/TIU, tandai satu kunci jawaban; untuk TKP, isi skor tiap opsi dan tandai opsi kosong sebagai 0 pada profil yang berlaku. Tampilkan validasi dekat opsi yang bermasalah, tidak hanya toast.

Urutan opsi tidak diacak saat edit. Jika produk nantinya menyediakan pengacakan di sesi, antarmuka harus memperingatkan konsekuensi untuk bobot TKP dan meminta pemetaan skor tetap pada isi opsi.

### Bagian D — Pembahasan

Editor Quill serupa, dengan area gambar dan preview. Label: **Pembahasan**. Pembahasan dapat disimpan sebagai draft sebelum siap publikasi, tetapi tidak boleh muncul kepada peserta sebelum aturan sesi mengizinkan pembahasan.

### Panel Ringkasan & status

Selalu tampilkan bank pemilik, bank penggunaan, kategori, subkategori, profil bobot, jumlah opsi tervalidasi, gambar terpasang, dan status. Tombol utama **Simpan draft** dan **Simpan & tandai siap**; tombol terbitkan hanya bila pengguna berizin dan seluruh validasi wajib lolos. Autosave dapat menjadi peningkatan berikutnya; sebelum tersedia, beri peringatan perubahan belum disimpan saat keluar.

## 6. Rich text, gambar, dan status editor

**Pilihan gratis/open-source yang direkomendasikan:** Quill (lisensi BSD-3-Clause) untuk editor, dengan toolbar yang disederhanakan sesuai kebutuhan soal. Gunakan kontrol gambar buatan aplikasi untuk unggah/paste agar gambar tersimpan melalui alur media Aster; jangan mengandalkan base64 besar tertanam dalam HTML. Distribusi dapat memakai aset lokal terpin atau CDN yang versinya dipatok. Untuk penerapan offline/mandiri, vendorkan aset lokal dan sertakan lisensi.

Untuk tabel, gunakan DataTables core, Responsive, dan RowReorder dari ekstensi open-source MIT. Hindari DataTables Editor dan komponen DataTables Plus berbayar; edit dilakukan lewat halaman/form Aster sendiri. Referensi lisensi dan kemampuan resmi: [Quill](https://github.com/slab/quill), [lisensi DataTables](https://datatables.net/license/), [Responsive](https://datatables.net/manual/extensions/responsive/), [RowReorder](https://datatables.net/manual/extensions/rowreorder/).

Perilaku status editor/media:

- **Memuat editor:** placeholder netral dan status “Menyiapkan editor…”.
- **Editor gagal dimuat:** pesan jelas, pertahankan nilai form jika memungkinkan, sediakan input teks fallback dan tombol coba lagi. Jangan tampilkan editor kosong seolah konten hilang.
- **Gambar sedang diunggah:** indikator progres dan nama berkas; cegah submit sampai unggahan selesai atau dibatalkan.
- **Gambar gagal:** tunjukkan alasan sederhana dan tombol coba lagi/hapus; jangan menghapus gambar lain atau teks.
- **Tidak punya izin:** tampilkan mode baca-saja atau status akses ditolak beserta tautan kembali; sembunyikan aksi edit jika akses tak tersedia.
- **Konten belum disimpan:** indikator perubahan tertunda dan konfirmasi saat meninggalkan halaman.

Rich text harus dibersihkan di server menggunakan allowlist elemen/atribut dan URL aman. UX tidak boleh menyiratkan bahwa validasi sisi browser menggantikan pemeriksaan server. Gambar memakai alt text; alt kosong hanya diperbolehkan untuk gambar dekoratif.

## 7. Tabel, pencarian, dan urutan drag-and-drop

Gunakan DataTables dengan bahasa Indonesia, pencarian cepat, sorting kolom yang relevan, paging, jumlah baris per halaman, dan ringkasan jumlah hasil. Filter harus dapat dikombinasikan dan mudah dibersihkan (**Reset filter**). Simpan filter/sort dalam URL atau state halaman bila memungkinkan agar pengguna dapat kembali ke hasil yang sama.

### Drag-and-drop daftar soal

- Tampilkan handle drag khusus, nomor urutan, dan petunjuk “Seret untuk mengubah urutan”. Jangan jadikan seluruh baris area drag karena pengguna dapat salah memindahkan soal saat memilih teks.
- Urutan manual hanya berlaku pada satu bank/kategori/filter yang stabil. Saat filter/pencarian aktif, nonaktifkan drag atau tampilkan keterangan bahwa urutan penuh perlu dilihat tanpa filter.
- Setelah dilepas, tampilkan status “Menyimpan urutan…” lalu konfirmasi “Urutan diperbarui”. Jika simpan gagal, kembalikan ke urutan sebelumnya dan tampilkan aksi coba lagi.
- Sediakan alternatif tanpa pointer: tombol **Naik** dan **Turun**, atau kontrol posisi numerik dengan label; drag bukan satu-satunya cara mengurutkan.
- Perubahan urutan anggota bank tidak mengubah urutan kategori dalam blueprint dan tidak mengubah snapshot sesi yang sudah dimulai.

RowReorder mendukung pointer/touch; keyboard tetap membutuhkan kontrol eksplisit. Pada mobile, pilih kartu/baris ringkas atau disclosure untuk detail; jangan mengecilkan tabel desktop sampai teks dan aksi sulit disentuh.

## 8. Blueprint dan pembuatan sesi ujian

Halaman wizard lima langkah dengan ringkasan tetap:

1. **Profil aturan** — pilih profil SKD 2026 atau profil seleksi lain. Tampilkan tahun, sumber, durasi, total butir, ambang, dan status verifikasi.
2. **Bank sumber** — pilih satu atau lebih bank. Tampilkan pohon bank, jumlah soal siap per kategori, jumlah dipakai sesi lain bila relevan, dan jumlah yang dapat dipilih.
3. **Urutan kategori & kuota** — susun kategori dengan drag handle dan tombol naik/turun. Baris kategori memuat nama, jumlah diminta, jumlah tersedia, total skor maksimum, dan ambang. Preset awal SKD: TWK 30 → TIU 35 → TKP 45. Kuota dapat diedit untuk sesi non-preset bila role mengizinkan.
4. **Urutan soal** — per kategori pilih **Urutan manual** atau **Acak soal dalam kategori**. Mode manual memakai daftar soal berurutan dan kontrol drag/tombol. Mode acak menampilkan jumlah pool dan kuota, lalu ringkasan bahwa soal diundi saat attempt mulai. Kategori tetap mengikuti langkah 3.
5. **Tinjau & terbitkan** — tinjau durasi, profil, kategori/urutan/kuota, skor, sumber bank, mode randomisasi, dan validasi. Publikasi terkunci jika pool soal kurang, kategori kosong, bobot TKP tidak lengkap, atau aturan belum aktif/terverifikasi.

### Validasi dan ringkasan sesi

Di setiap langkah tampilkan jumlah **tersedia / dibutuhkan**, misalnya “42 tersedia · 30 dibutuhkan”. Tampilkan error pada kategori terkait dan ringkasan error di bagian atas. Jangan lanjut ke publikasi bila kuota lebih besar dari pool. Pertahankan nilai input jika validasi gagal.

Acak soal satu kali ketika attempt dibuat, simpan pilihan dan urutan final sebagai snapshot, dan tunjukkan bahwa refresh tidak mengubah urutan. Acak opsi menjadi pengaturan terpisah dan nonaktif secara default; bila opsi TKP berbobot, pastikan skor mengikuti identitas opsi, bukan posisi tampil. Riwayat attempt lama tidak berubah saat bank, soal, atau aturan diperbarui.

## 9. Status kosong, loading, error, dan izin

| Keadaan | Tampilan dan tindakan |
|---|---|
| Belum ada bank | Ilustrasi/ikon sederhana, penjelasan ringkas, CTA **Buat bank pertama** jika diizinkan. Jangan menyisakan kanvas kosong. |
| Bank belum berisi soal | Jelaskan bank aktif dan tombol **Tambah soal**; bila izin tidak ada, berikan pesan hubungi pengelola. |
| Pencarian/filter tanpa hasil | “Tidak ada soal yang cocok.” Tampilkan **Hapus filter** dan pertahankan pencarian. |
| Data sedang dimuat | Skeleton baris/kartu dengan ukuran serupa konten akhir; hindari spinner yang mengganti seluruh halaman. |
| Gagal memuat/simpan | Pesan yang menjelaskan tindakan gagal, tombol coba lagi, dan pertahankan input. Jangan menampilkan stack trace. |
| Tidak punya izin baca | Halaman akses ditolak yang konsisten dengan admin Aster, tombol kembali; jangan bocorkan isi data lewat tabel/HTML. |
| Tidak punya izin edit | Form baca-saja atau tautan kembali, dengan alasan akses ringkas. Tidak menampilkan kontrol submit aktif. |
| Soal terkunci riwayat | Jelaskan bahwa soal sudah dipakai attempt; tawarkan arsip atau lepas dari bank, bukan hapus permanen. |
| Blueprint tak valid | Ringkasan checklist masalah dengan tautan langsung ke kategori/field yang harus diperbaiki. |

## 10. Aksesibilitas dan responsivitas

- Semua kontrol memiliki label terlihat; placeholder bukan pengganti label.
- Gunakan heading berurutan, `fieldset`/`legend` untuk opsi, focus ring yang jelas, dan status dinamis yang diumumkan melalui live region.
- Toolbar Quill dapat dioperasikan keyboard dan memiliki nama aksesibel. Sediakan field teks alternatif gambar yang mudah ditemukan.
- Warna status selalu disertai teks/ikon; jangan bergantung pada biru/hijau/merah saja. Pertahankan kontras teks yang memadai.
- Modal konfirmasi mengunci fokus, dapat ditutup dengan keyboard, dan mengembalikan fokus ke pemicu.
- Drag-and-drop menyediakan alternatif keyboard dan kontrol sentuh berukuran nyaman.
- Pada lebar ponsel, susun form satu kolom, jadikan panel ringkasan disclosure, pertahankan aksi simpan mudah dijangkau, dan sediakan tampilan tabel responsif dengan detail baris yang dapat dibuka.
- Zoom browser 200% tidak boleh membuat toolbar, aksi simpan, atau konten penting terpotong.

## 11. Model izin yang tercermin di UI

Antarmuka membaca kapabilitas per aksi, bukan sekadar role label. Pemetaan menu yang disarankan:

| Area | Kapabilitas yang tercermin |
|---|---|
| Ikhtisar/bank | `question_banks.view`, `question_banks.create`, `question_banks.update`, `question_banks.delete` |
| Keanggotaan/reuse | `questions.view`, `questions.update` atau izin khusus keanggotaan bila disediakan; penghapusan anggota tidak sama dengan hapus soal pemilik |
| Kategori & bobot | `categories.view/create/update/delete`, `scoring_rules.view/update` |
| Soal/media | `questions.view/create/update/delete`, `media.upload/delete` |
| Blueprint/sesi | `exam_blueprints.view/create/update/delete/publish` |

Nama kapabilitas di atas adalah usulan UX untuk diselaraskan dengan skema dan route implementasi. Super Admin mengelola hak role pada halaman Akses & Role; perubahan hak tidak menggantikan pemeriksaan izin server pada setiap operasi.

## 12. Kriteria review UX sebelum implementasi dinyatakan selesai

- Admin dapat menemukan halaman kategori dari navigasi Bank Soal dan membedakan kategori resmi, subkategori belajar, serta profil non-SKD.
- Bobot TWK/TIU dan bobot opsi TKP terlihat sebelum soal dipakai; nilai menampilkan profil/tahun/sumber yang aktif.
- Soal menunjukkan satu bank pemilik dan daftar bank reuse; menambah/mencabut reuse tidak disamakan dengan duplikasi/hapus permanen.
- Stem, opsi, dan pembahasan memiliki alur rich text dan gambar dengan preview, alt text, progres, fallback, serta error yang mempertahankan input.
- DataTables dapat dicari, diurutkan, dipaginasi, dan tetap usable di layar kecil; drag mempunyai alternatif keyboard/tombol.
- Blueprint menampilkan urutan kategori, jumlah per kategori, pool tersedia, bobot/ambang, dan pilihan acak per kategori sebelum sesi diterbitkan.
- Tampilan loading, kosong, error, tidak ada izin, dan data terkunci sudah didefinisikan.
- Pola visual dan spasi mengikuti sidebar/panel admin Aster; tidak ada bagian utama yang tampak seperti daftar teks tanpa wadah, padding, atau hirarki.

## Referensi lisensi/tooling

- Quill: [repositori dan lisensi BSD-3-Clause](https://github.com/slab/quill/).
- DataTables: [lisensi MIT](https://datatables.net/license/); gunakan core dan ekstensi open-source yang diperlukan saja.
- [Responsive](https://datatables.net/manual/extensions/responsive/) untuk tabel layar sempit; [RowReorder](https://datatables.net/manual/extensions/rowreorder/) untuk drag/touch. Gunakan kontrol keyboard buatan aplikasi sebagai alternatif aksesibel.
