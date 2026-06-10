import pandas as pd

from app.profiler import profile


def _df(d):
    # construye un DataFrame de strings, como lo entrega ingest
    return pd.DataFrame({k: [str(x) for x in v] for k, v in d.items()})


def _dim(report, name):
    return next(d for d in report.dimensions if d.name == name)


def test_perfect_dataset_scores_100():
    df = _df({"id": [1, 2, 3, 4], "v": [10, 20, 30, 40]})
    r = profile(df, "t.csv")
    assert r.overall_score == 100.0
    assert r.warnings == []


def test_null_tokens_count_as_missing_not_invalid():
    # 'N/A' en columna numerica es FALTANTE, no invalido
    df = _df({"year": ["2001", "N/A", "2003", "2004"]})
    r = profile(df, "t.csv")
    col = r.columns[0]
    assert col.inferred_type == "integer"
    assert col.missing_count == 1
    assert col.invalid_count == 0
    assert _dim(r, "completeness").score == 75.0  # 1 de 4 faltante


def test_type_inference_90pct_threshold():
    # 9 enteros + 1 basura = 90% -> integer, 1 invalido
    vals = [str(i) for i in range(9)] + ["junk"]
    df = _df({"c": vals})
    r = profile(df, "t.csv")
    assert r.columns[0].inferred_type == "integer"
    assert r.columns[0].invalid_count == 1


def test_below_threshold_becomes_text_no_invalids():
    # 5 enteros + 5 texto = 50% -> text, sin invalidos
    df = _df({"c": ["1", "2", "3", "4", "5", "a", "b", "c", "d", "e"]})
    r = profile(df, "t.csv")
    assert r.columns[0].inferred_type == "text"
    assert r.columns[0].invalid_count == 0


def test_duplicate_rows_lower_uniqueness_and_warn():
    df = _df({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    r = profile(df, "t.csv")
    assert r.duplicate_rows == 1
    assert _dim(r, "uniqueness").score == round(100 * (1 - 1 / 3), 2)
    assert any(w.kind == "duplicate_rows" for w in r.warnings)


def test_constant_column_flagged_in_distribution():
    df = _df({"k": ["same"] * 20 + ["other"]})  # 95.2% un valor
    r = profile(df, "t.csv")
    assert r.columns[0].is_constant
    assert any(w.kind == "constant" for w in r.warnings)
    assert _dim(r, "distribution").score < 100


def test_outliers_detected_by_iqr():
    df = _df({"x": [10] * 20 + [10000]})  # un outlier claro
    r = profile(df, "t.csv")
    assert r.columns[0].outlier_count >= 1


def test_missing_over_threshold_warns():
    # 2 de 10 faltantes = 20% > 5%
    df = _df({"c": ["1", "2", "", "", "5", "6", "7", "8", "9", "10"]})
    r = profile(df, "t.csv")
    assert any(w.kind == "missing" and w.column == "c" for w in r.warnings)


def test_weights_applied_to_overall():
    # 10 enteros distintos, 1 faltante -> completitud 90, resto 100.
    # global = (90*30 + 100*30 + 100*20 + 100*20)/100 = 97
    df = _df({"c": ["1", "2", "3", "4", "5", "6", "7", "8", "9", ""]})
    r = profile(df, "t.csv")
    assert _dim(r, "completeness").score == 90.0
    assert r.overall_score == 97.0
