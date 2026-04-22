"""App-layer post-processing of backtest outputs (does not modify src/)."""
from __future__ import annotations

import pandas as pd


def _index_equal(a: object, b: object) -> bool:
    try:
        return bool(pd.Timestamp(a) == pd.Timestamp(b))
    except (TypeError, ValueError):
        return a == b


def annotate_forced_exit_trades(trades: list[dict], chart_df: pd.DataFrame | None) -> list[dict]:
    """
    Mark the last trade with forced_exit=True when exit is on the final bar without a sell
    signal on that bar (engine flattening an open position).
    """
    if not trades or chart_df is None or len(chart_df) == 0:
        return [dict(t) for t in trades]
    out = [dict(t) for t in trades]
    last_idx = chart_df.index[-1]
    last = out[-1]
    exit_time = last.get("exit_time")
    if not _index_equal(exit_time, last_idx):
        return out
    forced = True
    if "signal" in chart_df.columns:
        try:
            if int(chart_df["signal"].iloc[-1]) == -1:
                forced = False
        except (TypeError, ValueError, IndexError):
            pass
    if forced:
        last["forced_exit"] = True
    return out


def any_forced_exit(trades: list[dict]) -> bool:
    return any(bool(t.get("forced_exit")) for t in trades)
