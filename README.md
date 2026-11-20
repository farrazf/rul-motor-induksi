# Sisa Umur Pakai Motor Induksi · Farraz dan Jundan

**Kasus:** 03 · Sisa Umur Pakai Motor Induksi · **Aplikasi:** https://ml.deltavia.org · **Repositori:** https://github.com/farrazf/rul-motor-induksi · **Video:** https://drive.google.com/file/d/1LV25Rwxy1waTMwxEyEd-OfOPiUbOL2xu/view?usp=sharing

| Anggota | NIM | Bagian yang dikerjakan |
|---|---|---|
| Farraz Firdaus Nur Ardiyanto | 2405166 | API FastAPI dan validasi masukan, halaman web, uji otomatis, *deployment*, serta bagian 5–6 laporan |
| Jundan Abdul Wahhab | 2405647 | EDA dan pembersihan data, `src/features.py`, *baseline*, perbandingan dan evaluasi model, ambang status, serta bagian 1–4 laporan |

## Masalah dan pengguna

Penggunanya adalah perencana pemeliharaan sebuah grup pabrik yang mengoperasikan ratusan motor induksi. Motor pengganti
baru tiba 2–4 minggu setelah dipesan, jadi keputusan yang dibantu model adalah **kapan memesan**. Dari pembacaan sensor
satu hari, model menebak sisa umur pakai motor (`rul_hari`) dan aplikasi mengubahnya menjadi status
**aman / pesan pengganti sekarang / segera ganti**. Menebak terlalu tinggi (pesanan terlambat, lini berhenti) jauh lebih
mahal daripada menebak terlalu rendah (motor dipesan terlalu dini).

## Data dan pembersihan

`data/raw.csv`: 79.652 baris, 11 kolom, 300 motor yang dicatat harian sejak dipasang sampai rusak.
Setelah dibersihkan: 79.159 baris, tepat 300 motor. Rinciannya ada di bagian 2–3 *notebook*.

| Masalah yang ditemukan | Jumlah baris | Cara menangani |
|---|---|---|
| `motor_id` ditulis tidak seragam (`m-001`, `M001`, `M-001`) | 3.185 | Angkanya diambil lalu ditulis ulang `M-001`. Tanpa ini terbaca 1.147 motor dan motor yang sama bisa masuk *train* sekaligus *test* |
| `tipe_motor` salah tulis (`22KW`, `5,5 kW`) atau berbeda dari tipe motor itu sendiri | 1.588 | Tulisan dirapikan, lalu dipakai tipe mayoritas tiap motor (daya nominal sebuah motor tidak berubah) |
| Baris kembar | 493 | Dihapus, disisakan satu per motor per hari |
| Suhu belitan dalam kelvin (Plant Purwakarta) | 25.355 | Nilai > 200 dikurangi 273,15 |
| `arus_A` kosong / `suhu_belitan_C` kosong | 1.602 / 794 | Dibiarkan kosong: sensor juga bisa mati saat model dipakai, dan model yang dipilih bisa menerima nilai kosong |
| Getaran bernilai −1 (kode galat sensor) | 241 | Dijadikan kosong |
| Hari yang tidak tercatat | 1.198 | Dibiarkan, karena model menebak dari satu baris |
| Beban di atas 100% | 797 | Dipertahankan (maksimum 110%, masih wajar untuk beban lebih sesaat) |

## Hasil

Metrik utama: **MAE pada baris dengan RUL ≤ 60 hari** (rentang tempat keputusan pemesanan diambil). MAE semua baris sebagai pelengkap.
Data dibagi **per motor** (180 *train* / 60 *validation* / 60 *test*), karena di pabrik model dipakai untuk motor yang belum
pernah dilihat sampai rusak. Jika baris diacak, galat tampak 5,2 hari padahal sebenarnya 12,0 hari (percobaan di bagian 4 *notebook*).

| Model | MAE RUL ≤ 60 *validation* | MAE RUL ≤ 60 *test* | MAE semua baris *test* |
|---|---|---|---|
| *Baseline*: regresi linear, enam sensor asli | 30,91 | 30,87 | 49,05 |
| Model final: *gradient boosting* + fitur buatan + `hari_operasi` + bobot 3× pada RUL ≤ 60 | **7,47** | **6,84** | 39,82 |

Urutan perbaikan pada data *validation* (MAE RUL ≤ 60): regresi linear 30,91 → *random forest* 13,99 → *gradient boosting* 12,65
→ + fitur buatan 12,38 → + `hari_operasi` 8,79 → + bobot 7,47.

*Threshold* yang dipakai (dipilih dari data *validation*, tersimpan di `artifacts/metadata.json`):

- **Pesan pengganti sekarang bila tebakan ≤ 45 hari.** Ini ambang terkecil yang membuat ≥ 95% motor menerima alarm pertama
  minimal 28 hari (pengiriman terlama) sebelum rusak. Pada data *test*, 60 dari 60 motor memenuhinya.
- **Segera ganti bila tebakan ≤ 18 hari.** Ini ambang terkecil yang menangkap ≥ 95% baris dengan RUL ≤ 14 hari (pengiriman tercepat).
  Pada data *test* tertangkap 95,8%.

## Cara menjalankan

