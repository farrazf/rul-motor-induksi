"""Uji asap API: masukan normal, ekstrem, kotor, dan tidak valid. Jalankan dari root repositori: pytest -q"""
import pytest
from fastapi.testclient import TestClient

from app.api.main import app

# motor 11 kW yang sudah menunjukkan tanda kerusakan (getaran tinggi, suhu naik, putaran turun)
MENDEKATI_RUSAK = {
    "tipe_motor": "11kW", "hari_operasi": 240, "beban_pct": 76.0, "arus_A": 17.4, "tegangan_V": 380.0,
    "suhu_belitan_C": 78.5, "getaran_rms_mm_s": 5.6, "kecepatan_rpm": 1462,
}
SEHAT = {**MENDEKATI_RUSAK, "hari_operasi": 30, "arus_A": 16.4, "suhu_belitan_C": 59.5, "getaran_rms_mm_s": 2.05, "kecepatan_rpm": 1475}
HAMPIR_MATI = {**MENDEKATI_RUSAK, "hari_operasi": 280, "arus_A": 17.9, "suhu_belitan_C": 84.0, "getaran_rms_mm_s": 7.3, "kecepatan_rpm": 1458}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # `with` menjalankan startup: model dimuat sekali
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok" and len(r.json()["fitur_input"]) == 8


def test_bentuk_jawaban(client):
    r = client.post("/predict", json=MENDEKATI_RUSAK)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["rul_hari"] >= 0
    assert body["rul_bawah"] <= body["rul_hari"] <= body["rul_atas"]
    assert body["status"] in ("SEGERA GANTI", "PESAN PENGGANTI SEKARANG", "AMAN")


def test_urutan_status_masuk_akal(client):
    sehat = client.post("/predict", json=SEHAT).json()
    dekat = client.post("/predict", json=MENDEKATI_RUSAK).json()
    mati = client.post("/predict", json=HAMPIR_MATI).json()
    assert sehat["status"] == "AMAN"
    assert mati["status"] == "SEGERA GANTI"
    assert sehat["rul_hari"] > dekat["rul_hari"] > mati["rul_hari"]


def test_suhu_kelvin_sama_dengan_celsius(client):
    c = client.post("/predict", json=MENDEKATI_RUSAK).json()
    k = client.post("/predict", json={**MENDEKATI_RUSAK, "suhu_belitan_C": 78.5 + 273.15}).json()
    assert k["rul_hari"] == pytest.approx(c["rul_hari"], abs=0.1)
    assert any("kelvin" in catatan for catatan in k["catatan"])


def test_tipe_ditulis_tidak_baku_dirapikan(client):
    for tulisan in ["11KW", "11 kW", " 11kw "]:
        assert client.post("/predict", json={**MENDEKATI_RUSAK, "tipe_motor": tulisan}).status_code == 200
    assert client.post("/predict", json={**MENDEKATI_RUSAK, "tipe_motor": "5,5 kW", "arus_A": 8.7}).status_code == 200


def test_sensor_mati_tetap_dijawab_dengan_catatan(client):
    r = client.post("/predict", json={**MENDEKATI_RUSAK, "arus_A": None, "getaran_rms_mm_s": None})
    assert r.status_code == 200
    assert any("Sensor kosong" in catatan for catatan in r.json()["catatan"])


def test_ekstrem_tapi_mungkin_tetap_dijawab_dengan_peringatan(client):
    r = client.post("/predict", json={**MENDEKATI_RUSAK, "getaran_rms_mm_s": 30, "suhu_belitan_C": 150, "hari_operasi": 3000})
    assert r.status_code == 200
    assert any("di luar rentang data latih" in catatan for catatan in r.json()["catatan"])


def test_tipe_tidak_cocok_dengan_arus_diberi_peringatan(client):
    r = client.post("/predict", json={**MENDEKATI_RUSAK, "tipe_motor": "22kW"})  # arus 17 A terlalu kecil untuk 22 kW
    assert r.status_code == 200
    assert any("Arus tidak sesuai" in catatan for catatan in r.json()["catatan"])


@pytest.mark.parametrize("field,value", [
    ("tipe_motor", "7.5kW"), ("hari_operasi", -5), ("beban_pct", 0), ("arus_A", -3), ("tegangan_V", 0),
    ("suhu_belitan_C", 1000), ("suhu_belitan_C", 230), ("getaran_rms_mm_s", -1), ("kecepatan_rpm", 3000),
    ("kecepatan_rpm", "cepat"), ("hari_operasi", None),
])
def test_masukan_mustahil_ditolak_422(client, field, value):
    r = client.post("/predict", json={**MENDEKATI_RUSAK, field: value})
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"][-1] == field


def test_kolom_hilang_ditolak(client):
    body = {k: v for k, v in MENDEKATI_RUSAK.items() if k != "getaran_rms_mm_s"}
    assert client.post("/predict", json=body).status_code == 422


def test_badan_kosong_ditolak(client):
    assert client.post("/predict", json={}).status_code == 422


def test_batch(client):
    r = client.post("/predict/batch", json=[SEHAT, MENDEKATI_RUSAK, HAMPIR_MATI])
    assert r.status_code == 200 and len(r.json()) == 3
    assert client.post("/predict/batch", json=[]).json() == []
    assert client.post("/predict/batch", json=[SEHAT, {**SEHAT, "arus_A": -1}]).status_code == 422


def test_pesan_galat_bahasa_indonesia(client):
    r = client.post("/predict", json={**MENDEKATI_RUSAK, "getaran_rms_mm_s": -5, "kecepatan_rpm": 3000})
    pesan = r.json()["pesan"]
    assert r.status_code == 422 and len(pesan) == 2
    assert pesan[0].startswith("getaran_rms_mm_s: harus ≥ 0") and pesan[1].startswith("kecepatan_rpm: harus ≤ 1500")


def test_tabel_baris_buruk_tidak_menggagalkan_baris_lain(client):
    """Dipakai fitur unggah CSV: baris mustahil dilaporkan, baris lain tetap diprediksi."""
    rows = [SEHAT, {**SEHAT, "arus_A": -1}, {**HAMPIR_MATI, "arus_A": None}, {"tipe_motor": "11kW"}, {**SEHAT, "kecepatan_rpm": "cepat"}]
    r = client.post("/predict/tabel", json=rows)
    j = r.json()
    assert r.status_code == 200 and [x["ok"] for x in j] == [True, False, True, False, False]
    assert j[0]["hasil"]["status"] == "AMAN" and j[2]["hasil"]["status"] == "SEGERA GANTI"
    assert j[1]["hasil"] is None and j[1]["galat"][0].startswith("arus_A")
    assert len(j[3]["galat"]) == 7  # tujuh kolom wajib tidak diisi


def test_halaman_web_dan_contoh_csv(client):
    r = client.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"] and "Sisa Umur Pakai Motor" in r.text
    r = client.get("/contoh.csv")
    assert r.status_code == 200 and r.text.startswith("motor_id,")
