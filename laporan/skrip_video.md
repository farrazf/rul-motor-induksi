# Skrip dan Skenario Video Demo · Kasus 03 Sisa Umur Pakai Motor Induksi

Target durasi **4 menit 35 detik** (batas 5 menit, cadangan 25 detik). Susunannya kurang lebih mengikuti pembagian waktu
dari README mata kuliah: masalah, arsitektur (data → model → API → aplikasi), demo, lalu hasil dan keterbatasan.

Aturan mata kuliah: **setiap anggota menjelaskan bagian yang dikerjakannya sendiri.** Pembagian di bawah mengikuti
pembagian kerja di README dan lampiran laporan: Jundan memegang data dan model, Farraz memegang API dan aplikasi.

| Pembicara | Bagian | Waktu | Lama |
|---|---|---|---|
| Farraz | Perkenalan, masalah, dan pengguna | 0:00–0:40 | 40 detik |
| Jundan | Data dan pembersihan, pembagian data, model | 0:40–1:50 | 70 detik |
| Farraz | API, *deployment*, dan demo langsung | 1:50–3:35 | 105 detik |
| Jundan | Hasil, *baseline*, keterbatasan, penutup | 3:35–4:35 | 60 detik |

Total Farraz 2 menit 25 detik, Jundan 2 menit 10 detik. Hanya ada tiga kali pergantian pembicara.

**Cara memakai narasi.** Narasi di bawah ditulis seperti orang berbicara, bukan seperti tulisan laporan, dan angkanya
dibulatkan supaya enak diucapkan. Tidak perlu dibaca kata per kata: pahami isi tiap paragraf, lalu ucapkan dengan gaya
bicara sendiri. Yang harus tetap sama hanya urutan isi dan angkanya. Angka persisnya ada di tabel pada akhir dokumen ini.

## Persiapan sebelum merekam

Yang direkam hanya **suara**. Gambar di layar disusun belakangan mengikuti suara.

- Rekam satu berkas per bagian: `1_farraz`, `2a_jundan`, `2b_jundan`, `2c_farraz`, `3_farraz`, `4_jundan`.
- Rekam di ruangan yang sepi, dengan jarak ponsel atau mikrofon yang sama dari awal sampai akhir.
- Kalau salah ucap, diam sebentar lalu ulangi kalimatnya dari awal. Bagian yang salah dibuang saat penyuntingan.
- Di bagian demo (bagian 3), beri jeda sekitar satu detik di antara tiap langkah.
- Kirim berkas aslinya (sebagai dokumen atau lewat Drive), bukan pesan suara WhatsApp.
- Kalau jumlah seluruh rekaman lebih dari 4 menit 45 detik, buang langkah demo nomor 4 (sensor kosong).

## Skenario per adegan

### Adegan 1 · Perkenalan, masalah, dan pengguna (0:00–0:40) · Farraz

**Layar:** judul proyek dan nama anggota, lalu halaman depan aplikasi.

**Narasi:**

> Halo semua, perkenalkan nama saya Farraz Firdaus Nur Ardiyanto dari Prodi Mekatronika dan Kecerdasan Buatan, dan ini teman
> saya Jundan Abdul Wahhab, juga dari Prodi MKB. Di proyek kali ini, kami membuat sebuah sistem yang bisa memperkirakan
> sisa umur pakai motor induksi di pabrik.
>
> Jadi, kalau ada motor yang rusak, penggantinya itu baru datang dua sampai empat minggu setelah dipesan. Kalau pesannya
> telat, produksi berhenti. Kalau kecepatan, stoknya numpuk di gudang. Nah, dengan sistem ini, bagian pemeliharaan
> tinggal memasukkan data sensor motornya, nanti keluar perkiraan sisa umurnya dan saran kapan harus pesan pengganti.
> Untuk data dan modelnya, akan dijelaskan oleh Jundan.

### Adegan 2 · Arsitektur: data → model → API → aplikasi (0:40–2:15)

**2a. Data dan pembersihan (0:40–1:15) · Jundan**

**Layar:** diagram arsitektur sebentar (kotak "Data klien" dan "Notebook"), lalu tabel ringkasan masalah data di *notebook*.

> Oke, terima kasih Farraz. Jadi data yang kami pakai itu ada hampir 80 ribu baris dari 300 motor, yang dicatat setiap
> hari sampai motornya rusak. Nah, waktu kami cek, ternyata datanya masih berantakan. Misalnya, nomor motornya ditulis
> beda-beda, jadi yang harusnya 300 motor malah terbaca seribu lebih. Terus, suhu dari salah satu pabrik ternyata pakai
> kelvin, bukan celsius. Ada juga baris yang dobel, sama nilai getaran minus satu, yang ternyata itu kode error dari
> sensornya. Jadi semua itu kami bersihkan dulu sebelum melatih model.

**2b. Pembagian data dan model (1:15–1:50) · Jundan**

**Layar:** gambar getaran menurut umur total motor, lalu tabel perbandingan model di *notebook* (bagian 7).

> Selanjutnya, datanya kami bagi per motor, bukan per baris: 180 motor untuk latihan, 60 untuk validasi, dan 60 untuk
> pengujian. Kenapa per motor? Karena di pabrik nanti, modelnya dipakai untuk motor yang belum pernah dia lihat. Kalau
> barisnya diacak, modelnya kelihatan cuma meleset 5 hari, padahal aslinya 12 hari.
>
> Untuk modelnya, kami pakai gradient boosting. Kami juga memasukkan lama motor beroperasi, karena motor yang umurnya
> panjang ternyata rusaknya lebih pelan. Terakhir, motor yang sisa umurnya di bawah 60 hari kami kasih bobot tiga kali,
> karena di situ keputusan pesannya diambil. Selanjutnya saya kembalikan ke Farraz.