Butuh Python 3.12.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.api.main:app --reload       # API + halaman web: http://127.0.0.1:8000 (dokumentasi API di /docs)
streamlit run app/ui/streamlit_app.py   # antarmuka alternatif dengan Streamlit
```

Menjalankan ulang *notebook* dan uji otomatis:

```bash
pip install -r requirements-dev.txt
jupyter nbconvert --to notebook --execute --inplace notebooks/rul_motor_induksi.ipynb   # ±1,5 menit
pytest -q                                                                               # 25 uji
```

Contoh memanggil API:

```bash
curl -X POST https://ml.deltavia.org/predict -H "content-type: application/json" \
  -d '{"tipe_motor":"11kW","hari_operasi":240,"beban_pct":76,"arus_A":17.4,"tegangan_V":380,"suhu_belitan_C":78.5,"getaran_rms_mm_s":5.6,"kecepatan_rpm":1462}'
# → rul_hari 24.1, kisaran 18–34, status "PESAN PENGGANTI SEKARANG"
```

| Endpoint | Kegunaan |
|---|---|
| `GET /` | Halaman web: formulir satu motor, unggah CSV banyak motor, penjelasan model |
| `POST /predict` | Satu motor. Masukan mustahil ditolak dengan kode 422 dan pesan berbahasa Indonesia |
| `POST /predict/batch` | Banyak motor, ketat: satu baris mustahil menolak seluruh permintaan |
| `POST /predict/tabel` | Banyak motor, longgar (dipakai unggah CSV): baris mustahil dilaporkan, baris lain tetap diprediksi |
| `GET /health` | Versi model, ambang status, dan metrik |

### Deployment

Aplikasi berjalan di Vercel sebagai satu fungsi Python. `pyproject.toml` menunjuk `app.api.main:app` dan hanya memuat
library yang dibutuhkan saat prediksi; `.vercelignore` menahan *notebook*, laporan, data mentah, dan Streamlit agar tidak ikut diunggah.

```bash
npx vercel deploy --prod
```

`Dockerfile` disediakan sebagai alternatif (misalnya Hugging Face Spaces), dan `app/ui/streamlit_app.py` bisa dipasang
di Streamlit Community Cloud.

## Struktur repositori

```
notebooks/rul_motor_induksi.ipynb   dari data mentah sampai model tersimpan (11 bagian)
data/raw.csv                        data mentah dari klien
data/bersih.csv                     hasil pembersihan (ditulis notebook)
data/contoh_batch.csv               contoh berkas untuk fitur unggah CSV
src/features.py                     pembersihan dan pembuat fitur, dipakai saat pelatihan dan saat prediksi
artifacts/model.joblib              pipeline: pembuat fitur + model
artifacts/metadata.json             versi, fitur masukan, ambang status, metrik, rentang data latih
app/skema.py                        aturan validasi masukan (satu tempat untuk API dan Streamlit)
app/predictor.py                    memuat model, membuat status, kisaran, dan catatan
app/api/main.py                     FastAPI
app/web/index.html                  halaman web yang disajikan FastAPI
app/ui/streamlit_app.py             antarmuka alternatif (Streamlit)
tests/test_api.py                   uji otomatis: masukan wajar, ekstrem, kotor, dan mustahil
laporan/                            laporan (.docx dan .pdf) beserta gambarnya
```

## Keterbatasan

- **Motor sehat.** Selama motor masih sehat, sensor belum memberi tanda. Di atas ±150 hari tebakan hanya berarti
  "masih lama" (MAE ±58 hari, setara *baseline*).
- **Di luar data latih.** Model hanya mengenal motor 5,5 kW, 11 kW, dan 22 kW pada 380 V yang berjalan sampai rusak tanpa
  pernah diperbaiki. Setelah perbaikan besar, `hari_operasi` tidak lagi mencerminkan umur motor.
- **Satu hari.** Tebakan dibuat dari pembacaan satu hari sehingga naik-turun mengikuti derau sensor; 46% baris dengan
  RUL 29–60 hari masih berstatus aman pada hari tertentu. Memakai riwayat (rata-rata 7 hari + tren getaran) menurunkan
  MAE *validation* dari 7,47 menjadi 4,56 hari, tetapi pengguna harus mengunggah pembacaan beberapa minggu (bagian 9 *notebook*).
- **Data sintetis.** Hanya ada satu pola kerusakan yang berangsur. Motor nyata bisa rusak mendadak tanpa gejala,
  dan data itu belum tersedia. Belum ada pula data biaya henti produksi untuk menghitung ambang dari sisi biaya.

## Daftar periksa sebelum dikumpulkan

- [x] Repositori bersifat publik dan setiap anggota memiliki *commit*
- [x] *Notebook* dapat dijalankan ulang dari awal sampai akhir tanpa galat
- [x] *Baseline* wajib dilaporkan dan dibandingkan
- [x] Data *test* hanya dibuka satu kali, di akhir
- [x] `artifacts/metadata.json` berisi versi model, fitur masukan, *threshold*, dan metrik
- [x] Aplikasi dapat dibuka orang lain melalui tautan, termasuk dari ponsel
- [x] Aplikasi tidak berhenti mendadak ketika menerima masukan yang tidak wajar
- [x] Laporan paling banyak 6 halaman dan video paling lama 5 menit (4 menit 50 detik)
