from __future__ import annotations

import pandas as pd


def ema(close: pd.Series, window: int) -> pd.Series:
    """Returns the exponential moving average of Close for the given span."""
    if window <= 0:
        raise ValueError("window must be a positive integer")
    if close is None or close.empty:
        raise ValueError("close series is empty")

    # adjust=False matches the recursive EMA update (each value depends on the prior EMA), not the
    # fully expanded weighted-sum form that adjust=True uses.
    result = close.ewm(span=window, adjust=False).mean()
    result.name = f"EMA_{window}"
    return result
