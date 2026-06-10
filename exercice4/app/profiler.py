"""Modulo profundo: perfila un DataFrame y produce un Report.

Interfaz pequena (`profile`), comportamiento rico detras. Implementa al pie de
la letra las reglas de CONTEXT.md:

- Faltante  = vacio/espacios o token nulo de una lista fija (case-insensitive).
  Se normaliza ANTES de inferir tipo, asi completitud y validez no se solapan.
- Tipo      = dominante por columna: si >=90% de los NO faltantes parsean como
  numerico/fecha, la columna ES ese tipo; si no, es texto.
- Invalido  = celda no faltante que no parsea como el tipo inferido (solo tipo).
- Unicidad  = filas exactamente duplicadas.
- Distrib.  = outliers IQR (1.5x) en numericas + columnas constantes (>=95%).
- Sub-score = 100 x (1 - tasa_de_defecto), lineal, para las cuatro.
- Global    = media ponderada 30/30/20/20.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from .report import (
    DIMENSION_WEIGHTS,
    ColumnProfile,
    DimensionScore,
    Report,
    Warning,
)

# --- constantes de reglas (CONTEXT.md) -------------------------------------
NULL_TOKENS = {"", "n/a", "na", "null", "nan", "none", "-"}
TYPE_PARSE_THRESHOLD = 0.90       # >=90% parsean -> ese tipo
CONSTANT_THRESHOLD = 0.95         # >=95% un valor -> constante/casi-constante
IQR_FACTOR = 1.5
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y")

# umbrales de warning (porcentajes 0-100)
WARN_MISSING_PCT = 5.0
WARN_INVALID_PCT = 5.0
WARN_OUTLIER_PCT = 1.0


# --- parsers de celda -------------------------------------------------------
def _is_int(v: str) -> bool:
    try:
        int(v.strip())
        return True
    except (ValueError, AttributeError):
        return False


def _is_float(v: str) -> bool:
    try:
        float(v.strip())
        return True
    except (ValueError, AttributeError):
        return False


def _is_date(v: str) -> bool:
    s = v.strip()
    for fmt in DATE_FORMATS:
        try:
            datetime.strptime(s, fmt)
            return True
        except ValueError:
            continue
    return False


def _missing_mask(series: pd.Series) -> pd.Series:
    norm = series.fillna("").astype(str).str.strip().str.lower()
    return norm.isin(NULL_TOKENS)


def _infer_type(non_missing: pd.Series) -> str:
    """Tipo dominante entre integer | float | date | text."""
    if len(non_missing) == 0:
        return "text"
    n = len(non_missing)
    int_rate = non_missing.map(_is_int).sum() / n
    if int_rate >= TYPE_PARSE_THRESHOLD:
        return "integer"
    float_rate = non_missing.map(_is_float).sum() / n
    if float_rate >= TYPE_PARSE_THRESHOLD:
        return "float"
    date_rate = non_missing.map(_is_date).sum() / n
    if date_rate >= TYPE_PARSE_THRESHOLD:
        return "date"
    return "text"


def _invalid_mask(non_missing: pd.Series, dtype: str) -> pd.Series:
    if dtype == "integer":
        return ~non_missing.map(_is_int)
    if dtype == "float":
        return ~non_missing.map(_is_float)
    if dtype == "date":
        return ~non_missing.map(_is_date)
    return pd.Series(False, index=non_missing.index)  # text: nunca invalido


def _profile_column(series: pd.Series, name: str) -> tuple[ColumnProfile, int]:
    """Devuelve (perfil, celdas_numericas_no_faltantes) para agregados."""
    n = len(series)
    miss = _missing_mask(series)
    missing_count = int(miss.sum())
    non_missing = series[~miss].astype(str).str.strip()

    dtype = _infer_type(non_missing)
    inval = _invalid_mask(non_missing, dtype)
    invalid_count = int(inval.sum())

    distinct_count = int(non_missing.nunique())
    vc = non_missing.value_counts()
    top_values = [(str(k), int(v)) for k, v in vc.head(5).items()]
    nm = len(non_missing)
    is_constant = nm > 0 and (vc.iloc[0] / nm) >= CONSTANT_THRESHOLD

    # estadistica / outliers solo para numericas (valores validos)
    cmin = cmax = cmean = cstd = None
    outlier_count = 0
    numeric_cells = 0
    if dtype in ("integer", "float"):
        valid_vals = pd.to_numeric(non_missing[~inval], errors="coerce").dropna()
        numeric_cells = len(valid_vals)
        if numeric_cells > 0:
            cmin, cmax = float(valid_vals.min()), float(valid_vals.max())
            cmean = float(valid_vals.mean())
            cstd = float(valid_vals.std(ddof=0))
            q1, q3 = valid_vals.quantile(0.25), valid_vals.quantile(0.75)
            iqr = q3 - q1
            # iqr==0 (columna casi-constante): los pocos valores distintos del
            # nucleo caen fuera de [q1, q3] y se marcan como outliers.
            lo, hi = q1 - IQR_FACTOR * iqr, q3 + IQR_FACTOR * iqr
            outlier_count = int(((valid_vals < lo) | (valid_vals > hi)).sum())

    profile = ColumnProfile(
        name=name,
        inferred_type=dtype,
        n=n,
        missing_count=missing_count,
        missing_pct=round(100 * missing_count / n, 2) if n else 0.0,
        invalid_count=invalid_count,
        invalid_pct=round(100 * invalid_count / nm, 2) if nm else 0.0,
        distinct_count=distinct_count,
        is_constant=bool(is_constant),
        outlier_count=outlier_count,
        outlier_pct=round(100 * outlier_count / n, 2) if n else 0.0,
        min=cmin, max=cmax, mean=cmean, std=cstd,
        top_values=top_values,
    )
    return profile, numeric_cells


def _score(defect_rate: float) -> float:
    return round(100 * (1 - defect_rate), 2)


def profile(df: pd.DataFrame, filename: str, created_at: str | None = None) -> Report:
    n_rows, n_cols = df.shape
    total_cells = n_rows * n_cols

    cols: list[ColumnProfile] = []
    total_missing = total_invalid = total_nonmissing = 0
    total_outliers = total_numeric_cells = degenerate_cols = 0

    for name in df.columns:
        prof, numeric_cells = _profile_column(df[name], str(name))
        cols.append(prof)
        total_missing += prof.missing_count
        total_invalid += prof.invalid_count
        total_nonmissing += (n_rows - prof.missing_count)
        total_outliers += prof.outlier_count
        total_numeric_cells += numeric_cells
        if prof.is_constant:
            degenerate_cols += 1

    # --- dimensiones ---
    completeness = _score(total_missing / total_cells) if total_cells else 100.0
    validity = _score(total_invalid / total_nonmissing) if total_nonmissing else 100.0

    duplicate_rows = int(df.duplicated().sum())
    uniqueness = _score(duplicate_rows / n_rows) if n_rows else 100.0

    outlier_rate = (total_outliers / total_numeric_cells) if total_numeric_cells else 0.0
    degenerate_rate = (degenerate_cols / n_cols) if n_cols else 0.0
    distribution = _score((outlier_rate + degenerate_rate) / 2)

    dims = [
        DimensionScore("completeness", completeness, DIMENSION_WEIGHTS["completeness"]),
        DimensionScore("validity", validity, DIMENSION_WEIGHTS["validity"]),
        DimensionScore("uniqueness", uniqueness, DIMENSION_WEIGHTS["uniqueness"]),
        DimensionScore("distribution", distribution, DIMENSION_WEIGHTS["distribution"]),
    ]
    overall = round(sum(d.score * d.weight for d in dims) / 100, 2)

    warnings = _collect_warnings(cols, duplicate_rows)

    return Report(
        filename=filename,
        created_at=created_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        n_rows=n_rows,
        n_cols=n_cols,
        overall_score=overall,
        duplicate_rows=duplicate_rows,
        dimensions=dims,
        columns=cols,
        warnings=warnings,
    )


def _collect_warnings(cols: list[ColumnProfile], duplicate_rows: int) -> list[Warning]:
    out: list[Warning] = []
    for c in cols:
        if c.missing_pct > WARN_MISSING_PCT:
            out.append(Warning("missing", f"{c.missing_pct}% de valores faltantes", c.name))
        if c.invalid_pct > WARN_INVALID_PCT:
            out.append(Warning(
                "invalid",
                f"{c.invalid_pct}% no conforman el tipo inferido ({c.inferred_type})",
                c.name,
            ))
        if c.outlier_pct > WARN_OUTLIER_PCT:
            out.append(Warning("outliers", f"{c.outlier_pct}% de celdas son outliers (IQR)", c.name))
        if c.is_constant:
            out.append(Warning("constant", "columna constante / casi-constante (>=95% un valor)", c.name))
    if duplicate_rows > 0:
        out.append(Warning("duplicate_rows", f"{duplicate_rows} filas totalmente duplicadas"))
    return out
