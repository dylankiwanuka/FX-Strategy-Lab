from __future__ import annotations

import pandas as pd


def clean_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and validates OHLC data:
    - ensures datetime index
    - sorts by time
    - removes duplicate timestamps
    - converts values to numeric
    - forward-fills missing values
    - drops remaining NaNs
    """
    if df is None or df.empty:
        raise ValueError("Input OHLC DataFrame is empty.")

    out = df.copy()

    out.index = pd.to_datetime(out.index, errors="coerce")
    if out.index.isna().any():
        raise ValueError("Index contains invalid datetime values.")

    out = out.sort_index()
    out = out[~out.index.duplicated(keep="first")]

    required = ["Open", "High", "Low", "Close"]
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError(f"OHLC DataFrame missing columns: {missing}")

    for c in required:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    out = out.ffill()
    out = out.dropna(subset=required)

    if not out.index.is_monotonic_increasing:
        raise ValueError("Datetime index is not sorted correctly after cleaning.")

    return out
