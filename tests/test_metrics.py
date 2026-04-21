"""Focused metrics tests (logic only)."""
from __future__ import annotations

import pandas as pd
import pytest

from src.backtest.metrics import compute_metrics


def test_max_drawdown_correctness() -> None:
    equity = pd.Series([100.0, 110.0, 99.0, 104.0], index=range(4))
    m = compute_metrics([], equity)
    assert m["max_drawdown_value"] < 0
    assert m["max_drawdown_pct"] == pytest.approx(abs((99.0 - 110.0) / 110.0 * 100))


def test_win_rate_calculation() -> None:
    equity = pd.Series([10_000.0, 10_050.0, 10_020.0, 10_080.0], index=range(4))
    trades = [
        {"pnl": 50.0, "return_pct": 0.5},
        {"pnl": -30.0, "return_pct": -0.3},
        {"pnl": 60.0, "return_pct": 0.6},
    ]
    m = compute_metrics(trades, equity)
    assert m["num_trades"] == 3
    assert m["win_rate_pct"] == pytest.approx(100.0 * 2 / 3)
