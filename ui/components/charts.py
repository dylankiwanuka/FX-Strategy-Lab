"""Charts: candlestick market view and equity curve."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.viz.charts import candlestick_with_overlay

from ui.helpers.formatting import csv_bytes, equity_curve_export_df
from ui.helpers.layout import render_centered_chart, render_section_heading, render_wide_button_row


def render_market_movement(
    last_chart_df: pd.DataFrame,
    last_trades: list[dict[str, Any]],
    last_overlay_cols: list[str],
    last_chart_title: str,
    last_strategy: str | None,
    *,
    last_params: dict[str, Any] | None = None,
    checkbox_key: str = "trade_marker_toggle",
    show_heading: bool = True,
) -> None:
    if show_heading:
        render_section_heading("1) Market Movement", "market")
    show_trade_markers = st.checkbox("Show trade markers (recommended)", value=True, key=checkbox_key)

    def _plot() -> None:
        fig = candlestick_with_overlay(last_chart_df, overlay_cols=last_overlay_cols, title=last_chart_title)
        is_backtest = last_strategy in ("MA crossover backtest", "RSI backtest", "SMA price cross backtest")
        if show_trade_markers and last_trades and is_backtest:
            try:
                entry_times = pd.to_datetime([t["entry_time"] for t in last_trades])
                entry_prices = [t["entry_price"] for t in last_trades]
                exit_times = pd.to_datetime([t["exit_time"] for t in last_trades])
                exit_prices = [t["exit_price"] for t in last_trades]
            except Exception:
                entry_times = [t["entry_time"] for t in last_trades]
                entry_prices = [t["entry_price"] for t in last_trades]
                exit_times = [t["exit_time"] for t in last_trades]
                exit_prices = [t["exit_price"] for t in last_trades]
            fig.add_trace(
                go.Scatter(
                    x=entry_times,
                    y=entry_prices,
                    mode="markers",
                    marker=dict(symbol="triangle-up", size=10, color="green", line=dict(color="darkgreen", width=1)),
                    name="Buy",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=exit_times,
                    y=exit_prices,
                    mode="markers",
                    marker=dict(symbol="triangle-down", size=10, color="red", line=dict(color="darkred", width=1)),
                    name="Sell",
                )
            )
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

    render_centered_chart(_plot)

    if last_strategy == "RSI backtest" and "rsi" in last_chart_df.columns:
        rsi_series = last_chart_df["rsi"].dropna()
        if not rsi_series.empty:
            oversold = (last_params or {}).get("oversold", 30.0)
            overbought = (last_params or {}).get("overbought", 70.0)

            def _rsi_panel() -> None:
                rsi_fig = go.Figure()
                rsi_fig.add_trace(
                    go.Scatter(
                        x=rsi_series.index,
                        y=rsi_series.values,
                        mode="lines",
                        name="RSI",
                        line=dict(color="#4c78a8", width=1.6),
                    )
                )
                rsi_fig.add_hline(y=float(oversold), line_dash="dash", line_color="#c0392b", line_width=1)
                rsi_fig.add_hline(y=float(overbought), line_dash="dash", line_color="#b8860b", line_width=1)
                rsi_fig.update_layout(
                    height=180,
                    margin=dict(l=20, r=20, t=24, b=20),
                    showlegend=False,
                    yaxis=dict(range=[0, 100], title="RSI"),
                    xaxis_title=None,
                    title="RSI context (compact)",
                )
                st.plotly_chart(rsi_fig, use_container_width=True)
                st.caption(
                    f"RSI line with thresholds: oversold {float(oversold):.0f}, overbought {float(overbought):.0f}."
                )

            render_centered_chart(_rsi_panel)


def render_equity_section(
    last_equity_curve: pd.Series | None,
    *,
    download_key: str = "download_latest_equity",
    show_heading: bool = True,
) -> None:
    if show_heading:
        render_section_heading("3) Account Value Over Time", "equity")
    if last_equity_curve is not None:
        st.caption(
            "This shows simulated account value over time; dips are drawdowns when the strategy was losing."
        )

        def _line() -> None:
            st.line_chart(last_equity_curve.to_frame("Equity"))

        render_centered_chart(_line)
        eq_export = equity_curve_export_df(last_equity_curve)

        def _download() -> None:
            st.download_button(
                label="Download equity (CSV)",
                data=csv_bytes(eq_export),
                file_name="latest_equity_curve.csv",
                mime="text/csv",
                key=download_key,
                use_container_width=True,
            )

        render_wide_button_row(_download)
    else:
        st.info("Run a backtest strategy (MA crossover or RSI) to see account value over time.")
