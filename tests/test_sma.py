"""Unit tests for the SMA indicator. Synthetic data only."""
from __future__ import annotations

import pandas as pd
import pytest

from src.indicators.sma import sma


def test_sma_output_is_series() -> None:
    close = pd.Series([1.0, 2.0, 3.0], dtype=float)
    result = sma(close, window=2)
    assert isinstance(result, pd.Series)


def test_sma_output_length_matches_input() -> None:
    close = pd.Series([1.0, 2.0, 3.0, 4.0], dtype=float)
    result = sma(close, window=2)
    assert len(result) == len(close)


def test_sma_index_preserved() -> None:
    idx = pd.DatetimeIndex(pd.date_range("2024-01-01", periods=4, freq="D"))
    close = pd.Series([1.0, 2.0, 3.0, 4.0], index=idx, dtype=float)
    result = sma(close, window=2)
    assert result.index.equals(close.index)


def test_sma_nan_count() -> None:
    close = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=float)
    result = sma(close, window=3)
    assert result.iloc[:2].isna().all()
    assert not result.iloc[2:].isna().any()


def test_sma_known_arithmetic() -> None:
    close = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], dtype=float)
    result = sma(close, window=3)
    assert result.iloc[2] == pytest.approx(2.0)
    assert result.iloc[3] == pytest.approx(3.0)
    assert result.iloc[4] == pytest.approx(4.0)


def test_sma_window_of_one_no_nans() -> None:
    close = pd.Series([1.0, 2.0, 3.5], dtype=float)
    result = sma(close, window=1)
    assert not result.isna().any()
    pd.testing.assert_series_equal(result, close)


def test_sma_window_equals_series_length() -> None:
    close = pd.Series([2.0, 4.0, 6.0], dtype=float)
    result = sma(close, window=len(close))
    assert result.iloc[:-1].isna().all()
    assert result.iloc[-1] == pytest.approx(close.mean())


def test_sma_window_larger_than_series() -> None:
    close = pd.Series([1.0, 2.0, 3.0], dtype=float)
    result = sma(close, window=10)
    assert result.isna().all()


def test_sma_window_zero_raises() -> None:
    close = pd.Series([1.0, 2.0], dtype=float)
    with pytest.raises(ValueError, match="window must be a positive integer"):
        sma(close, window=0)


def test_sma_window_negative_raises() -> None:
    close = pd.Series([1.0, 2.0], dtype=float)
    with pytest.raises(ValueError, match="window must be a positive integer"):
        sma(close, window=-3)


def test_sma_empty_series_raises() -> None:
    close = pd.Series(dtype=float)
    with pytest.raises(ValueError, match="close series is empty"):
        sma(close, window=3)


def test_sma_none_raises() -> None:
    with pytest.raises(ValueError, match="close series is empty"):
        sma(None, window=3)  # type: ignore[arg-type]
