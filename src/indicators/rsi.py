from __future__ import annotations

import pandas as pd


def rsi(close: pd.Series, period: int) -> pd.Series:
    """RSI from simple rolling mean gains/losses (not Wilder smoothing) for easier reading."""
    if period <= 0:
        raise ValueError("period must be a positive integer")
    if close is None or close.empty:
        raise ValueError("close series is empty")

    delta = close.diff()  # NaN at index 0 is expected and flows correctly into the gain/loss split.
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)

    # Simple rolling mean keeps the RSI construction legible against textbook definitions.
    avg_gain = gains.rolling(window=period, min_periods=period).mean()
    avg_loss = losses.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    result = 100 - (100 / (1 + rs))
    both_zero = (avg_gain == 0) & (avg_loss == 0)
    # Flat price yields 0/0 which becomes NaN in pandas — 50 is the neutral RSI when nothing moved.
    result = result.where(~both_zero, 50.0)

    result.name = f"RSI_{period}"  # Named here so downstream DataFrames show a clear column label.
    return result
