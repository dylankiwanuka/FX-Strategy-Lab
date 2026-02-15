from __future__ import annotations

import pandas as pd


def compute_metrics(
    trades: list[dict],
    equity_curve: pd.Series,
) -> dict:
    """
    Compute performance metrics from backtest outputs.

    Metrics:
    - total_return_pct: Period return (first to last equity) in percent.
    - num_trades: Number of round-trip trades.
    - win_rate_pct: Percent of trades with positive pnl (0 if no trades).
    - avg_trade_return_pct: Average return_pct across trades (0 if no trades).
    - max_drawdown_pct: Worst drawdown as a positive percentage (e.g. 5.0 = 5% drawdown).
    - max_drawdown_value: Worst peak-to-trough drop in equity units, signed negative (e.g. -500.0).
    """
    if equity_curve is None or len(equity_curve) == 0:
        raise ValueError("equity_curve must be non-empty")

    total_return_pct = float(
        (equity_curve.iloc[-1] / equity_curve.iloc[0] - 1) * 100
    )
    num_trades = int(len(trades))

    if num_trades == 0:
        win_rate_pct = 0.0
        avg_trade_return_pct = 0.0
    else:
        wins = sum(1 for t in trades if t["pnl"] > 0)
        win_rate_pct = float(wins / num_trades * 100)
        avg_trade_return_pct = float(
            sum(t["return_pct"] for t in trades) / num_trades
        )

    peak = equity_curve.cummax()
    drawdown_value = equity_curve - peak
    max_drawdown_value = float(drawdown_value.min())

    drawdown_pct = (equity_curve - peak) / peak
    drawdown_pct = drawdown_pct.replace([float("inf"), float("-inf")], 0.0).fillna(0.0)
    drawdown_pct = drawdown_pct * 100
    max_drawdown_pct = float(abs(drawdown_pct.min()))

    return {
        "total_return_pct": total_return_pct,
        "num_trades": num_trades,
        "win_rate_pct": win_rate_pct,
        "avg_trade_return_pct": avg_trade_return_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "max_drawdown_value": max_drawdown_value,
    }
