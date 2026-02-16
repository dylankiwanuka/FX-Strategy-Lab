from __future__ import annotations

import pandas as pd


def run_backtest(
    df: pd.DataFrame,
    initial_capital: float = 10000.0,
) -> tuple[list[dict], pd.Series]:
    """
    Minimal sequential backtester: long-only, one position at a time.
    Entry at signal==1, exit at signal==-1, at Close. Returns trades and index-aligned equity curve.
    """
    if "Close" not in df.columns or "signal" not in df.columns or df.empty:
        raise ValueError("DataFrame must contain non-empty Close and signal columns")

    cash = initial_capital
    in_position = False
    entry_time = None
    entry_price = None
    units = 0.0
    trades: list[dict] = []
    equity_list: list[float] = []

    for i in range(len(df)):
        idx = df.index[i]
        close = df["Close"].iloc[i]
        signal = df["signal"].iloc[i]

        if signal == 1 and not in_position:
            units = cash / close
            cash = 0.0
            entry_time = idx
            entry_price = close
            in_position = True

        if signal == -1 and in_position:
            cash += units * close
            exit_price = close
            pnl = (exit_price - entry_price) * units
            return_pct = (exit_price - entry_price) / entry_price * 100
            trades.append({
                "entry_time": entry_time,
                "entry_price": entry_price,
                "exit_time": idx,
                "exit_price": exit_price,
                "pnl": pnl,
                "return_pct": return_pct,
            })
            in_position = False

        if in_position:
            equity = cash + units * close
        else:
            equity = cash
        equity_list.append(equity)

    if in_position:
        last_idx = df.index[-1]
        last_close = df["Close"].iloc[-1]
        cash += units * last_close
        pnl = (last_close - entry_price) * units
        return_pct = (last_close - entry_price) / entry_price * 100
        trades.append({
            "entry_time": entry_time,
            "entry_price": entry_price,
            "exit_time": last_idx,
            "exit_price": last_close,
            "pnl": pnl,
            "return_pct": return_pct,
        })
        equity_list[-1] = cash

    equity_curve = pd.Series(equity_list, index=df.index)
    return (trades, equity_curve)
