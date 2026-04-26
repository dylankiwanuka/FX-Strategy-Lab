"""Tables: trades and session history."""
from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from ui.helpers.formatting import csv_bytes, num_float, num_int
from ui.helpers.layout import (
    render_centered_button_pair,
    render_centered_table,
    render_section_heading,
    render_wide_button_row,
)
from ui.helpers.postprocess import any_forced_exit


def render_latest_vs_previous_run(run_history: list[dict[str, Any]]) -> None:
    if len(run_history) < 2:
        return
    prev, latest = run_history[-2], run_history[-1]
    ret_p = num_float(prev.get("total_return_pct"))
    ret_l = num_float(latest.get("total_return_pct"))
    dd_p = num_float(prev.get("max_drawdown_pct"))
    dd_l = num_float(latest.get("max_drawdown_pct"))
    nt_p = num_int(prev.get("num_trades"))
    nt_l = num_int(latest.get("num_trades"))

    lines: list[str] = ["**Latest vs previous run**"]
    if ret_l is not None and ret_p is not None:
        d = ret_l - ret_p
        if abs(d) < 1e-9:
            lines.append(f"- Total return was **unchanged** at **{ret_l:.2f}** percentage points.")
        elif d > 0:
            lines.append(f"- Total return **increased** by **{d:.2f}** percentage points vs the previous run.")
        else:
            lines.append(f"- Total return **decreased** by **{abs(d):.2f}** percentage points vs the previous run.")
    if dd_l is not None and dd_p is not None:
        d = dd_l - dd_p
        if abs(d) < 1e-9:
            lines.append(f"- Max drawdown (%) was **unchanged** at **{dd_l:.2f}**%.")
        elif d < 0:
            lines.append(
                f"- Max drawdown **improved** (lower) by **{abs(d):.2f}** percentage points — **less** peak-to-trough risk in % terms."
            )
        else:
            lines.append(
                f"- Max drawdown **worsened** (higher) by **{d:.2f}** percentage points — **more** peak-to-trough risk in % terms."
            )
    if nt_l is not None and nt_p is not None:
        d = nt_l - nt_p
        if d == 0:
            lines.append("- Number of trades was **unchanged**.")
        elif d > 0:
            lines.append(f"- This run produced **{d}** more trade(s) than the previous run.")
        else:
            lines.append(f"- This run produced **{abs(d)}** fewer trade(s) than the previous run.")

    if len(lines) == 1:
        lines.append("- The last two rows do not include comparable return, drawdown, and trade fields.")
    st.markdown("\n".join(lines))


def render_strategy_decisions(
    last_strategy: str | None,
    last_trades: list[dict[str, Any]],
    *,
    download_key: str = "download_latest_trades",
    show_heading: bool = True,
) -> None:
    if show_heading:
        render_section_heading("2) Strategy Decisions", "strategy")
    st.markdown("**Simulated Trades**")
    if last_strategy == "SMA overlay (no trades)":
        st.info(
            "No trades in this mode; this strategy only overlays an indicator. Try **MA crossover backtest**, "
            "**RSI backtest**, or **SMA price cross backtest** to see simulated trades."
        )
    elif len(last_trades) == 0:
        st.warning("No trades were generated. Try a longer date range or adjust strategy parameters.")
    else:
        cap = "Each row is one completed trade (buy then sell)."
        if any_forced_exit(last_trades):
            cap += " Forced exit: the backtest ended while this trade was still open. It was automatically closed at the final bar's price."
        st.caption(cap)
        trades_df = pd.DataFrame(last_trades)
        render_centered_table(trades_df, height=300)
        def _download() -> None:
            st.download_button(
                label="Download trades (CSV)",
                data=csv_bytes(trades_df),
                file_name="latest_trades.csv",
                mime="text/csv",
                key=download_key,
                use_container_width=True,
            )

        render_wide_button_row(_download)


def render_session_summary(
    run_history: list[dict[str, Any]],
    *,
    download_key: str = "download_session_run_summary",
    clear_key: str = "clear_session_history",
) -> None:
    render_section_heading("Session Run Summary", "session")
    if run_history:
        st.caption("Compare runs in-session using the history table below (latest row at bottom).")
        if len(run_history) >= 2:
            render_latest_vs_previous_run(run_history)
        hist_df = pd.DataFrame(run_history)

        def _clear() -> None:
            if st.button("Clear session history", key=clear_key, use_container_width=True):
                st.session_state.run_history = []
                st.rerun()

        def _download() -> None:
            st.download_button(
                label="Download session summary (CSV)",
                data=csv_bytes(hist_df),
                file_name="session_run_summary.csv",
                mime="text/csv",
                key=download_key,
                use_container_width=True,
            )

        render_centered_button_pair(_clear, _download)
        render_centered_table(hist_df, height=300)
    else:
        st.info("No backtest runs saved yet. Run MA crossover, RSI, or SMA price cross backtest to build session history.")
