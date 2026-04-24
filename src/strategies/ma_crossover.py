from __future__ import annotations

import pandas as pd

from src.indicators.sma import sma
from src.indicators.ema import ema


def ma_crossover_signals(
    df: pd.DataFrame,
    fast_window: int,
    slow_window: int,
    ma_type: str,
) -> pd.DataFrame:
    """Adds fast/slow moving averages plus crossover signals (1=buy, -1=sell, 0=none)."""
    if "Close" not in df.columns or df["Close"] is None or df["Close"].empty:
        raise ValueError("DataFrame must contain a non-empty Close column")
    if fast_window <= 0 or slow_window <= 0:
        raise ValueError("fast_window and slow_window must be positive integers")
    if fast_window >= slow_window:
        raise ValueError("fast_window must be less than slow_window")
    if ma_type not in ("SMA", "EMA"):
        raise ValueError("ma_type must be 'SMA' or 'EMA'")

    close = df["Close"]
    if ma_type == "SMA":
        fast_ma = sma(close, fast_window)
        slow_ma = sma(close, slow_window)
    else:
        fast_ma = ema(close, fast_window)
        slow_ma = ema(close, slow_window)

    # Need prior MA values to catch the flip bar — comparing only current fast vs slow would stay
    # true for the whole leg after a cross, not just the crossing bar.
    fast_prev = fast_ma.shift(1)
    slow_prev = slow_ma.shift(1)
    cross_above = (fast_ma > slow_ma) & (fast_prev <= slow_prev)
    cross_below = (fast_ma < slow_ma) & (fast_prev >= slow_prev)

    signal = pd.Series(0, index=df.index, dtype=int)
    signal = signal.mask(cross_above, 1).mask(cross_below, -1).astype(int)  # vectorised masks, no per-row loop

    out = df.copy()
    out["fast_ma"] = fast_ma
    out["slow_ma"] = slow_ma
    out["signal"] = signal
    return out
