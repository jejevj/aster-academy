# RES Public Recon: kedinasan.id

**Tanggal observasi:** 8 November 2026  
**Cakupan:** halaman publik yang dapat dibaca tanpa akun.  
**Mode:** observe-only. Tidak login, mengirim formulir, membuat akun, atau mengubah data.

## Charter

Gunakan kedinasan.id sebagai referensi untuk memperkaya rencana Aster Academy dengan pola produk bimbingan belajar dan persiapan ujian. Hasil ini mendokumentasikan pola dan fitur yang terlihat, bukan spesifikasi lengkap produk privat.

## Temuan teramati

| ID | Temuan | Bukti |
|---|---|---|
| PUB-01 | Beranda mengikuti urutan promosi: proposisi nilai dan CTA, bukti sosial, masalah belajar, solusi, proses belajar, kelas live, testimoni, angka hasil, unduhan aplikasi, footer. | [Beranda](https://kedinasan.id/) |
| PUB-02 | Produk dibagi menjadi paket bimbel per sekolah kedinasan dan paket tryout yang dapat dicari/dipilih. Halaman paket bimbel menampilkan rentang harga per sekolah. | [Paket bimbel](https://kedinasan.id/product), [Paket tryout](https://kedinasan.id/product-to) |
| PUB-03 | Beranda menjanjikan tryout CAT, analisis hasil, materi/video/e-book, dan kelas Zoom dengan mentor. | [Beranda](https://kedinasan.id/) |
| PUB-04 | Ada jadwal kelas live dengan filter sekolah, waktu, durasi, kategori materi, dan CTA bergabung. | [Jadwal Zoom](https://kedinasan.id/jadwal-zoom) |
| PUB-05 | Ada alat pencocokan sekolah kedinasan berdasarkan data pendidikan dan profil fisik seperti kondisi mata, tinggi, berat, dan tanggal lahir. Formulir ini membaca data sensitif; implementasi Aster perlu tujuan, persetujuan, minimisasi, dan retensi data yang jelas. | [Cek Sekdin](https://kedinasan.id/cek-sekdin) |
| PUB-06 | Pusat informasi berupa artikel dapat dicari dan difilter menurut sekolah kedinasan; artikel mengarah kembali ke paket belajar. | [Artikel](https://kedinasan.id/blogs) |
| PUB-07 | Beranda menampilkan testimoni alumni, sekolah tujuan, angka alumni/tryout/materi, kanal aplikasi, dan CTA WhatsApp sebagai unsur kepercayaan dan konversi. | [Beranda](https://kedinasan.id/) |

## Inventaris fitur awal

1. Beranda pemasaran dengan CTA utama ke katalog dan CTA bantuan.
2. Katalog program/bimbel yang dikelompokkan menurut sekolah atau jalur seleksi.
3. Katalog tryout dan detail paket latihan.
4. Detail program dengan kurikulum, materi, mentor, jadwal, dan opsi pendaftaran.
5. Dashboard belajar: video/materi, tryout, analisis hasil, progres, dan kelas live.
6. Kalender kelas live dengan filter kategori/jalur.
7. Artikel informasi dengan pencarian dan filter.
8. Direktori sekolah dan alat pencocokan profil (fitur opsional setelah kebutuhan privasi dikaji).
9. Testimoni, hasil alumni, FAQ, bantuan, dan halaman kebijakan.

## Implikasi untuk Aster Academy

- Ganti konsep kursus umum dalam [plan.md](plan.md) dengan platform persiapan seleksi yang punya program per jalur/sekolah, latihan CAT, pembahasan, kelas live, dan konten informasi.
- Pertahankan rancangan Aster sendiri: identitas visual biru glassmorphism/minimalis, penamaan, teks, ikon, foto, testimoni, dan aset orisinal. Yang diambil sebagai referensi adalah arsitektur informasi dan pola alur umum.
- Tambahkan entitas data kandidat: `institutions`, `programs`, `packages`, `question_sets`, `questions`, `attempts`, `attempt_answers`, `live_sessions`, `articles`, `testimonials`. Pemetaan ini masih hipotesis untuk Aster, bukan skema internal kedinasan.id.
- Fitur tes profil sekolah memerlukan tinjauan terpisah sebelum dibuat karena mengumpulkan informasi fisik dan tanggal lahir.
- Penjualan/pembayaran tampak sebagai bagian dari model paket, tetapi alur checkout, pembayaran, akses setelah pembelian, dan refund belum diamati.

## Belum teramati / pertanyaan terbuka

- Alur login, onboarding, pembelian, pembayaran, entitlement, tryout, skor, pembahasan, dan dashboard di `app.kedinasan.id` tidak diperiksa karena memerlukan sesi akun.
- Tidak ada pengamatan browser interaktif, state loading/error, aksi pada form, respons jaringan, atau tampilan responsif. Karena itu, aturan bisnis, model data nyata, API, dan design token belum dikonfirmasi.
- Validitas angka pemasaran dan aturan seleksi perlu diverifikasi dengan sumber resmi sebelum dipakai di Aster.
- Perlu menentukan apakah Aster menyediakan kursus gratis, paket berbayar, atau keduanya; layanan pembayaran dan sumber video juga belum diputuskan.

## Batas pemakaian

Catatan publik ini dibuat dengan membaca halaman yang tersedia tanpa login dan tanpa melakukan tindakan yang mengubah data. RES mensyaratkan penggunaan pada produk yang pengguna berwenang untuk pelajari. Skill tersebut juga mengharuskan browser terpisah/akun khusus untuk penelusuran interaktif. Tahap ini hanya mencakup public recon; belum ada pemetaan interaktif atau handoff RES penuh.
