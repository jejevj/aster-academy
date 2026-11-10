# Arsitektur Aster Academy

Aplikasi menggunakan pola MVC berlapis dengan Python standard library. Refactor berlangsung bertahap agar route dan data SQLite yang sudah digunakan tetap kompatibel.

```text
app.py                      Entry point: inisialisasi schema dan jalankan HTTP server
controllers/http_controller.py
                            HTTP controller: parsing request, routing, response, render template
services/                    Aturan autentikasi, formatting, sanitasi rich text,
                              dan operasi domain soal/attempt
repositories/                 Akses koneksi SQLite
models/                       Konfigurasi database dan model setting koneksi
core.py                       Kompatibilitas sementara: konfigurasi, permission,
                              schema bootstrap, dan fungsi lama yang masih dipakai controller
```

## Pembagian tanggung jawab

- **Model:** `models/database.py` memuat `DatabaseSettings` dan konfigurasi path.
- **Repository:** `repositories/sqlite_repository.py` membuka koneksi SQLite dengan row factory, foreign keys, dan timeout.
- **Service:** `services/authentication.py`, `services/rich_text.py`, `services/formatting.py`, dan `services/question_service.py` menyediakan aturan reusable di luar HTTP handler.
- **Controller:** `controllers/http_controller.py` menangani HTTP dan alur route. Template sidebar admin bersama berada di `templates/admin_sidebar.html`.
- **Entry point:** `app.py` memulai migrasi dan server, tetap kompatibel dengan perintah sebelumnya.

## Status dan langkah berikutnya

Fondasi MVC telah dipisah dan import lama tetap diarahkan melalui entry point. Sebagian handler masih menjalankan SQL langsung dan `core.py` masih memuat banyak routing-adjacent helpers/schema setup. Tahap berikutnya adalah memindahkan akses data per domain ke repository, aturan alur ke service, lalu mengurangi `core.py` menjadi konfigurasi/bootstrap saja. Setiap pemindahan mempertahankan kontrak route dan menggunakan migrasi SQLite non-destruktif.
