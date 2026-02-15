from __future__ import annotations

import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    """
    Simple Moving Average (SMA) over a rolling window.
    """
    if window <= 0:
        raise ValueError("window must be a positive integer")
    if close is None or close.empty:
        raise ValueError("close series is empty")

    return close.rolling(window=window, min_periods=window).mean()
