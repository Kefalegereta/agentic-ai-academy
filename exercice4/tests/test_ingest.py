import pytest

from app.ingest import IngestError, parse_csv, MAX_BYTES


def test_parses_basic_csv_as_strings():
    data = b"a,b\n1,x\n2,y\n"
    df = parse_csv(data, "t.csv")
    assert list(df.columns) == ["a", "b"]
    assert df.shape == (2, 2)
    # todo se lee como string: el profiler decide los tipos
    assert df["a"].tolist() == ["1", "2"]


def test_does_not_interpret_na_tokens():
    # 'NA'/'' deben llegar crudos; el profiler decide que es faltante
    df = parse_csv(b"a,b\nNA,\n1,2\n", "t.csv")
    assert df["a"].tolist() == ["NA", "1"]
    assert df["b"].tolist() == ["", "2"]


def test_empty_file_rejected():
    with pytest.raises(IngestError):
        parse_csv(b"", "t.csv")


def test_headers_only_rejected():
    with pytest.raises(IngestError):
        parse_csv(b"a,b\n", "t.csv")


def test_oversize_rejected(monkeypatch):
    big = b"a,b\n" + b"1,2\n" * 10
    monkeypatch.setattr("app.ingest.MAX_BYTES", 5)
    with pytest.raises(IngestError):
        parse_csv(big, "t.csv")


def test_latin1_fallback():
    data = "n,city\n1,Málaga\n".encode("latin-1")
    df = parse_csv(data, "t.csv")
    assert df.shape == (1, 2)