**2c. API dan deployment (1:50–2:15) · Farraz**

**Layar:** diagram arsitektur ("Artifact" → "predictor.py" → "FastAPI di Vercel" → "Halaman web"), lalu sekilas halaman `/docs`.

> Oke, jadi model yang sudah jadi tadi kami simpan, lalu kami buatkan API-nya pakai FastAPI. Tugas API ini ada tiga:
> memeriksa masukannya, menjalankan modelnya, lalu mengembalikan perkiraan, kisaran, dan statusnya. Kode pengolah datanya
> juga ikut disimpan bareng modelnya, jadi perhitungan waktu prediksi sama persis dengan waktu pelatihan. Setelah itu
> API-nya kami deploy ke Vercel, sekalian dengan halaman webnya. Sekarang kita langsung coba aplikasinya.

### Adegan 3 · Demo langsung (2:15–3:35) · Farraz

**Layar:** https://ml.deltavia.org sepanjang adegan.

| # | Aksi di layar | Yang muncul | Narasi |
|---|---|---|---|
| 1 | Tunjuk isian bawaan, klik **Perkirakan Sisa Umur** | 24 hari, kisaran 18–34 hari, **Pesan Pengganti Sekarang** | "Nah, ini tampilan aplikasinya, bisa dibuka juga dari HP. Misalnya ada motor 11 kilowatt yang sudah jalan 240 hari, getarannya 5,6. Saya klik Perkirakan Sisa Umur. Nah, hasilnya sisa umurnya sekitar 24 hari, dengan kisaran 18 sampai 34 hari. Statusnya 'pesan pengganti sekarang', karena pengirimannya bisa sampai empat minggu." |
| 2 | Klik contoh **Hampir rusak**, lalu **Perkirakan Sisa Umur** | 2 hari, **Segera Ganti** | "Sekarang kita coba motor yang getarannya sudah 7,3. Ternyata sisa umurnya tinggal 2 hari, dan statusnya berubah jadi 'segera ganti'." |
| 3 | Klik contoh **Masukan mustahil**, lalu **Perkirakan Sisa Umur** | **Masukan Tidak Wajar**, dua baris alasan | "Terus, gimana kalau datanya salah ketik? Saya coba isi getarannya minus lima dan kecepatannya 3.000 rpm. Nah, aplikasinya nggak error. Masukannya ditolak, dan ada pesan isian mana yang salah. Kalau di API-nya, ini dikembalikan sebagai kode 422." |
| 4 | Klik contoh **Mendekati rusak**, hapus isi **Arus**, lalu **Perkirakan Sisa Umur** | Hasil tetap keluar, ada bagian **Catatan** tentang sensor kosong | "Kalau ada sensor yang mati, isiannya dikosongkan saja. Modelnya tetap menjawab, tapi ada catatan kalau hasilnya kurang akurat." |
| 5 | Pindah ke **Banyak Motor**, klik **Pilih Berkas CSV**, pilih `contoh_batch.csv` | Ringkasan 2 / 1 / 5 dan tabel yang terurut | "Yang terakhir, kalau motornya banyak, tinggal upload file CSV. Dari delapan motor ini, dua harus segera diganti, satu perlu dipesan, dan lima masih aman. Tabelnya juga sudah diurutkan dari yang paling mendesak. Untuk hasil dan keterbatasannya, akan dijelaskan oleh Jundan." |

Langkah 3 adalah yang wajib (satu masukan tidak wajar). Langkah 4 boleh dibuang jika waktu tidak cukup.

### Adegan 4 · Hasil, *baseline*, dan keterbatasan (3:35–4:35) · Jundan

**Layar:** `08_hasil_test.png` untuk bagian hasil, lalu tab **Tentang Model** di aplikasi untuk bagian keterbatasan.

> Oke, sekarang hasilnya. Ukuran yang kami pakai itu MAE, yaitu rata-rata seberapa jauh tebakan modelnya meleset, khusus
> untuk motor yang sisa umurnya di bawah 60 hari. Di data uji, yang baru kami buka satu kali di akhir, baseline regresi
> linear meleset rata-rata hampir 31 hari. Sedangkan model kami melesetnya kurang dari 7 hari, jadi lebih dari empat kali
> lebih kecil. Semua dari 60 motor uji juga dapat peringatan paling lambat 28 hari sebelum rusak.
>
> Tapi sistem ini masih punya keterbatasan. Untuk motor yang masih sehat, modelnya cuma bisa bilang "masih lama", belum
> bisa kasih angka yang tepat. Tebakannya juga dibuat dari data satu hari saja, jadi bisa naik-turun. Dan datanya itu
> data buatan, padahal motor asli bisa saja rusak mendadak. Ke depannya, kami ingin memakai riwayat beberapa hari, karena
> di percobaan kami galatnya turun jadi sekitar empat setengah hari. Mungkin itu saja dari kami, terima kasih.

## Angka persis di balik narasi

Di narasi angkanya dibulatkan ("hampir 80 ribu", "hampir 31 hari", "kurang dari 7 hari"). Angka persisnya di bawah ini,
untuk berjaga-jaga kalau ditanya.

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
