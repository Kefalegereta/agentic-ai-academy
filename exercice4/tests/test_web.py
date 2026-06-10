from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main


@pytest.fixture
def client(tmp_path, monkeypatch):
    # base de datos aislada por test
    db = tmp_path / "web.db"
    monkeypatch.setattr("app.store.DEFAULT_DB", db)
    main.init_db()
    return TestClient(main.app)


def test_upload_then_view_report(client):
    csv = b"a,b\n1,x\n2,y\n2,y\n"  # una fila duplicada
    resp = client.post("/upload", files={"file": ("demo.csv", csv, "text/csv")})
    assert resp.status_code == 200  # sigue el redirect 303 -> 200
    assert "Data quality report" in resp.text
    assert "demo.csv" in resp.text


def test_bad_upload_shows_error(client):
    resp = client.post("/upload", files={"file": ("empty.csv", b"", "text/csv")})
    assert resp.status_code == 400
    assert "vacio" in resp.text or "vacío" in resp.text


def test_history_lists_uploaded(client):
    client.post("/upload", files={"file": ("h.csv", b"a\n1\n2\n", "text/csv")})
    resp = client.get("/")
    assert "h.csv" in resp.text


def test_missing_report_404(client):
    resp = client.get("/reports/9999")
    assert resp.status_code == 404


def test_real_vgsales_if_present(client):
    path = Path(__file__).resolve().parent.parent / "vgsales.csv"
    if not path.exists():
        pytest.skip("vgsales.csv no presente")
    resp = client.post(
        "/upload", files={"file": ("vgsales.csv", path.read_bytes(), "text/csv")}
    )
    assert resp.status_code == 200
    assert "Data quality report" in resp.text
