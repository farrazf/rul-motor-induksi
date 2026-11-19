"""FastAPI untuk model sisa umur pakai (RUL) motor induksi.

Jalankan dari root repositori:
    uvicorn app.api.main:app --reload
Lalu buka http://127.0.0.1:8000 (halaman web) atau http://127.0.0.1:8000/docs (dokumentasi API).
"""
import json
import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))  # supaya `app` dan `src` bisa di-import
from app import predictor  # noqa: E402
from app.skema import InputMotor, Prediksi, pesan_galat, validasi_baris  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("prediksi")

MAX_BATCH = 1000
HALAMAN_WEB = ROOT / "app" / "web" / "index.html"
CONTOH_CSV = ROOT / "data" / "contoh_batch.csv"


@asynccontextmanager
async def lifespan(app: FastAPI):
    predictor.load()  # model dimuat sekali saat server menyala, bukan setiap permintaan
    yield


app = FastAPI(title="Sisa Umur Pakai Motor Induksi", version="1.0.0", lifespan=lifespan,
              description="Masukan: tipe motor, umur motor, dan pembacaan sensor hari ini. Keluaran: perkiraan sisa umur (hari) dan status.")


@app.exception_handler(RequestValidationError)
async def masukan_ditolak(request: Request, exc: RequestValidationError):
    """Masukan mustahil -> 422. `detail` adalah format baku FastAPI, `pesan` versi bahasa Indonesia untuk ditampilkan."""
    galat = exc.errors()
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(galat, custom_encoder={Exception: str}),
                                                  "pesan": pesan_galat(galat)})


def _log(inputs: list[dict], outputs: list[dict]):
    """Setiap prediksi dicatat (masukan + keluaran) supaya bisa diaudit dan dipantau perubahannya."""
    for x, y in zip(inputs, outputs):
        log.info("prediksi %s", json.dumps({"input": x, "output": y, "ts": time.time()}))


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def beranda():
    """Halaman web untuk perencana pemeliharaan (formulir + unggah CSV). Halaman ini memanggil endpoint di bawah."""
    return HALAMAN_WEB.read_text(encoding="utf-8")


@app.get("/contoh.csv", include_in_schema=False)
def contoh_csv():
    """Contoh berkas untuk fitur unggah CSV."""
    return FileResponse(CONTOH_CSV, media_type="text/csv", filename="contoh_batch.csv")


@app.get("/health")
def health():
    _, meta = predictor.load()
    return {"status": "ok", "versi_model": meta["versi_model"], "ambang_status": meta["ambang_status"],
            "fitur_input": meta["fitur_input"], "metrik_test": meta["metrik_test"],
            "motor_test": meta["pembagian_data"]["motor_test"]}


@app.post("/predict", response_model=Prediksi)
def predict(x: InputMotor):
    """Satu motor: JSON masuk, prediksi keluar. Masukan yang mustahil ditolak dengan kode 422."""
    row = x.model_dump()
    hasil = predictor.predict_one(row)
    _log([row], [hasil])
    return hasil


@app.post("/predict/batch", response_model=list[Prediksi])
def predict_batch(xs: list[InputMotor]):
    """Banyak motor, ketat: satu baris mustahil membuat seluruh permintaan ditolak (422)."""
    if len(xs) > MAX_BATCH:
        raise HTTPException(413, f"Maksimal {MAX_BATCH} baris per permintaan.")
    rows = [x.model_dump() for x in xs]
    if not rows:
        return []
    hasil = predictor.predict_rows(rows)
    _log(rows, hasil)
    return hasil


@app.post("/predict/tabel")
def predict_tabel(rows: list[dict]):
    """Banyak motor, longgar (dipakai fitur unggah CSV): tiap baris diperiksa sendiri-sendiri.
    Baris yang mustahil dilaporkan beserta alasannya, baris lain tetap diprediksi."""
    if len(rows) > MAX_BATCH:
        raise HTTPException(413, f"Maksimal {MAX_BATCH} baris per permintaan.")
    jawaban, baik, posisi = [], [], []
    for i, row in enumerate(rows):
        bersih, galat = validasi_baris(row)
        jawaban.append({"baris": i + 1, "ok": not galat, "galat": galat, "hasil": None})
        if bersih is not None:
            baik.append(bersih)
            posisi.append(i)
    if baik:
        hasil = predictor.predict_rows(baik)
        _log(baik, hasil)
        for i, h in zip(posisi, hasil):
            jawaban[i]["hasil"] = h
    return jawaban
