"""Aplikasi Streamlit untuk perencana pemeliharaan.

Jalankan dari root repositori:
    streamlit run app/ui/streamlit_app.py

Dua mode:
- Mode A (API_URL kosong): model dimuat langsung di sini. Paling mudah di-deploy (Streamlit Community Cloud).
- Mode B (API_URL diisi, mis. https://xxx.hf.space): memanggil FastAPI lewat HTTP.
  Isi lewat environment variable API_URL, atau di Streamlit Cloud: Settings → Secrets → API_URL = "https://..."
"""
import os
import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # Streamlit menjalankan berkas ini dari app/ui, jadi root repositori ditambah manual
from app import predictor  # noqa: E402
from app.skema import validasi_baris as validasi  # noqa: E402


def _api_url() -> str:
    try:
        url = st.secrets.get("API_URL", "")
    except Exception:  # tidak ada secrets.toml: wajar saat dijalankan lokal
        url = ""
    return (url or os.getenv("API_URL", "")).rstrip("/")


API_URL = _api_url()
TIMEOUT = 60  # detik; layanan gratis yang sedang tidur butuh waktu untuk bangun

SENSOR = {  # kolom: (label, nilai contoh, langkah)
    "beban_pct": ("Beban (% daya nominal)", 76.0, 0.5),
    "arus_A": ("Arus (A)", 17.4, 0.1),
    "tegangan_V": ("Tegangan (V)", 380.0, 0.5),
    "suhu_belitan_C": ("Suhu belitan (°C)", 78.5, 0.5),
    "getaran_rms_mm_s": ("Getaran RMS (mm/s)", 5.6, 0.1),
    "kecepatan_rpm": ("Kecepatan (rpm)", 1462.0, 1.0),
}


def prediksi(rows: list[dict]) -> list[dict]:
    """rows sudah lolos validasi. Mode A: model lokal. Mode B: lewat API."""
    if not API_URL:
        return predictor.predict_rows(rows)
    r = requests.post(API_URL + "/predict/batch", json=rows, timeout=TIMEOUT)
    if r.status_code == 422:
        raise ValueError(f"Masukan ditolak API (422): {r.json().get('detail')}")
    r.raise_for_status()
    return r.json()


def info_model() -> dict:
    return predictor.load()[1]  # metadata.json ikut di repositori, jadi selalu tersedia untuk kedua mode


def tampilkan_hasil(hasil: dict):
    teks = f"### {hasil['status']}\n{hasil['saran']}"
    if hasil["status"] == "SEGERA GANTI":
        st.error(teks)
    elif hasil["status"] == "PESAN PENGGANTI SEKARANG":
        st.warning(teks)
    else:
        st.success(teks)
    k1, k2 = st.columns(2)
    k1.metric("Perkiraan sisa umur", f"{hasil['rul_hari']:.0f} hari")
    k2.metric("Kisaran 80 %", f"{hasil['rul_bawah']:.0f}–{hasil['rul_atas']:.0f} hari",
              help="Pada data validation, 8 dari 10 motor dengan tebakan sebesar ini rusak di dalam kisaran tersebut.")
    for c in hasil["catatan"]:
        st.info(c)


st.set_page_config(page_title="Sisa Umur Pakai Motor Induksi", layout="centered")
st.title("Sisa umur pakai motor induksi")
st.caption("Untuk perencana pemeliharaan: masukkan pembacaan sensor hari ini, dapatkan perkiraan sisa umur motor "
           "dan keputusan pemesanan motor pengganti.")

try:
    META = info_model()
except Exception as e:
    st.error(f"Model belum siap: {e}")
    st.stop()

FITUR = META["fitur_input"]
AMBANG = META["ambang_status"]
mode = f"Mode B · memanggil API {API_URL}" if API_URL else "Mode A · model dimuat langsung"
st.caption(f"{mode} · versi model {META['versi_model']} · pesan pengganti bila sisa umur ≤ {AMBANG['pesan_pengganti_maks_hari']} hari, "
           f"segera ganti bila ≤ {AMBANG['segera_ganti_maks_hari']} hari")

tab_satu, tab_batch, tab_tentang = st.tabs(["Satu motor", "Banyak motor (CSV)", "Tentang model"])

with tab_satu:
    with st.form("input"):
        c1, c2 = st.columns(2)
        tipe = c1.selectbox("Tipe motor", ["5.5kW", "11kW", "22kW"], index=1, help="Daya nominal pada pelat nama motor")
        hari = c2.number_input("Hari operasi", value=240, step=1, help="Jumlah hari sejak motor dipasang")
        nilai = {}
        for i, (kolom, (label, contoh, langkah)) in enumerate(SENSOR.items()):
            if i % 2 == 0:
                kiri, kanan = st.columns(2)  # satu baris = dua sensor, supaya urutannya tetap rapi di layar ponsel
            nilai[kolom] = (kiri if i % 2 == 0 else kanan).number_input(label, value=contoh, step=langkah, format="%.2f")
        mati = st.multiselect("Sensor yang sedang tidak tersedia (opsional)", list(SENSOR), format_func=lambda k: SENSOR[k][0],
                              placeholder="Pilih sensor yang mati",
                              help="Sensor yang dipilih di sini dikirim sebagai kosong. Model tetap menjawab, dengan catatan.")
        kirim = st.form_submit_button("Perkirakan sisa umur", type="primary", use_container_width=True)

    if kirim:
        row = {"tipe_motor": tipe, "hari_operasi": hari, **{k: (None if k in mati else v) for k, v in nilai.items()}}
        bersih, galat = validasi(row)
        if galat:
            st.error("Masukan tidak wajar, prediksi tidak dijalankan:\n\n" + "\n".join(f"- {g}" for g in galat))
        else:
            try:
                hasil = prediksi([bersih])[0]
            except Exception as e:
                st.error(f"Gagal memprediksi: {e}")
            else:
                tampilkan_hasil(hasil)
                with st.expander("Lihat request dan response JSON"):
                    st.json({"request": bersih, "response": hasil})

