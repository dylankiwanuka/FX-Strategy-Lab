"""Tests for strategy signal generation. Synthetic DataFrames only; no live API."""
from __future__ import annotations

import pandas as pd
import pytest

from src.strategies.ma_crossover import ma_crossover_signals
from src.strategies.rsi_strategy import rsi_signals


# ---- MA Crossover ----


def test_ma_crossover_cross_above_buy_signal():
    """When fast MA crosses above slow MA at a known bar, signal is 1 at that bar."""
    # SMA(2) and SMA(4). Build Close so that at bar 3 (0-indexed) fast crosses above slow.
    # Close: 10, 10, 12, 14 -> SMA2: NaN, 10, 11, 13; SMA4: NaN, NaN, NaN, (10+10+12+14)/4=11.5
    # At bar 3: fast_ma=13, slow_ma=11.5, fast_prev=11, slow_prev=NaN. We need slow_prev valid.
    # Use more bars: 10, 10, 10, 10, 12, 14 -> SMA2: NaN, 10, 10, 10, 11, 13; SMA4: NaN, NaN, NaN, 10, 10.5, 11.5
    # At bar 4: fast_ma=11, slow_ma=10.5, fast_prev=10, slow_prev=10 -> cross above (11>10.5 and 10<=10). So signal=1 at 4.
    close = pd.Series([10.0, 10.0, 10.0, 10.0, 12.0, 14.0], index=range(6))
    df = pd.DataFrame({"Close": close})
    out = ma_crossover_signals(df, fast_window=2, slow_window=4, ma_type="SMA")
    assert "fast_ma" in out.columns and "slow_ma" in out.columns and "signal" in out.columns
    # Cross above at index 4
    assert out["signal"].iloc[4] == 1


def test_ma_crossover_cross_below_sell_signal():
    """When fast MA crosses below slow MA, signal is -1 at that bar."""
    # Need fast_prev >= slow_prev and fast_ma < slow_ma. Close: 100,100,100,100,80,60 -> SMA2: NaN,100,100,100,90,70; SMA4: NaN,NaN,NaN,100,95,85
    # Bar 4: fast=90, slow=95, fast_prev=100, slow_prev=100 -> cross_below = (90<95) & (100>=100) = True.
    close = pd.Series([100.0, 100.0, 100.0, 100.0, 80.0, 60.0], index=range(6))
    df = pd.DataFrame({"Close": close})
    out = ma_crossover_signals(df, fast_window=2, slow_window=4, ma_type="SMA")
    assert out["signal"].iloc[4] == -1


def test_ma_crossover_no_cross_signal_zero():
    """When there is no cross, signal stays 0."""
    close = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0], index=range(5))  # monotonic up -> fast always above slow after warmup
    df = pd.DataFrame({"Close": close})
    out = ma_crossover_signals(df, fast_window=2, slow_window=4, ma_type="SMA")
    assert (out["signal"] == 0).all()


def test_ma_crossover_fast_ge_slow_raises():
    """fast_window >= slow_window raises ValueError."""
    df = pd.DataFrame({"Close": [1.0, 2.0, 3.0, 4.0, 5.0]})
    with pytest.raises(ValueError, match="fast_window must be less than slow_window"):
        ma_crossover_signals(df, fast_window=3, slow_window=3, ma_type="SMA")
    with pytest.raises(ValueError, match="fast_window must be less than slow_window"):
        ma_crossover_signals(df, fast_window=4, slow_window=3, ma_type="SMA")


def test_ma_crossover_invalid_ma_type_raises():
    """ma_type not 'SMA' or 'EMA' raises ValueError."""
    df = pd.DataFrame({"Close": [1.0, 2.0, 3.0, 4.0, 5.0]})
    with pytest.raises(ValueError, match="ma_type must be 'SMA' or 'EMA'"):
        ma_crossover_signals(df, fast_window=2, slow_window=4, ma_type="OTHER")


def test_ma_crossover_missing_close_raises():
    """DataFrame without Close or with empty Close raises ValueError."""
    with pytest.raises(ValueError, match="DataFrame must contain a non-empty Close column"):
        ma_crossover_signals(pd.DataFrame({"Other": [1, 2, 3]}), 2, 4, "SMA")
    empty = pd.DataFrame({"Close": []})
    with pytest.raises(ValueError, match="DataFrame must contain a non-empty Close column"):
        ma_crossover_signals(empty, 2, 4, "SMA")


def test_ma_crossover_ema_type():
    """ma_type EMA produces valid output with same signal logic."""
    close = pd.Series([10.0, 10.0, 12.0, 14.0], index=range(4))
    df = pd.DataFrame({"Close": close})
    out = ma_crossover_signals(df, fast_window=2, slow_window=3, ma_type="EMA")
    assert "fast_ma" in out.columns and "slow_ma" in out.columns and "signal" in out.columns
    assert out["signal"].dtype in (int, "int32", "int64") or out["signal"].values.dtype.kind == "i"


# ---- RSI Strategy ----


def test_rsi_signals_oversold_buy():
    """When RSI drops below oversold, signal is 1."""
    # Decreasing then flat: RSI will go low. period=2, oversold=30. Need RSI < 30.
    # 10, 9, 8, 7, 6, 6, 6 -> after warmup RSI 0 then stays low
    close = pd.Series([10.0, 9.0, 8.0, 7.0, 6.0, 6.0, 6.0], index=range(7))
    df = pd.DataFrame({"Close": close})
    out = rsi_signals(df, period=2, oversold=30, overbought=70)
    assert "rsi" in out.columns and "signal" in out.columns
    # RSI at index 1 is 0 (all losses), so signal should be 1
    assert out["signal"].iloc[1] == 1


def test_rsi_signals_overbought_sell():
    """When RSI rises above overbought, signal is -1."""
    close = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], index=range(6))
    df = pd.DataFrame({"Close": close})
    out = rsi_signals(df, period=2, oversold=30, overbought=70)
    # RSI = 100 after warmup for strictly increasing -> signal -1
    assert out["signal"].iloc[-1] == -1 or (out["signal"] == -1).any()


def test_rsi_signals_oversold_ge_overbought_raises():
    """oversold >= overbought raises ValueError."""
    df = pd.DataFrame({"Close": [1.0, 2.0, 3.0, 4.0, 5.0]})
    with pytest.raises(ValueError, match="oversold must be less than overbought"):
        rsi_signals(df, period=2, oversold=50, overbought=50)
    with pytest.raises(ValueError, match="oversold must be less than overbought"):
        rsi_signals(df, period=2, oversold=70, overbought=30)


def test_rsi_signals_missing_close_raises():
    """DataFrame without non-empty Close raises ValueError."""
    with pytest.raises(ValueError, match="DataFrame must contain a non-empty Close column"):
        rsi_signals(pd.DataFrame({"Other": [1, 2, 3]}), period=2)
    empty = pd.DataFrame({"Close": []})
    with pytest.raises(ValueError, match="DataFrame must contain a non-empty Close column"):
        rsi_signals(empty, period=2)


def test_rsi_signals_signal_values_are_1_or_minus1_or_zero():
    """Signal column contains only 1, -1, or 0."""
    close = pd.Series([10.0, 11.0, 10.5, 12.0, 11.0, 13.0, 12.0], index=range(7))
    df = pd.DataFrame({"Close": close})
    out = rsi_signals(df, period=2, oversold=25, overbought=75)
    assert set(out["signal"].dropna().unique()).issubset({-1, 0, 1})
