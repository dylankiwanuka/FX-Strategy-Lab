"""Unit tests for RSI indicator. Synthetic data only; no live API."""
from __future__ import annotations

import pandas as pd
import pytest

from src.indicators.rsi import rsi


def test_rsi_output_length_and_type():
    """Output length equals input length; type is Series."""
    close = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], index=range(8))
    result = rsi(close, period=2)
    assert isinstance(result, pd.Series)
    assert len(result) == len(close)
    assert result.index.equals(close.index)


def test_rsi_name_set():
    """Result series has name RSI_{period}."""
    close = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    result = rsi(close, period=2)
    assert result.name == "RSI_2"


def test_rsi_non_nan_in_range_0_100():
    """Non-NaN RSI values are in [0, 100]."""
    close = pd.Series([10.0, 12.0, 11.0, 13.0, 9.0, 14.0, 10.0, 11.0, 12.0, 13.0], index=range(10))
    result = rsi(close, period=3)
    valid = result.dropna()
    assert (valid >= 0).all() and (valid <= 100).all()


def test_rsi_increasing_series_high_after_warmup():
    """Steadily increasing prices produce high RSI (gains only -> RSI 100) after warmup."""
    # 1, 2, 3, 4, ... -> all gains after first diff; avg_loss = 0 -> RSI = 100
    close = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0], index=range(10))
    result = rsi(close, period=2)
    # First valid RSI at index 1 (period=2). After that, all deltas positive -> high RSI
    assert result.iloc[1] == pytest.approx(100.0)
    assert result.iloc[-1] == pytest.approx(100.0)


def test_rsi_decreasing_series_low_after_warmup():
    """Steadily decreasing prices produce low RSI (losses only -> RSI 0) after warmup."""
    close = pd.Series([10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0], index=range(10))
    result = rsi(close, period=2)
    assert result.iloc[1] == pytest.approx(0.0)
    assert result.iloc[-1] == pytest.approx(0.0)


def test_rsi_flat_series_fifty_after_warmup():
    """Flat prices -> delta=0 -> both_zero -> implementation sets 50.0."""
    close = pd.Series([5.0, 5.0, 5.0, 5.0, 5.0, 5.0], index=range(6))
    result = rsi(close, period=2)
    valid = result.dropna()
    assert (valid == 50.0).all()


def test_rsi_empty_series_raises():
    """Empty close series raises ValueError."""
    close = pd.Series(dtype=float)
    with pytest.raises(ValueError, match="close series is empty"):
        rsi(close, 2)


def test_rsi_period_zero_raises():
    """period <= 0 raises ValueError."""
    close = pd.Series([1.0, 2.0, 3.0])
    with pytest.raises(ValueError, match="period must be a positive integer"):
        rsi(close, 0)
    with pytest.raises(ValueError, match="period must be a positive integer"):
        rsi(close, -1)


def test_rsi_none_close_raises():
    """None close raises ValueError."""
    with pytest.raises(ValueError, match="close series is empty"):
        rsi(None, 2)


def test_rsi_period_one():
    """period=1 is allowed; first value is 50 (diff NaN -> gains=0, losses=0 -> both_zero -> 50); then RSI 100/0."""
    close = pd.Series([10.0, 11.0, 10.0], index=range(3))
    result = rsi(close, period=1)
    assert len(result) == 3
    # Index 0: diff NaN -> where(delta>0,0) gives 0, so gains=0, losses=0 -> both_zero -> 50
    assert result.iloc[0] == pytest.approx(50.0)
    assert result.iloc[1] == pytest.approx(100.0)
    assert result.iloc[2] == pytest.approx(0.0)
