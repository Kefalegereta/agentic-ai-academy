"""Capa web: subir CSV -> perfilar -> guardar -> informe HTML, con historico.

Esta capa es deliberadamente fina: orquesta ingest -> profiler -> store y
delega todo el calculo en los modulos profundos.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .ingest import IngestError, parse_csv
from .profiler import profile
from .store import init_db, save_report, list_reports, get_report

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Data Quality Checker", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def _score_band(score: float) -> str:
    if score >= 90:
        return "good"
    if score >= 75:
        return "warn"
    return "bad"


templates.env.filters["band"] = _score_band


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"reports": list_reports(), "error": None}
    )


@app.post("/upload")
async def upload(request: Request, file: UploadFile = File(...)):
    data = await file.read()
    try:
        df = parse_csv(data, file.filename or "uploaded.csv")
        report = profile(df, file.filename or "uploaded.csv")
    except IngestError as exc:
        return templates.TemplateResponse(
            request, "index.html",
            {"reports": list_reports(), "error": str(exc)},
            status_code=400,
        )
    report_id = save_report(report)
    return RedirectResponse(url=f"/reports/{report_id}", status_code=303)


@app.get("/reports/{report_id}", response_class=HTMLResponse)
def report_view(request: Request, report_id: int):
    report = get_report(report_id)
    if report is None:
        return templates.TemplateResponse(
            request, "index.html",
            {"reports": list_reports(),
             "error": f"No existe el informe #{report_id}."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request, "report.html", {"r": report, "report_id": report_id}
    )
