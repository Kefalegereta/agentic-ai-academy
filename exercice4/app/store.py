"""Persistencia de informes en SQLite (CONTEXT.md).

Guarda el informe computado como JSON + metadatos para listarlo y reabrirlo.
NO guarda el CSV crudo. Sin comparacion entre runs (eso seria v2).
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .report import Report

DEFAULT_DB = Path(__file__).resolve().parent.parent / "reports.db"


@dataclass
class ReportSummary:
    """Fila del historico: lo justo para la lista, sin cargar el JSON entero."""
    id: int
    filename: str
    created_at: str
    n_rows: int
    n_cols: int
    overall_score: float


def _connect(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str = DEFAULT_DB) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                filename     TEXT    NOT NULL,
                created_at   TEXT    NOT NULL,
                n_rows       INTEGER NOT NULL,
                n_cols       INTEGER NOT NULL,
                overall_score REAL   NOT NULL,
                report_json  TEXT    NOT NULL
            )
            """
        )


def save_report(report: Report, db_path: Path | str = DEFAULT_DB) -> int:
    with _connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO reports
               (filename, created_at, n_rows, n_cols, overall_score, report_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                report.filename,
                report.created_at,
                report.n_rows,
                report.n_cols,
                report.overall_score,
                json.dumps(report.to_dict()),
            ),
        )
        return int(cur.lastrowid)


def list_reports(db_path: Path | str = DEFAULT_DB) -> list[ReportSummary]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """SELECT id, filename, created_at, n_rows, n_cols, overall_score
               FROM reports ORDER BY id DESC"""
        ).fetchall()
    return [ReportSummary(**dict(r)) for r in rows]


def get_report(report_id: int, db_path: Path | str = DEFAULT_DB) -> Report | None:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT report_json FROM reports WHERE id = ?", (report_id,)
        ).fetchone()
    if row is None:
        return None
    return Report.from_dict(json.loads(row["report_json"]))
