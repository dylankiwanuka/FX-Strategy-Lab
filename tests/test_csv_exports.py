"""CSV export helpers (ui.helpers.formatting) — no Streamlit."""
from __future__ import annotations

import io

import pandas as pd

from ui.helpers.formatting import csv_bytes, equity_curve_export_df, rename_first_index_column


def test_trades_csv_structure() -> None:
    df = pd.DataFrame([{"a": 1, "b": 2}])
    raw = csv_bytes(df).decode("utf-8")
    assert "a" in raw.splitlines()[0]


def test_equity_csv_columns_datetime_index() -> None:
    idx = pd.to_datetime(["2024-01-01", "2024-01-02"])
    s = pd.Series([100.0, 101.0], index=idx, name="Equity")
    out = equity_curve_export_df(s)
    assert "Date" in out.columns
    assert "Equity" in out.columns
    buf = io.StringIO(csv_bytes(out).decode("utf-8"))
    roundtrip = pd.read_csv(buf)
    assert list(roundtrip.columns) == ["Date", "Equity"]


def test_equity_csv_columns_integer_index() -> None:
    s = pd.Series([1.0, 2.0], index=[0, 1])
    out = equity_curve_export_df(s)
    assert "Index" in out.columns


def test_rename_first_index_column() -> None:
    df = pd.DataFrame({"x": [1]})
    df.index = pd.to_datetime(["2024-01-01"])
    r = df.reset_index()
    r = rename_first_index_column(r)
    assert r.columns[0] == "Date"


def test_session_history_export_headers() -> None:
    hist = [{"a": 1, "b": "x"}]
    df = pd.DataFrame(hist)
    header = csv_bytes(df).decode("utf-8").splitlines()[0]
    assert "a" in header and "b" in header
