from __future__ import annotations

import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    """Returns the simple moving average of Close over a fixed-length rolling window."""
    if window <= 0:
        raise ValueError("window must be a positive integer")
    if close is None or close.empty:
        raise ValueError("close series is empty")

    # min_periods=window avoids misleading partial-window means at the start — NaN is more honest.
    return close.rolling(window=window, min_periods=window).mean()
