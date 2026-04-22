"""Performance metrics section."""
from __future__ import annotations

import html
from typing import Any

import streamlit as st

from ui.helpers.layout import centered_main_block, render_section_heading_centered

_GOOD = "#15803d"
_BAD = "#b91c1c"
_NEUTRAL = "#1e293b"
_MUTED = "#64748b"


def _span_val(text: str, color: str | None) -> str:
    if color is None:
        return html.escape(text)
    return f'<span style="color:{color};font-weight:600;">{html.escape(text)}</span>'


def _color_total_return(v: float) -> str | None:
    if v > 0:
        return _GOOD
    if v < 0:
        return _BAD
    return None


def _color_win_rate(v: float) -> str | None:
    if v >= 55:
        return _GOOD
    if v <= 45:
        return _BAD
    return None


def _color_avg_trade(v: float) -> str | None:
    if v > 0:
        return _GOOD
    if v < 0:
        return _BAD
    return None


def _color_drawdown_pct(v: float) -> str | None:
    if v > 0:
        return _BAD
    if v == 0:
        return _GOOD
    return None


def _metric_cell(label: str, value_html: str) -> str:
    safe_label = html.escape(label)
    return (
        '<div style="text-align:center;width:100%;box-sizing:border-box;">'
        f'<p style="margin:0;font-size:0.95rem;color:{_MUTED};">{safe_label}</p>'
        f'<p style="margin:0.22rem 0 0 0;font-size:1.62rem;color:{_NEUTRAL};">{value_html}</p>'
        "</div>"
    )


def _embedded_metrics_grid_html(
    *,
    total_return: float,
    win_rate: float,
    avg_trade: float,
    max_dd: float,
    max_dd_val: float,
    num_trades: Any,
) -> str:
    """HTML-only 3x2 grid (no st.columns) for use inside nested Streamlit columns."""
    tr_s = f"{total_return:.2f}%"
    wr_s = f"{win_rate:.2f}%"
    at_s = f"{avg_trade:.2f}%"
    dd_s = f"{max_dd:.2f}%"
    ddv_s = f"{max_dd_val:.2f}"
    nt_s = str(num_trades)

    cells = [
        _metric_cell("Total return (%)", _span_val(tr_s, _color_total_return(total_return))),
        _metric_cell("Num trades", _span_val(nt_s, None)),
        _metric_cell("Win rate (%)", _span_val(wr_s, _color_win_rate(win_rate))),
        _metric_cell("Avg trade return (%)", _span_val(at_s, _color_avg_trade(avg_trade))),
        _metric_cell("Max drawdown (%)", _span_val(dd_s, _color_drawdown_pct(max_dd))),
        _metric_cell("Max drawdown (value)", _span_val(ddv_s, None)),
    ]
    inner = "".join(f'<div style="min-width:0;">{c}</div>' for c in cells)
    return (
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);'
        'gap:0.35rem 0.5rem;width:100%;">'
        f"{inner}</div>"
    )


def render_performance_summary(
    last_metrics: dict[str, Any] | None,
    *,
    show_heading: bool = True,
    show_details_expander: bool = True,
    nested_in_column: bool = False,
) -> None:
    """When nested_in_column=True, skip Streamlit columns (Tutor shell is already inside a column)."""

    def _caption() -> None:
        st.markdown(
            "<p style='text-align:center;margin:0 0 0.5rem 0;color:#64748b;font-size:0.9rem;'>"
            "You can see return and drawdown together—both matter for risk."
            "</p>",
            unsafe_allow_html=True,
        )

    if nested_in_column:
        if show_heading:
            render_section_heading_centered("4) Performance Summary", "performance")
        _caption()
        if last_metrics is not None:
            total_return = float(last_metrics["total_return_pct"])
            win_rate = float(last_metrics["win_rate_pct"])
            avg_trade = float(last_metrics["avg_trade_return_pct"])
            max_dd = float(last_metrics["max_drawdown_pct"])
            max_dd_val = float(last_metrics["max_drawdown_value"])
            num_trades = last_metrics["num_trades"]
            st.markdown(
                _embedded_metrics_grid_html(
                    total_return=total_return,
                    win_rate=win_rate,
                    avg_trade=avg_trade,
                    max_dd=max_dd,
                    max_dd_val=max_dd_val,
                    num_trades=num_trades,
                ),
                unsafe_allow_html=True,
            )
            if show_details_expander:
                with st.expander("What do these metrics mean?"):
                    st.markdown(
                        "- **Total return (%)**: Percentage gain or loss over the whole period.\n"
                        "- **Num trades**: Number of round-trip trades (buy then sell).\n"
                        "- **Win rate (%)**: Percentage of trades that made a profit.\n"
                        "- **Avg trade return (%)**: Average percentage return per trade.\n"
                        "- **Max drawdown (%)**: Largest peak-to-trough decline as a percentage.\n"
                        "- **Max drawdown (value)**: Largest peak-to-trough decline in account units (negative number)."
                    )
        else:
            st.info("Performance metrics are available when you run a backtest strategy (MA crossover or RSI).")
        return

    with centered_main_block():
        if show_heading:
            render_section_heading_centered("4) Performance Summary", "performance")
        _caption()
        if last_metrics is not None:
            total_return = float(last_metrics["total_return_pct"])
            win_rate = float(last_metrics["win_rate_pct"])
            avg_trade = float(last_metrics["avg_trade_return_pct"])
            max_dd = float(last_metrics["max_drawdown_pct"])
            max_dd_val = float(last_metrics["max_drawdown_value"])
            num_trades = last_metrics["num_trades"]

            tr_s = f"{total_return:.2f}%"
            wr_s = f"{win_rate:.2f}%"
            at_s = f"{avg_trade:.2f}%"
            dd_s = f"{max_dd:.2f}%"
            ddv_s = f"{max_dd_val:.2f}"
            nt_s = str(num_trades)

            r1, r2, r3 = st.columns([1, 1, 1])
            r1.markdown(
                _metric_cell("Total return (%)", _span_val(tr_s, _color_total_return(total_return))),
                unsafe_allow_html=True,
            )
            r2.markdown(_metric_cell("Num trades", _span_val(nt_s, None)), unsafe_allow_html=True)
            r3.markdown(
                _metric_cell("Win rate (%)", _span_val(wr_s, _color_win_rate(win_rate))),
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            r4, r5, r6 = st.columns([1, 1, 1])
            r4.markdown(
                _metric_cell("Avg trade return (%)", _span_val(at_s, _color_avg_trade(avg_trade))),
                unsafe_allow_html=True,
            )
            r5.markdown(
                _metric_cell("Max drawdown (%)", _span_val(dd_s, _color_drawdown_pct(max_dd))),
                unsafe_allow_html=True,
            )
            r6.markdown(_metric_cell("Max drawdown (value)", _span_val(ddv_s, None)), unsafe_allow_html=True)

            if show_details_expander:
                with st.expander("What do these metrics mean?"):
                    st.markdown(
                        "- **Total return (%)**: Percentage gain or loss over the whole period.\n"
                        "- **Num trades**: Number of round-trip trades (buy then sell).\n"
                        "- **Win rate (%)**: Percentage of trades that made a profit.\n"
                        "- **Avg trade return (%)**: Average percentage return per trade.\n"
                        "- **Max drawdown (%)**: Largest peak-to-trough decline as a percentage.\n"
                        "- **Max drawdown (value)**: Largest peak-to-trough decline in account units (negative number)."
                    )
        else:
            st.info("Performance metrics are available when you run a backtest strategy (MA crossover or RSI).")
