"""Muat artifact satu kali, lalu prediksi. Dipakai FastAPI (app/api/main.py) dan Streamlit mode A (app/ui/streamlit_app.py)."""
import json
import sys
import time
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
# model.joblib menyimpan rujukan ke src.features.tambah_fitur, jadi root repositori harus bisa di-import
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.features import BATAS_KELVIN, tambah_fitur  # noqa: E402

ARTIFACT_DIR = ROOT / "artifacts"

SARAN = {
    "SEGERA GANTI": "Sisa umur diperkirakan lebih pendek daripada pengiriman tercepat (2 minggu). "
                    "Ganti dengan stok cadangan atau minta pengiriman kilat, dan siapkan jadwal henti.",
    "PESAN PENGGANTI SEKARANG": "Pesan motor pengganti hari ini. Dengan pengiriman 2–4 minggu, motor baru masih tiba sebelum motor lama rusak.",
    "AMAN": "Belum perlu memesan. Lanjutkan pemantauan harian.",
}
RASIO_ARUS_WAJAR = (1.5, 2.5)   # ampere per kW beban; data latih berada di 1,6–2,4
RUL_SEHAT = 150                 # di atas ini sensor belum menunjukkan tanda kerusakan (lihat notebook, EDA 5.2)


@lru_cache(maxsize=1)
def load():
    """(model, metadata). lru_cache = dimuat sekali per proses, bukan setiap permintaan."""
    model_path, meta_path = ARTIFACT_DIR / "model.joblib", ARTIFACT_DIR / "metadata.json"
    if not model_path.exists():
        raise FileNotFoundError(f"{model_path} tidak ada. Jalankan notebook sampai selesai, lalu commit folder artifacts/.")
    return joblib.load(model_path), json.loads(meta_path.read_text())


def status_dari_rul(rul: float, ambang: dict) -> str:
    if rul <= ambang["segera_ganti_maks_hari"]:
        return "SEGERA GANTI"
    if rul <= ambang["pesan_pengganti_maks_hari"]:
        return "PESAN PENGGANTI SEKARANG"
    return "AMAN"


def kisaran(rul: float, tabel: list[dict]) -> tuple[float, float]:
    """Kisaran 80 % dari galat pada data validation, sesuai besar tebakannya."""
    for baris in tabel:
        if rul <= baris["tebakan_maks"]:
            return max(0.0, rul + baris["bawah"]), rul + baris["atas"]
    return max(0.0, rul + tabel[-1]["bawah"]), rul + tabel[-1]["atas"]


def catatan_masukan(asli: dict, fitur: pd.Series, rul: float, meta: dict) -> list[str]:
    """Peringatan untuk pengguna. Masukan tetap diprediksi, tetapi pengguna diberi tahu kapan hasilnya perlu diragukan."""
    catatan = []
    suhu = asli.get("suhu_belitan_C")
    if suhu is not None and suhu > BATAS_KELVIN:
        catatan.append(f"Suhu {suhu:g} dianggap kelvin dan dikonversi menjadi {suhu - 273.15:.1f} °C.")
    kosong = [k for k in meta["fitur_input"] if k not in ("tipe_motor", "hari_operasi") and pd.isna(fitur.get(k))]
    if kosong:
        catatan.append("Sensor kosong: " + ", ".join(kosong) + ". Model tetap menjawab, tetapi tebakannya kurang tepat.")
    if "getaran_rms_mm_s" in kosong:
        catatan.append("Getaran adalah sensor paling penting bagi model. Tanpa getaran, jangan mengambil keputusan dari angka ini saja.")
    for kolom, (bawah, atas) in meta["rentang_data_latih"].items():
        nilai = fitur.get(kolom)
        if pd.notna(nilai) and not (bawah <= nilai <= atas):
            catatan.append(f"{kolom} = {nilai:g} berada di luar rentang data latih ({bawah:g}–{atas:g}). Model belum pernah melihat kondisi ini.")
    rasio = fitur.get("rasio_arus")
    if pd.notna(rasio) and not (RASIO_ARUS_WAJAR[0] <= rasio <= RASIO_ARUS_WAJAR[1]):
        catatan.append("Arus tidak sesuai dengan tipe motor dan beban yang dimasukkan. Periksa tipe motor atau sensor arus.")
    if rul > RUL_SEHAT:
        catatan.append(f"Sensor belum menunjukkan tanda kerusakan. Untuk motor sehat, angka di atas ±{RUL_SEHAT} hari hanyalah perkiraan kasar.")
    return catatan


def predict_rows(rows: list[dict]) -> list[dict]:
    """Prediksi beberapa baris sekaligus. Tiap baris berisi kolom fitur_input dari metadata (sudah lolos validasi skema)."""
    model, meta = load()
    mulai = time.perf_counter()
    X = pd.DataFrame(rows)[meta["fitur_input"]]
    tebakan = model.predict(X).clip(min=0)
    latency = round((time.perf_counter() - mulai) * 1000, 1)
    fitur = pd.concat([X[["tipe_motor"]].reset_index(drop=True), tambah_fitur(X).reset_index(drop=True)], axis=1)

    hasil = []
    for i, rul in enumerate(tebakan):
        rul = float(rul)
        bawah, atas = kisaran(rul, meta["kisaran_galat_80persen"])
        status = status_dari_rul(rul, meta["ambang_status"])
        hasil.append({
            "rul_hari": round(rul, 1),
            "rul_bawah": round(bawah, 1),
            "rul_atas": round(atas, 1),
            "status": status,
            "saran": SARAN[status],
            "catatan": catatan_masukan(rows[i], fitur.iloc[i], rul, meta),
            "versi_model": meta["versi_model"],
            "latency_ms": latency,
        })
    return hasil


def predict_one(row: dict) -> dict:
    return predict_rows([row])[0]
