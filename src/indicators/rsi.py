from __future__ import annotations

import pandas as pd


def rsi(close: pd.Series, period: int) -> pd.Series:
    """
    Relative Strength Index (RSI) using rolling average of gains and losses over the given period.
    """
    if period <= 0:
        raise ValueError("period must be a positive integer")
    if close is None or close.empty:
        raise ValueError("close series is empty")

    delta = close.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)

    avg_gain = gains.rolling(window=period, min_periods=period).mean()
    avg_loss = losses.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    result = 100 - (100 / (1 + rs))
    both_zero = (avg_gain == 0) & (avg_loss == 0)
    result = result.where(~both_zero, 50.0)

    result.name = f"RSI_{period}"
    return result
