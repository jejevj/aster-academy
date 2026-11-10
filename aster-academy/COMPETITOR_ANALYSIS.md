# Analisis Kompetitor dan Prioritas Produk Aster Academy

**Tanggal riset:** 10 November 2026
**Cakupan:** platform persiapan SKD/sekolah kedinasan yang dapat diakses publik. Klaim kompetitor diringkas dari halaman resmi atau halaman produk mereka; angka pemasaran tidak divalidasi secara independen.

## Posisi Aster Saat Ini

Aster sudah memiliki fondasi yang tepat untuk simulasi SKD: bank soal terstruktur, blueprint kategori, snapshot attempt yang menjaga riwayat, aturan skor/passing grade, materi, dan progres pelajaran. Namun nilai pengguna yang terlihat masih tertinggal karena dashboard siswa belum sebelumnya menampilkan hasil tryout dan jadwal nyata, belum ada laporan analitik per topik, tryout terjadwal/ranking, komunitas, atau jalur seleksi lanjutan.

## Peta Kompetitor

| Produk | Penawaran yang tampak | Implikasi untuk Aster |
|---|---|---|
| Analitica | Latihan, tryout, laporan perkembangan, komunitas Circle, dan asisten AI untuk SKD Kedinasan.[1] | Kombinasi latihan + laporan terarah adalah benchmark paling relevan. AI/community bukan prioritas awal tanpa moderation dan sumber konten yang matang. |
| Ruangguru | CAT 100 menit, 110 soal TWK/TIU/TKP, pembahasan, pengulangan tryout, video, dan komunitas/grup diskusi.[2] | Aster sudah dekat pada mesin tryout; perlu pengalaman pasca-tryout yang lebih berguna dan kurikulum belajar yang terkait kelemahan siswa. |
| Siap Dinas | Hasil langsung, pembahasan, sertifikat, ebook, ranking nasional/provinsi/kota, dan retry terbatas.[3] | Ranking dan sertifikat bernilai pemasaran, tetapi baru layak setelah identitas peserta, kebijakan event, dan integritas leaderboard tersedia. |
| Gass Education | CAT, skor real-time, pembahasan, ranking nasional, tryout event, analisis jawaban, dan grup belajar.[4] | Fitur yang paling layak ditiru adalah event tryout terjadwal + analisis jawaban, bukan ranking terlebih dahulu. |
| kedinasan.id | CAT, analisis kelemahan, materi/video/ebook, kelas Zoom mentor, dan jadwal live.[5] | Aster sudah memiliki data jadwal live dan materi; perlu menampilkannya secara nyata di dashboard siswa lalu menambah hubungan rekomendasi belajar. |
| Bimbelio | Analitik kemampuan dan rekomendasi personal, mentor, live class, dan AI 24/7.[6] | Rekomendasi personal harus dimulai dari aturan deterministik berbasis kategori; jangan lompat ke AI sebelum data/guardrail siap. |
| Schoolmedia | CBT, autosave jawaban, timer per subtes, analitik skor subtes, banyak tipe soal, dan pembahasan.[7] | Autosave jawaban adalah gap reliabilitas yang penting. Aster sekarang masih mengandalkan aksi “Simpan & lanjut”. |
| Kelas ASN | Simulasi CAT, pembahasan, ranking, komunitas, serta analisis target/formasi.[8] | Untuk kedinasan, modul informasi target sekolah dan tahapan seleksi lebih relevan daripada meniru data formasi CPNS secara langsung. |

## Fitur yang Diadaptasi Sekarang

Dashboard siswa kini membaca hasil tryout yang telah selesai dan jadwal live yang sudah diterbitkan dari database, bukan lagi menampilkan placeholder. Hasil menampilkan judul tryout, waktu selesai, skor, total nilai, persentase, dan tautan opaque ke review hasil. Ini mengadopsi prinsip laporan hasil instan dari kompetitor, tetapi menggunakan data nyata dan tidak membuat klaim prediktif tentang peluang kelulusan.

## Backlog Produk yang Direkomendasikan

### P0 — Nilai Belajar dan Reliabilitas

1. **Analisis pasca-tryout per kategori dan rekomendasi belajar deterministik**
   - Tampilkan TWK/TIU/TKP terlemah, perbandingan attempt terakhir dengan sebelumnya, dan tautan ke materi/kumpulan soal kategori tersebut.
   - Dasar: kompetitor menonjolkan laporan/analisis kelemahan.[1][4][5]
   - Guardrail: tampilkan sebagai evaluasi latihan, bukan prediksi lolos.

