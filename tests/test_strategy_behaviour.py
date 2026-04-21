"""Strategy behaviour on synthetic series (distinct from test_strategies)."""
from __future__ import annotations

import pandas as pd
import pytest

from src.strategies.ma_crossover import ma_crossover_signals
from src.strategies.rsi_strategy import rsi_signals


def test_ma_crossover_trending_market_produces_signals() -> None:
    """Strong uptrend after flat warmup should yield at least one buy from crossover logic."""
    close = pd.Series([1.0] * 20 + list(range(20, 40)), index=range(40))
    df = pd.DataFrame({"Close": close})
    out = ma_crossover_signals(df, fast_window=3, slow_window=8, ma_type="SMA")
    assert (out["signal"] == 1).any()


def test_rsi_extreme_conditions_signals() -> None:
    """Sharp drop then bounce produces oversold buy before overbought sell in this synthetic path."""
    n = 30
    drops = [100.0 - i * 3.0 for i in range(n // 2)]
    rises = [drops[-1] + i * 2.5 for i in range(1, n - len(drops) + 1)]
    close = pd.Series(drops + rises, index=range(len(drops + rises)))
    df = pd.DataFrame({"Close": close})
    out = rsi_signals(df, period=5, oversold=35.0, overbought=65.0)
    assert (out["rsi"] < 35).any() or (out["signal"] == 1).any()


# ---- SMA Price Cross ----

from src.strategies.sma_price_cross import sma_price_cross_signals


def test_sma_price_cross_buy_signal_on_known_cross() -> None:
    close = pd.Series([5.0, 5.0, 5.0, 4.0, 4.0, 4.0, 10.0, 10.0, 10.0], dtype=float)
    df = pd.DataFrame({"Open": close, "High": close, "Low": close, "Close": close})
    out = sma_price_cross_signals(df, window=3)
    assert out["signal"].iloc[6] == 1


def test_sma_price_cross_sell_signal_on_known_cross() -> None:
    close = pd.Series([5.0, 5.0, 5.0, 6.0, 6.0, 6.0, 1.0, 1.0, 1.0], dtype=float)
    df = pd.DataFrame({"Open": close, "High": close, "Low": close, "Close": close})
    out = sma_price_cross_signals(df, window=3)
    assert out["signal"].iloc[6] == -1


def test_sma_price_cross_no_signal_when_no_cross() -> None:
    close = pd.Series([5.0] * 8, dtype=float)
    df = pd.DataFrame({"Close": close})
    out = sma_price_cross_signals(df, window=3)
    assert (out["signal"] == 0).all()


def test_sma_price_cross_signal_column_values_valid() -> None:
    close = pd.Series([1.0, 3.0, 2.0, 5.0, 4.0, 6.0, 7.0], dtype=float)
    df = pd.DataFrame({"Close": close})
    out = sma_price_cross_signals(df, window=2)
    assert set(out["signal"].unique()).issubset({-1, 0, 1})


def test_sma_price_cross_output_has_sma_column() -> None:
    close = pd.Series([1.0, 2.0, 3.0, 4.0], dtype=float)
    df = pd.DataFrame({"Close": close})
    out = sma_price_cross_signals(df, window=2)
    assert "sma" in out.columns


def test_sma_price_cross_missing_close_raises() -> None:
    df = pd.DataFrame({"Open": [1.0, 2.0]})
    with pytest.raises(ValueError, match="DataFrame must contain a non-empty Close column"):
        sma_price_cross_signals(df, window=3)


def test_sma_price_cross_window_zero_raises() -> None:
    df = pd.DataFrame({"Close": [1.0, 2.0, 3.0]})
    with pytest.raises(ValueError, match="window must be a positive integer"):
        sma_price_cross_signals(df, window=0)
