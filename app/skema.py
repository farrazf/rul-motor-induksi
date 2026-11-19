"""Aturan validasi masukan. Dipakai FastAPI (app/api/main.py) dan Streamlit (app/ui/streamlit_app.py),
supaya batas "masukan yang mustahil" hanya ditulis di satu tempat."""
import math
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

SENSOR = ["beban_pct", "arus_A", "tegangan_V", "suhu_belitan_C", "getaran_rms_mm_s", "kecepatan_rpm"]


class InputMotor(BaseModel):
    """Pembacaan satu motor pada satu hari.

    Nilai di luar batas fisik ditolak (422) sebelum menyentuh model.
    Sensor boleh null (sensor mati): model tetap menjawab, dengan catatan.
    """
    tipe_motor: Literal["5.5kW", "11kW", "22kW"]
    hari_operasi: float = Field(ge=0, le=10_000, description="jumlah hari sejak motor dipasang")
    beban_pct: float | None = Field(ge=1, le=150, description="beban, % dari daya nominal")
    arus_A: float | None = Field(gt=0, le=100)
    tegangan_V: float | None = Field(ge=300, le=460)
    suhu_belitan_C: float | None = Field(ge=-20, le=473.15, description="°C; angka kelvin (253–473) dikonversi otomatis")
    getaran_rms_mm_s: float | None = Field(ge=0, le=50)
    kecepatan_rpm: float | None = Field(ge=1000, le=1500, description="motor 4 kutub 50 Hz: di bawah 1500 rpm")

    @field_validator("tipe_motor", mode="before")
    @classmethod
    def rapikan_tipe(cls, v):
        """'22KW', '11 kW', '5,5 kW' diterima dan dirapikan."""
        if isinstance(v, str):
            return v.replace(" ", "").replace(",", ".").lower().replace("kw", "kW")
        return v

    @field_validator(*SENSOR, mode="before")
    @classmethod
    def nan_jadi_kosong(cls, v):
        """Sel kosong pada CSV terbaca sebagai NaN; perlakukan sebagai sensor kosong."""
        if isinstance(v, float) and math.isnan(v):
            return None
        return v

    @field_validator("suhu_belitan_C")
    @classmethod
    def suhu_masuk_akal(cls, v):
        if v is not None and 200 < v < 253:
            raise ValueError("suhu 200–253 tidak masuk akal, baik sebagai °C maupun kelvin")
        return v

    model_config = {"json_schema_extra": {"examples": [{
        "tipe_motor": "11kW", "hari_operasi": 240, "beban_pct": 76.0, "arus_A": 17.4, "tegangan_V": 380.0,
        "suhu_belitan_C": 78.5, "getaran_rms_mm_s": 5.6, "kecepatan_rpm": 1462}]}}


class Prediksi(BaseModel):
    rul_hari: float = Field(description="perkiraan sisa umur pakai (hari)")
    rul_bawah: float = Field(description="batas bawah kisaran 80 %")
    rul_atas: float = Field(description="batas atas kisaran 80 %")
    status: Literal["SEGERA GANTI", "PESAN PENGGANTI SEKARANG", "AMAN"]
    saran: str
    catatan: list[str] = Field(description="peringatan tentang masukan, mis. sensor kosong atau di luar rentang data latih")
    versi_model: str
    latency_ms: float


def pesan_galat(galat: list[dict]) -> list[str]:
    """Ubah daftar galat validasi pydantic (hasil .errors()) menjadi kalimat bahasa Indonesia untuk pengguna."""
    pesan = []
    for g in galat:
        kolom = str(g["loc"][-1]) if g["loc"] else "masukan"
        jenis, ctx = g["type"], g.get("ctx", {})
        if jenis == "missing" or (g.get("input") is None and kolom == "hari_operasi"):
            isi = "wajib diisi"
        elif jenis in ("greater_than_equal", "greater_than"):
            isi = f"harus {'≥' if jenis.endswith('equal') else '>'} {ctx.get('ge', ctx.get('gt'))}"
        elif jenis in ("less_than_equal", "less_than"):
            isi = f"harus {'≤' if jenis.endswith('equal') else '<'} {ctx.get('le', ctx.get('lt'))}"
        elif jenis == "literal_error":
            isi = "harus salah satu dari 5.5kW, 11kW, 22kW"
        elif jenis in ("float_parsing", "float_type", "int_parsing"):
            isi = "harus berupa angka"
        elif jenis == "value_error":
            isi = str(ctx.get("error", g["msg"]))
        else:
            isi = g["msg"]
        pesan.append(f"{kolom}: {isi} (diterima: {g.get('input')!r})")
    return pesan


def validasi_baris(row: dict) -> tuple[dict | None, list[str]]:
    """Kembalikan (baris bersih, []) bila wajar, atau (None, daftar pesan galat) bila tidak."""
    try:
        return InputMotor(**row).model_dump(), []
    except ValidationError as e:
        return None, pesan_galat(e.errors())
