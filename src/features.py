"""Pembersihan data dan pembuatan fitur untuk prediksi sisa umur pakai (RUL) motor induksi.

Berkas ini dipakai di DUA tempat: notebook pelatihan dan aplikasi (API/Streamlit).
Karena fungsinya sama persis, data saat prediksi diperlakukan sama dengan data saat pelatihan.
Jangan mengubah rumus di sini tanpa melatih ulang model.
"""
import numpy as np
import pandas as pd

KOLOM_SENSOR = ["beban_pct", "arus_A", "tegangan_V", "suhu_belitan_C", "getaran_rms_mm_s", "kecepatan_rpm"]
FITUR_INPUT = ["tipe_motor", "hari_operasi"] + KOLOM_SENSOR  # kolom yang diminta dari pengguna
TARGET = "rul_hari"

DAYA_KW = {"5.5kW": 5.5, "11kW": 11.0, "22kW": 22.0}  # daya nominal tiap tipe motor
RPM_SINKRON = 1500.0   # motor 4 kutub pada listrik 50 Hz
BATAS_KELVIN = 200.0   # belitan motor tidak mungkin > 200 °C, jadi angka di atas ini pasti kelvin
BEBAN_ACUAN = 75.0     # beban rata-rata armada (%), titik acuan koreksi beban

# Pengaruh beban terhadap sensor pada motor SEHAT (dihitung di notebook, bagian EDA, dari data train saja).
# Contoh: setiap beban naik 1 %, suhu belitan naik sekitar 0,33 °C walaupun motornya sehat.
KOEF_SUHU = 0.33       # °C per 1 % beban
KOEF_RPM = -0.11       # rpm per 1 % beban
KOEF_GETARAN = 0.009   # mm/s per 1 % beban

FITUR_MODEL = [
    "hari_operasi", "daya_kW",
    "beban_pct", "arus_A", "tegangan_V", "suhu_belitan_C", "getaran_rms_mm_s", "kecepatan_rpm",
    "rasio_arus", "slip_pct", "suhu_koreksi", "rpm_koreksi", "getaran_koreksi",
]


def rapikan_tipe(tipe: pd.Series) -> pd.Series:
    """Samakan penulisan tipe motor: '22KW', '11 kW', '5,5 kW' -> '22kW', '11kW', '5.5kW'.
    Tipe yang tidak dikenal menjadi kosong (NA)."""
    t = tipe.astype("string").str.replace(" ", "").str.replace(",", ".").str.lower().str.replace("kw", "kW")
    return t.where(t.isin(list(DAYA_KW)))


def rapikan_sensor(df: pd.DataFrame) -> pd.DataFrame:
    """Perbaikan per baris yang juga berlaku saat prediksi:
    - semua sensor dipaksa menjadi angka (teks/None -> NaN),
    - suhu belitan dalam kelvin (Plant Purwakarta) diubah ke °C,
    - getaran negatif (kode galat sensor -1) dianggap kosong."""
    df = df.copy()
    for kolom in KOLOM_SENSOR + ["hari_operasi"]:
        df[kolom] = pd.to_numeric(df[kolom], errors="coerce").astype("float64")
    kelvin = df["suhu_belitan_C"] > BATAS_KELVIN
    df.loc[kelvin, "suhu_belitan_C"] = df.loc[kelvin, "suhu_belitan_C"] - 273.15
    df.loc[df["getaran_rms_mm_s"] <= 0, "getaran_rms_mm_s"] = np.nan
    return df


def bersihkan_data(df: pd.DataFrame) -> pd.DataFrame:
    """Pembersihan data mentah klien (hanya dipakai saat pelatihan karena butuh riwayat per motor)."""
    df = df.copy()
    # 1. ID motor ditulis tidak seragam ('m-001', 'M001', 'M-001 '): ambil angkanya, tulis ulang 'M-001'
    nomor = df["motor_id"].astype("string").str.extract(r"(\d+)")[0].astype(int)
    df["motor_id"] = "M-" + nomor.astype(str).str.zfill(3)
    # 2. Tipe motor ditulis tidak seragam
    df["tipe_motor"] = rapikan_tipe(df["tipe_motor"])
    # 3. Baris kembar (motor dan hari yang sama tercatat dua kali)
    df = df.drop_duplicates(subset=["motor_id", "hari_operasi"], keep="first")
    # 4. Tipe motor tidak mungkin berubah-ubah: pakai tipe yang paling sering muncul pada motor itu
    df["tipe_motor"] = df.groupby("motor_id")["tipe_motor"].transform(lambda s: s.mode().iloc[0])
    # 5. Satuan suhu dan kode galat sensor
    df = rapikan_sensor(df)
    df["hari_operasi"] = df["hari_operasi"].astype(int)
    return df.sort_values(["motor_id", "hari_operasi"]).reset_index(drop=True)


def sensor_asli(df: pd.DataFrame) -> pd.DataFrame:
    """Masukan untuk baseline wajib: enam sensor asli saja, tanpa fitur buatan."""
    return rapikan_sensor(df)[KOLOM_SENSOR]


def tambah_fitur(df: pd.DataFrame) -> pd.DataFrame:
    """Ubah kolom masukan (FITUR_INPUT) menjadi fitur model (FITUR_MODEL).

    Ide utamanya: sensor motor berubah karena DUA hal, yaitu beban hari itu dan kerusakan.
    Fitur 'koreksi' membuang pengaruh beban supaya yang tersisa adalah tanda kerusakan.
    """
    df = rapikan_sensor(df)
    df["daya_kW"] = rapikan_tipe(df["tipe_motor"]).map(DAYA_KW).astype("float64")
    # arus per kW beban: motor 5,5 kW dan 22 kW jadi bisa dibandingkan; naik saat motor makin tidak efisien
    df["rasio_arus"] = df["arus_A"] / (df["daya_kW"] * df["beban_pct"] / 100)
    # slip: seberapa jauh putaran tertinggal dari putaran sinkron
    df["slip_pct"] = (RPM_SINKRON - df["kecepatan_rpm"]) / RPM_SINKRON * 100
    # sensor seandainya motor bekerja pada beban acuan 75 %
    selisih_beban = df["beban_pct"] - BEBAN_ACUAN
    df["suhu_koreksi"] = df["suhu_belitan_C"] - KOEF_SUHU * selisih_beban
    df["rpm_koreksi"] = df["kecepatan_rpm"] - KOEF_RPM * selisih_beban
    df["getaran_koreksi"] = df["getaran_rms_mm_s"] - KOEF_GETARAN * selisih_beban
    # pembagian dengan beban 0 menghasilkan tak hingga; model hanya mengerti angka atau kosong
    return df[FITUR_MODEL].replace([np.inf, -np.inf], np.nan)
