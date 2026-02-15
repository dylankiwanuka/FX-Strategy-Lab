from __future__ import annotations

import pandas as pd

from src.indicators.rsi import rsi


def rsi_signals(
    df: pd.DataFrame,
    period: int = 14,
    oversold: float = 30,
    overbought: float = 70,
) -> pd.DataFrame:
    """
    RSI overbought/oversold signal generator. Adds rsi and signal (1=oversold buy, -1=overbought sell, 0=none).
    """
    if "Close" not in df.columns or df["Close"] is None or df["Close"].empty:
        raise ValueError("DataFrame must contain a non-empty Close column")
    if period <= 0:
        raise ValueError("period must be a positive integer")
    if oversold >= overbought:
        raise ValueError("oversold must be less than overbought")

    rsi_series = rsi(df["Close"], period)

    signal = pd.Series(0, index=df.index, dtype=int)
    signal = signal.mask(rsi_series < oversold, 1).mask(rsi_series > overbought, -1).astype(int)

    out = df.copy()
    out["rsi"] = rsi_series
    out["signal"] = signal
    return out
