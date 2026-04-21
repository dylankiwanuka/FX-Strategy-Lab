"""Backtest edge cases and forced-exit annotation (synthetic data)."""
from __future__ import annotations

import pandas as pd
import pytest

from src.backtest.engine import run_backtest
from ui.helpers.postprocess import annotate_forced_exit_trades


def _make_df(close_list: list[float], signal_list: list[int], index=None) -> pd.DataFrame:
    if index is None:
        index = range(len(close_list))
    return pd.DataFrame({"Close": close_list, "signal": signal_list}, index=index)


def test_no_trades_generated() -> None:
    df = _make_df([100.0, 101.0, 102.0], [0, 0, 0])
    trades, equity = run_backtest(df)
    assert trades == []
    assert len(equity) == len(df)


def test_single_trade_execution() -> None:
    df = _make_df([99.0, 100.0, 105.0, 110.0], [0, 1, 0, -1])
    trades, _ = run_backtest(df)
    assert len(trades) == 1
    assert trades[0]["entry_price"] == 100.0
    assert trades[0]["exit_price"] == 110.0


def test_forced_exit_at_end_flagged() -> None:
    df = _make_df([100.0, 102.0, 104.0], [0, 1, 0])
    trades, _ = run_backtest(df)
    annotated = annotate_forced_exit_trades(trades, df)
    assert annotated[-1].get("forced_exit") is True


def test_forced_exit_not_flagged_when_sell_on_last_bar() -> None:
    df = _make_df([100.0, 102.0, 104.0], [0, 1, -1])
    trades, _ = run_backtest(df)
    annotated = annotate_forced_exit_trades(trades, df)
    assert annotated[-1].get("forced_exit") is not True
