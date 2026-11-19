# Skrip dan Skenario Video Demo · Kasus 03 Sisa Umur Pakai Motor Induksi

Target durasi **4 menit 30 detik** (batas 5 menit, cadangan 30 detik). Susunannya mengikuti pembagian waktu dari
README mata kuliah: masalah 30 detik, arsitektur 90 detik, demo 90 detik, hasil dan keterbatasan 60 detik.

Aturan mata kuliah: **setiap anggota menjelaskan bagian yang dikerjakannya sendiri.** Pembagian di bawah mengikuti
pembagian kerja di README dan lampiran laporan: Jundan memegang data dan model, Farraz memegang API dan aplikasi.

| Pembicara | Bagian | Waktu | Lama |
|---|---|---|---|
| Farraz | Masalah dan pengguna | 0:00–0:30 | 30 detik |
| Jundan | Data dan pembersihan, pembagian data, model | 0:30–1:35 | 65 detik |
| Farraz | API, *deployment*, dan demo langsung | 1:35–3:30 | 115 detik |
| Jundan | Hasil, *baseline*, keterbatasan, penutup | 3:30–4:30 | 60 detik |

Total Farraz 2 menit 25 detik, Jundan 2 menit 5 detik. Hanya ada tiga kali pergantian pembicara.

## Persiapan sebelum merekam

Buka semua ini lebih dulu, masing-masing di tab atau jendela sendiri, supaya tidak ada waktu terbuang untuk mencari:

1. `laporan/gambar/10_arsitektur.png` (diagram arsitektur)
2. *Notebook* `notebooks/rul_motor_induksi.ipynb`, digulir ke tabel ringkasan masalah data (akhir bagian 2)
3. `laporan/gambar/05_getaran_per_umur.png` (getaran menurut umur total motor)
4. `src/features.py` dan `artifacts/metadata.json` di editor
5. https://ml.deltavia.org (aplikasi) dan https://ml.deltavia.org/docs (dokumentasi API)
6. `data/contoh_batch.csv` sudah ada di folder yang mudah dipilih saat unggah
7. `laporan/gambar/08_hasil_test.png` (hasil pada data *test*)

Hal teknis:

- Rekam layar 1080p, perbesar tampilan browser ke 125–150% supaya angka terbaca.
- Buka aplikasi sekali sebelum merekam. Permintaan pertama setelah lama tidak dipakai butuh beberapa detik lebih lama.
- Tutup notifikasi dan tab pribadi. Wajah pembicara cukup di sudut layar atau di awal bagiannya.
- Latihan satu kali dengan *stopwatch*. Jika lewat 4:45, buang langkah demo nomor 4 (sensor kosong).

## Skenario per adegan

### Adegan 1 · Masalah dan pengguna (0:00–0:30) · Farraz

**Layar:** judul proyek dan nama anggota (sampul laporan), lalu halaman depan aplikasi.

**Narasi:**

> Halo, saya Farraz, bersama Jundan, dari Mekatronika dan Kecerdasan Buatan UPI. Klien kami adalah manajer pemeliharaan sebuah
> grup pabrik dengan ratusan motor induksi. Motor pengganti baru datang dua sampai empat minggu setelah dipesan.
> Kalau terlambat memesan, lini produksi berhenti. Kalau terlalu cepat, stok menumpuk. Karena itu kami membuat aplikasi
> untuk perencana pemeliharaan: masukkan pembacaan sensor hari ini, keluar perkiraan sisa umur motor dan saran kapan harus memesan.

### Adegan 2 · Arsitektur: data → model → API → aplikasi (0:30–2:00)

**2a. Data dan pembersihan (0:30–1:00) · Jundan**

**Layar:** diagram arsitektur 5 detik (tunjuk kotak "Data klien" dan "Notebook"), lalu tabel ringkasan masalah data di *notebook*.

> Datanya 79.652 baris dari 300 motor, dicatat setiap hari sampai motor rusak. Data ini belum bersih. Penulisan nomor
> motor tidak seragam, sehingga 300 motor terbaca sebagai 1.147. Suhu dari Plant Purwakarta ternyata dalam kelvin.
> Ada baris kembar, dan ada getaran bernilai minus satu sebagai kode galat sensor. Semuanya kami perbaiki di notebook,
> dan fungsi pembersihnya kami simpan di `src/features.py` supaya dipakai juga saat prediksi.

**2b. Pembagian data dan model (1:00–1:35) · Jundan**

**Layar:** gambar getaran menurut umur total motor, lalu tabel perbandingan model di *notebook* (bagian 7).

> Data kami bagi per motor, bukan per baris: 180 motor untuk melatih, 60 untuk validasi, 60 untuk uji. Alasannya, di
> pabrik model dipakai untuk motor yang belum pernah dilihatnya. Kalau baris diacak, galat tampak 5 hari, padahal
> sebenarnya 12 hari. Modelnya gradient boosting. Dari EDA kami melihat motor berumur panjang rusak lebih lambat, jadi
> hari operasi kami jadikan masukan. Terakhir, baris dengan sisa umur di bawah 60 hari kami beri bobot tiga kali,
> karena di rentang itulah keputusan pemesanan diambil.

**2c. API dan deployment (1:35–2:00) · Farraz**

**Layar:** diagram arsitektur (tunjuk "Artifact" → "predictor.py" → "FastAPI di Vercel" → "Halaman web"), lalu sekilas `metadata.json` dan halaman `/docs`.

> Model dan metadatanya disimpan sebagai artifact. FastAPI memuatnya satu kali, memeriksa masukan, lalu mengembalikan
> prediksi, kisaran, dan status. API ini kami pasang di Vercel dan sekaligus menyajikan halaman web untuk pengguna.
> Pembuat fitur berada di dalam pipeline, jadi kode saat prediksi sama persis dengan saat pelatihan.