with tab_batch:
    st.write("Unggah CSV berisi satu baris per motor dengan kolom: " + ", ".join(f"`{k}`" for k in FITUR)
             + ". Kolom `motor_id` boleh disertakan sebagai pengenal.")
    contoh = ROOT / "data" / "contoh_batch.csv"
    if contoh.exists():
        st.download_button("Unduh contoh CSV", contoh.read_bytes(), "contoh_batch.csv", "text/csv")
    up = st.file_uploader("CSV", type="csv")
    if up is not None:
        try:
            df = pd.read_csv(up)
        except Exception as e:
            st.error(f"Berkas tidak bisa dibaca sebagai CSV: {e}")
            df = None
        if df is not None:
            kurang = [k for k in FITUR if k not in df.columns]
            if kurang:
                st.error(f"Kolom kurang: {kurang}")
            elif df.empty:
                st.error("Berkas tidak berisi baris data.")
            elif len(df) > 1000:
                st.error("Maksimal 1.000 baris per berkas.")
            else:
                data = df[FITUR].astype(object).where(df[FITUR].notna(), None).to_dict("records")  # NaN → None
                baris_baik, indeks_baik, ditolak = [], [], []
                for i, row in enumerate(data):
                    bersih, galat = validasi(row)
                    if galat:
                        ditolak.append({"baris ke-": i + 1, "alasan ditolak": "; ".join(galat)})
                    else:
                        baris_baik.append(bersih)
                        indeks_baik.append(i)
                if ditolak:
                    st.warning(f"{len(ditolak)} baris ditolak karena masukannya tidak wajar. Baris lain tetap diproses.")
                    st.dataframe(pd.DataFrame(ditolak), use_container_width=True, hide_index=True)
                if baris_baik:
                    try:
                        hasil = pd.DataFrame(prediksi(baris_baik))
                    except Exception as e:
                        st.error(f"Gagal memprediksi: {e}")
                    else:
                        hasil["catatan"] = hasil["catatan"].apply(" ".join)
                        masukan = df.iloc[indeks_baik].reset_index(drop=True)
                        pengenal = [k for k in masukan.columns if k not in FITUR]  # mis. motor_id
                        # pengenal dan hasil di kiri supaya langsung terlihat, masukan asli di kanan
                        out = pd.concat([masukan[pengenal], hasil[["status", "rul_hari", "rul_bawah", "rul_atas"]],
                                         masukan[FITUR], hasil[["catatan"]]], axis=1)
                        out = out.sort_values("rul_hari")  # yang paling mendesak di atas
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Segera ganti", int((out["status"] == "SEGERA GANTI").sum()))
                        m2.metric("Pesan pengganti sekarang", int((out["status"] == "PESAN PENGGANTI SEKARANG").sum()))
                        m3.metric("Aman", int((out["status"] == "AMAN").sum()))
                        st.dataframe(out, use_container_width=True, hide_index=True)
                        st.download_button("Unduh hasil", out.to_csv(index=False).encode(), "hasil_prediksi.csv", "text/csv")

with tab_tentang:
    uji, dasar = META["metrik_test"]["model"], META["metrik_test"]["baseline"]
    st.markdown(f"""
**Model** · {META['algoritma']}. Dilatih dari 240 motor *run-to-failure* dan diuji pada {META['pembagian_data']['motor_test']} motor
yang tidak pernah dilihat model.

| Galat rata-rata (MAE) pada data test | Baseline regresi linear | Model ini |
|---|---|---|
| Motor dengan sisa umur ≤ 60 hari | {dasar['MAE RUL≤60']:.1f} hari | **{uji['MAE RUL≤60']:.1f} hari** |
| Semua baris | {dasar['MAE semua baris']:.1f} hari | {uji['MAE semua baris']:.1f} hari |

**Arti status**

- **SEGERA GANTI**: sisa umur ≤ {AMBANG['segera_ganti_maks_hari']} hari. Pengiriman tercepat (2 minggu) kemungkinan tidak terkejar.
- **PESAN PENGGANTI SEKARANG**: sisa umur ≤ {AMBANG['pesan_pengganti_maks_hari']} hari. Ambang ini lebih besar daripada pengiriman terlama
  (4 minggu) karena sudah memuat margin untuk galat model.
- **AMAN**: di atas itu.

**Yang perlu diingat**

- Model paling tepat pada dua bulan terakhir umur motor. Selama motor masih sehat, sensor belum memberi tanda,
  sehingga angka di atas ±150 hari hanya berarti "masih lama".
- Tebakan dibuat dari pembacaan **satu hari**, jadi bisa naik-turun beberapa hari mengikuti derau sensor.
  Lihat arahnya selama beberapa hari sebelum membatalkan pesanan.
- Model hanya mengenal motor 5,5 kW, 11 kW, dan 22 kW yang belum pernah diperbaiki, pada tegangan 380 V.
""")
