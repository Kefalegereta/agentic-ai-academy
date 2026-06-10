import pandas as pd

from app.profiler import profile
from app.store import init_db, save_report, list_reports, get_report


def _report():
    df = pd.DataFrame({"a": ["1", "2"], "b": ["x", "y"]})
    return profile(df, "demo.csv")


def test_save_and_reopen_roundtrip(tmp_path):
    db = tmp_path / "r.db"
    init_db(db)
    rid = save_report(_report(), db)
    loaded = get_report(rid, db)
    assert loaded is not None
    assert loaded.filename == "demo.csv"
    assert loaded.overall_score == _report().overall_score
    assert len(loaded.columns) == 2


def test_list_orders_newest_first(tmp_path):
    db = tmp_path / "r.db"
    init_db(db)
    r1 = _report(); r1.filename = "first.csv"
    r2 = _report(); r2.filename = "second.csv"
    save_report(r1, db)
    save_report(r2, db)
    summaries = list_reports(db)
    assert [s.filename for s in summaries] == ["second.csv", "first.csv"]


def test_get_missing_returns_none(tmp_path):
    db = tmp_path / "r.db"
    init_db(db)
    assert get_report(999, db) is None
