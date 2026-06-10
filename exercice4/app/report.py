"""Modelo de datos del informe de calidad.

Vocabulario compartido por todos los modulos: el profiler PRODUCE un Report,
el store lo SERIALIZA a JSON, y la web lo RENDERIZA. Nadie mas conoce los
detalles internos del calculo: solo esta forma.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


# Pesos de las dimensiones en el score global (CONTEXT.md). Suman 100.
DIMENSION_WEIGHTS = {
    "completeness": 30,
    "validity": 30,
    "uniqueness": 20,
    "distribution": 20,
}


@dataclass
class DimensionScore:
    """Una de las cuatro dimensiones: su score 0-100 y su peso."""
    name: str
    score: float
    weight: int


@dataclass
class ColumnProfile:
    """Estadistica por columna. Casi todo aqui es 'estadistica'; algunos
    campos se promueven a warning segun los umbrales (ver profiler)."""
    name: str
    inferred_type: str          # integer | float | date | text
    n: int                      # filas totales
    missing_count: int
    missing_pct: float
    invalid_count: int
    invalid_pct: float
    distinct_count: int
    is_constant: bool           # >=95% un mismo valor (no faltante)
    outlier_count: int          # celdas IQR-outlier (solo numericas)
    outlier_pct: float
    # estadistica numerica opcional
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    top_values: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class Warning:
    """Un hallazgo promovido por encima de la estadistica."""
    kind: str                   # missing | invalid | outliers | constant | duplicate_rows
    message: str
    column: Optional[str] = None


@dataclass
class Report:
    filename: str
    created_at: str             # ISO-8601, lo sella la capa web/store
    n_rows: int
    n_cols: int
    overall_score: float
    duplicate_rows: int
    dimensions: list[DimensionScore]
    columns: list[ColumnProfile]
    warnings: list[Warning]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Report":
        return Report(
            filename=d["filename"],
            created_at=d["created_at"],
            n_rows=d["n_rows"],
            n_cols=d["n_cols"],
            overall_score=d["overall_score"],
            duplicate_rows=d["duplicate_rows"],
            dimensions=[DimensionScore(**x) for x in d["dimensions"]],
            columns=[ColumnProfile(**x) for x in d["columns"]],
            warnings=[Warning(**x) for x in d["warnings"]],
        )
