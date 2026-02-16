from __future__ import annotations

import pandas as pd


def ema(close: pd.Series, window: int) -> pd.Series:
    """
    Exponential Moving Average (EMA) over the given span.
    """
    if window <= 0:
        raise ValueError("window must be a positive integer")
    if close is None or close.empty:
        raise ValueError("close series is empty")

    result = close.ewm(span=window, adjust=False).mean()
    result.name = f"EMA_{window}"
    return result