2. **Autosave jawaban tryout**
   - Simpan saat opsi dipilih atau dengan debounce singkat; tetap validasi di server dan pertahankan submit eksplisit untuk selesai.
   - Dasar: CBT kompetitor menonjolkan autosave dan timer yang presisi.[7]
   - Acceptance: refresh halaman tidak kehilangan jawaban yang sudah dipilih.

3. **Tryout terjadwal sebagai event**
   - Status daftar/buka/tutup/hasil terbit, window pengerjaan, dan hasil baru tersedia setelah event ditutup jika kebijakan menghendaki.
   - Dasar: event tryout reguler dipakai oleh Gass Education dan Ruangguru.[2][4]
   - Guardrail: pisahkan clearly dari latihan mandiri yang dapat diulang.

### P1 — Diferensiasi Kedinasan

4. **Peta target sekolah dan tahap seleksi**
   - Siswa memilih target seperti STIS, STAN, IPDN, STMKG; dashboard menampilkan konten dan tahapan yang relevan (SKD, matematika STIS, TPA/TBI, psikotes, kebugaran bila tersedia).
   - Dasar: kompetitor menggabungkan persiapan lintas tahap dan target sekolah.[4][5][6]
   - Guardrail: sumber dan tanggal informasi pendaftaran wajib dicatat; konten usang harus terlihat sebagai usang.

5. **Roadmap belajar 4–8 minggu berbasis target dan nilai awal**
   - Hasil diagnostic singkat menghasilkan rencana mingguan, materi prioritas, dan target latihan.
   - Dasar: Superlatif memasarkan roadmap/jadwal belajar, sementara Bimbelio menonjolkan rekomendasi personal.[6]
   - Implementasi pertama cukup rule-based, bukan AI.

6. **Review pembahasan yang terstruktur**
   - Tandai soal untuk diulang, catatan pribadi, dan drill per kategori/subkategori dari soal salah.
   - Dasar: pembahasan detail dan evaluasi jawaban adalah baseline pasar.[2][3][4][7]

### P2 — Hanya Setelah Data dan Operasi Siap

7. **Leaderboard event yang sehat**
   - Ranking per event dengan opt-in nama samaran, waktu snapshot jelas, dan perlindungan privasi.
   - Dasar: ranking nasional tersebar luas pada kompetitor.[3][4][8]
   - Jangan rilis ranking global tanpa volume peserta, anti-cheat, dan kebijakan privasi.

8. **Komunitas dan mentor**
   - Mulai dari Q&A yang dimoderasi per materi/tryout sebelum forum bebas.
   - Dasar: Circle/grup/mentor adalah pembeda kompetitor.[1][2][5][6]
   - Risiko: membutuhkan moderation, laporan abuse, dan aturan konten.

9. **Asisten AI**
   - Gunakan untuk menjelaskan pembahasan dan menyusun latihan; semua jawaban harus dibatasi ke materi tervalidasi dan memiliki jalur eskalasi mentor.
   - Dasar: Analitica dan Bimbelio menawarkan asisten AI.[1][6]
   - Risiko: biaya, halusinasi, privasi siswa, dan integritas materi. Bukan prioritas MVP.

10. **Sertifikat dan pembayaran**
   - Sertifikat hanya untuk event yang kriteria dan identitas pesertanya jelas; pembayaran setelah paket, entitlement, refund, dan audit transaksi dirancang.
   - Dasar: sertifikat/akses premium dipakai oleh Siap Dinas dan Analitica.[1][3]

## Keputusan Manajerial

Jangan mengejar daftar fitur terbanyak. Urutan investasi Aster adalah:

1. Keandalan tryout dan evaluasi nyata.
2. Rekomendasi belajar berbasis kategori dan target sekolah.
3. Event terjadwal serta analitik perkembangan.
4. Baru kemudian komunitas, leaderboard, AI, sertifikat, dan monetisasi.

Keunggulan realistis Aster adalah transparansi: aturan skor bersumber, snapshot historis tidak berubah, hasil tidak dilebih-lebihkan sebagai jaminan lolos, dan rekomendasi dapat ditelusuri ke hasil latihan siswa.

## Sources

[1] https://analitica.id/tryout-skd-kedinasan — Analitica SKD Kedinasan
[2] https://www.ruangguru.com/kedinasan — Ruangguru Kedinasan
[3] https://siapdinas.com — Siap Dinas
[4] https://www.gasseducation.com — Gass Education
[5] https://kedinasan.id — kedinasan.id
[6] https://bimbelio.com — Bimbelio
[7] https://tryout.schoolmedia.id — Schoolmedia Tryout
[8] https://kelasasn.id — Kelas ASN
