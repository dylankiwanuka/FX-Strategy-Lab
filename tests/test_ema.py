"""Unit tests for EMA indicator. Synthetic data only; no live API."""
from __future__ import annotations

import pandas as pd
import pytest

from src.indicators.ema import ema


def test_ema_output_length_and_type():
    """Output length equals input length; type is Series; index preserved."""
    close = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=[0, 1, 2, 3, 4])
    result = ema(close, window=2)
    assert isinstance(result, pd.Series)
    assert len(result) == len(close)
    assert result.index.equals(close.index)


def test_ema_name_set():
    """Result series has name EMA_{window}."""
    close = pd.Series([1.0, 2.0, 3.0])
    result = ema(close, window=2)
    assert result.name == "EMA_2"


def test_ema_matches_pandas_reference():
    """EMA values match close.ewm(span=window, adjust=False).mean()."""
    close = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0], index=range(6))
    window = 3
    result = ema(close, window=window)
    reference = close.ewm(span=window, adjust=False).mean()
    for i in close.index:
        assert result.loc[i] == pytest.approx(reference.loc[i])


def test_ema_window_one_equals_series():
    """With window=1, EMA (ewm span=1) equals the close series."""
    close = pd.Series([1.0, 5.0, 3.0, 7.0], index=[0, 1, 2, 3])
    result = ema(close, window=1)
    pd.testing.assert_series_equal(result, close, check_names=False)
    assert result.name == "EMA_1"


def test_ema_empty_series_raises():
    """Empty close series raises ValueError."""
    close = pd.Series(dtype=float)
    with pytest.raises(ValueError, match="close series is empty"):
        ema(close, 2)


def test_ema_window_zero_raises():
    """window <= 0 raises ValueError."""
    close = pd.Series([1.0, 2.0, 3.0])
    with pytest.raises(ValueError, match="window must be a positive integer"):
        ema(close, 0)
    with pytest.raises(ValueError, match="window must be a positive integer"):
        ema(close, -1)


def test_ema_none_close_raises():
    """None close raises ValueError."""
    with pytest.raises(ValueError, match="close series is empty"):
        ema(None, 2)


def test_ema_warmup_first_value():
    """First value of EMA is the first close (ewm default behaviour)."""
    close = pd.Series([100.0, 102.0, 101.0, 105.0], index=range(4))
    result = ema(close, window=3)
    assert result.iloc[0] == pytest.approx(100.0)
