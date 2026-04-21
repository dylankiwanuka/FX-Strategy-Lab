from __future__ import annotations

import pandas as pd

from src.indicators.sma import sma


def sma_price_cross_signals(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """Generates buy (1) when Close crosses above its SMA, sell (-1) when it crosses below, else 0."""
    if "Close" not in df.columns or df["Close"].empty:
        raise ValueError("DataFrame must contain a non-empty Close column")
    if window <= 0:
        raise ValueError("window must be a positive integer")

    sma_series = sma(df["Close"], window)
    # need the previous bar to detect the moment of crossing, not just the current state
    close_prev = df["Close"].shift(1)
    sma_prev = sma_series.shift(1)
    cross_above = (df["Close"] > sma_series) & (close_prev <= sma_prev)
    cross_below = (df["Close"] < sma_series) & (close_prev >= sma_prev)

    signal = pd.Series(0, index=df.index, dtype=int)
    # simpler than MA crossover — one parameter, signal tied directly to price vs its own average
    signal = signal.mask(cross_above, 1).mask(cross_below, -1).astype(int)

    out = df.copy()
    out["sma"] = sma_series
    out["signal"] = signal
    return out