### Adegan 3 · Demo langsung (2:00–3:30) · Farraz

**Layar:** https://ml.deltavia.org sepanjang adegan.

| # | Aksi di layar | Yang muncul | Narasi |
|---|---|---|---|
| 1 | Tunjuk isian bawaan, klik **Perkirakan Sisa Umur** | 24 hari, kisaran 18–34 hari, **Pesan Pengganti Sekarang** | "Ini aplikasinya, bisa dibuka dari ponsel juga. Motor 11 kW, umur 240 hari, getaran 5,6. Perkiraannya 24 hari dengan kisaran 18 sampai 34 hari. Statusnya pesan pengganti sekarang, karena pengiriman bisa sampai empat minggu." |
| 2 | Klik contoh **Hampir rusak**, lalu **Perkirakan Sisa Umur** | 2 hari, **Segera Ganti** | "Untuk motor dengan getaran 7,3, sisa umurnya tinggal 2 hari. Statusnya segera ganti." |
| 3 | Klik contoh **Masukan mustahil**, lalu **Perkirakan Sisa Umur** | **Masukan Tidak Wajar**, dua baris alasan | "Sekarang masukan yang tidak wajar: getaran minus lima dan kecepatan 3.000 rpm. Aplikasi tidak berhenti. Masukan ditolak, pesannya menyebut kolom yang salah, dan API mengembalikan kode 422." |
| 4 | Klik contoh **Mendekati rusak**, hapus isi **Arus**, lalu **Perkirakan Sisa Umur** | Hasil tetap keluar, ada bagian **Catatan** tentang sensor kosong | "Kalau sebuah sensor mati, isiannya cukup dikosongkan. Model tetap menjawab, disertai catatan bahwa tebakannya kurang tepat." |
| 5 | Pindah ke **Banyak Motor**, klik **Pilih Berkas CSV**, pilih `contoh_batch.csv` | Ringkasan 2 / 1 / 5 dan tabel yang terurut | "Untuk banyak motor sekaligus, unggah CSV. Dari delapan motor, dua harus segera diganti, satu perlu dipesan, dan lima aman. Tabelnya diurutkan dari yang paling mendesak." |

Langkah 3 adalah yang wajib (satu masukan tidak wajar). Langkah 4 boleh dibuang jika waktu tidak cukup.

### Adegan 4 · Hasil, *baseline*, dan keterbatasan (3:30–4:30) · Jundan

**Layar:** `08_hasil_test.png` (0:00–0:35 dari adegan ini), lalu tab **Tentang Model** di aplikasi untuk bagian keterbatasan.

> Metrik utama kami adalah MAE pada baris dengan sisa umur di bawah 60 hari. Pada data uji, yang hanya kami buka satu
> kali di akhir, baseline regresi linear meleset rata-rata 30,9 hari. Model kami meleset 6,8 hari, atau 78 persen lebih
> kecil. Seluruh 60 motor uji mendapat peringatan untuk memesan paling lambat 28 hari sebelum rusak.
>
> Model ini punya batas. Untuk motor yang masih sehat, di atas kira-kira 150 hari, tebakan hanya berarti "masih lama".
> Model hanya mengenal tiga tipe motor yang belum pernah diperbaiki. Tebakan dibuat dari pembacaan satu hari, jadi bisa
> naik-turun. Datanya juga sintetis, sedangkan motor nyata bisa rusak mendadak. Langkah berikutnya adalah memakai
> riwayat beberapa hari, yang pada percobaan kami menurunkan galat menjadi 4,6 hari. Terima kasih.

## Angka yang harus diucapkan dengan tepat

| Hal | Angka |
|---|---|
| Ukuran data | 79.652 baris, 300 motor (terbaca 1.147 sebelum dibersihkan) |
| Pembagian data | 180 / 60 / 60 motor |
| Efek kebocoran data | 5,2 hari (acak) vs 12,0 hari (per motor) |
| MAE RUL ≤ 60 pada data *test* | *baseline* 30,87 → model 6,84 hari (78% lebih kecil) |
| MAE semua baris pada data *test* | *baseline* 49,05 → model 39,82 hari |
| Ambang status | pesan bila ≤ 45 hari, segera ganti bila ≤ 18 hari |
| Motor *test* yang mendapat alarm ≥ 28 hari sebelum rusak | 60 dari 60 |
| Eksperimen riwayat (data *validation*) | 7,47 → 4,56 hari |

## Pertanyaan yang mungkin ditanyakan dosen

- **Mengapa dibagi per motor?** Baris dari satu motor saling mirip. Jika diacak, model diuji pada motor yang sudah dilihatnya dan galat tampak jauh lebih kecil daripada kenyataan.
- **Apakah `hari_operasi` membocorkan target?** Tidak. Nilainya selalu diketahui perencana (tanggal pemasangan), sedangkan umur total motor tidak pernah diberikan ke model.
- **Mengapa ambang 45 hari padahal pengiriman paling lama 28 hari?** Selisihnya adalah margin untuk galat model. Ini ambang terkecil yang membuat sedikitnya 95% motor *validation* mendapat alarm 28 hari sebelum rusak.
- **Mengapa MAE semua baris masih 40 hari?** Motor sehat belum memberi tanda pada sensor, jadi sisa umur yang besar memang tidak bisa ditebak dari satu hari pembacaan. Karena itu metrik utamanya dibatasi pada RUL ≤ 60.
- **Mengapa sensor kosong dibiarkan kosong?** Sensor juga bisa mati saat model dipakai, dan *gradient boosting* berbasis histogram bisa menerima nilai kosong.
