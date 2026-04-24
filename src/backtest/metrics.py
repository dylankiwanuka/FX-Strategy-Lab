from __future__ import annotations

import pandas as pd


def compute_metrics(
    trades: list[dict],
    equity_curve: pd.Series,
) -> dict:
    """Summarise total return, trade stats, and drawdown from trades plus an equity curve."""
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

    peak = equity_curve.cummax()  # drawdown is from the running peak — worst loss while holding the run
    drawdown_value = equity_curve - peak
    max_drawdown_value = float(drawdown_value.min())

    drawdown_pct = (equity_curve - peak) / peak
    # A zero peak would divide by zero; replace infinities without masking genuine underwater periods.
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
