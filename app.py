from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data.loader import DataRequest, download_ohlc
from src.data.cleaning import clean_ohlc
from src.indicators.sma import sma
from src.viz.charts import candlestick_with_overlay
from src.strategies.ma_crossover import ma_crossover_signals
from src.strategies.rsi_strategy import rsi_signals
from src.backtest.engine import run_backtest
from src.backtest.metrics import compute_metrics


def _format_calculation_preview(df: pd.DataFrame, cols: list[str], max_rows: int = 8) -> pd.DataFrame:
    """Tail of selected columns with index shown as Date or Index for readability."""
    existing = [c for c in cols if c in df.columns]
    if not existing:
        return pd.DataFrame()
    preview = df[existing].tail(max_rows).copy()
    out = preview.reset_index()
    first = out.columns[0]
    if pd.api.types.is_datetime64_any_dtype(out[first]):
        out = out.rename(columns={first: "Date"})
    else:
        out = out.rename(columns={first: "Index"})
    return out


def _render_how_strategy_calculated() -> None:
    """Educational detail for the last successful run only (session state). Uses last_strategy, last_chart_df, last_overlay_cols, last_params."""
    last_strategy = st.session_state.get("last_strategy")
    last_chart_df = st.session_state.get("last_chart_df")
    if last_strategy is None or last_chart_df is None:
        return
    last_overlay_cols = st.session_state.get("last_overlay_cols") or []
    last_params = st.session_state.get("last_params") or {}

    st.markdown("## How This Strategy Is Calculated")

    if last_strategy == "SMA overlay (no trades)":
        n = last_params.get("sma_window", "?")
        overlay = last_overlay_cols[0] if last_overlay_cols else None
        with st.expander("Formula", expanded=False):
            st.markdown(
                f"- **Simple Moving Average (SMA)** smooths price by averaging the last **{n}** closing prices.\n"
                "- **SMA** = average of closing prices over the selected window."
            )
        with st.expander("Step-by-step logic", expanded=False):
            st.markdown(
                "1. Take **Close** for each bar.\n"
                f"2. Compute a **rolling average** over the last **{n}** closes.\n"
                "3. Plot the SMA on the same chart as price (no trades)."
            )
        with st.expander("Why signals happen", expanded=False):
            st.markdown(
                "This mode **does not generate buy or sell signals**—it is for **visual learning** only. "
                "You compare price to the SMA to see whether price is generally above or below its recent average."
            )
        with st.expander("Calculation preview", expanded=False):
            cols = ["Close"]
            if overlay and overlay in last_chart_df.columns:
                cols.append(overlay)
            prev = _format_calculation_preview(last_chart_df, cols)
            if prev.empty:
                st.caption("No preview columns available for this run.")
            else:
                st.dataframe(prev, use_container_width=True)


def enforce_intraday_limits(start_str: str, end_str: str, interval: str) -> tuple[str, str, str | None]:
    """
    Intraday intervals (like 1h) can fail if the date range is too old.
    This keeps the start date within the last ~730 days for intraday requests.
    Returns (start, end, warning_message).
    """
    intraday_intervals = {"1h", "30m", "15m", "5m", "1m"}
    if interval not in intraday_intervals:
        return start_str, end_str, None

    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%d")
        end_dt = datetime.strptime(end_str, "%Y-%m-%d")
    except ValueError:
        return start_str, end_str, "Invalid date format. Use YYYY-MM-DD."

    max_lookback = datetime.today() - timedelta(days=729)

    if start_dt < max_lookback:
        new_start = max_lookback.strftime("%Y-%m-%d")
        return new_start, end_str, f"For {interval} data, start date was adjusted to {new_start}."

    if end_dt <= start_dt:
        return start_str, end_str, "End date must be after start date."

    return start_str, end_str, None


def _clear_results_state():
    st.session_state.last_ran = False
    st.session_state.last_strategy = None
    st.session_state.last_params = None
    st.session_state.last_df = None
    st.session_state.last_chart_df = None
    st.session_state.last_trades = []
    st.session_state.last_equity_curve = None
    st.session_state.last_metrics = None
    st.session_state.last_overlay_cols = []
    st.session_state.last_chart_title = ""


_SESSION_DEFAULTS = {
    "last_ran": False,
    "last_strategy": None,
    "last_params": None,
    "last_df": None,
    "last_chart_df": None,
    "last_trades": [],
    "last_equity_curve": None,
    "last_metrics": None,
    "last_overlay_cols": [],
    "last_chart_title": "",
    "run_history": [],
}
for _k, _v in _SESSION_DEFAULTS.items():
    st.session_state.setdefault(_k, _v)

st.set_page_config(page_title="FX Strategy Lab", layout="wide")

st.title("FX Strategy Lab")
st.caption("Learn how simple trading strategies behave using historical FX data.")

st.sidebar.header("Data Settings")

symbol = st.sidebar.selectbox(
    "Currency pair (Yahoo Finance ticker)",
    ["EURUSD=X", "GBPUSD=X", "USDJPY=X"],
    index=0,
    help="The FX pair to load. Yahoo Finance ticker (e.g. EURUSD=X).",
)

start = st.sidebar.text_input(
    "Start date (YYYY-MM-DD)",
    value="2024-01-01",
    help="Start of the date range for historical data.",
)
end = st.sidebar.text_input(
    "End date (YYYY-MM-DD)",
    value="2024-03-01",
    help="End of the date range for historical data.",
)

interval = st.sidebar.selectbox(
    "Interval",
    ["1d", "1h"],
    index=0,
    help="Bar size: 1d = daily, 1h = hourly. Shorter intervals use more data.",
)

start, end, warning = enforce_intraday_limits(start, end, interval)
if warning:
    st.sidebar.warning(warning)

st.sidebar.header("Indicator Settings")
sma_window = st.sidebar.slider(
    "SMA window",
    min_value=5,
    max_value=60,
    value=20,
    step=1,
    help="Number of bars for the moving average. Larger = smoother, slower to react.",
)

strategy = st.sidebar.selectbox(
    "Strategy",
    ["SMA overlay (no trades)", "MA crossover backtest", "RSI backtest"],
    index=0,
    help="SMA overlay only plots price and MA. MA crossover and RSI run a full backtest with trades.",
)

if strategy == "MA crossover backtest":
    fast_window = st.sidebar.slider(
        "Fast window",
        min_value=5,
        max_value=50,
        value=10,
        step=1,
        help="Length of the fast moving average in bars. Must be less than slow window.",
    )
    slow_window = st.sidebar.slider(
        "Slow window",
        min_value=10,
        max_value=100,
        value=20,
        step=1,
        help="Length of the slow moving average in bars.",
    )
    ma_type = st.sidebar.selectbox(
        "MA type",
        ["SMA", "EMA"],
        index=0,
        help="SMA = simple average. EMA gives more weight to recent prices.",
    )
elif strategy == "RSI backtest":
    period = st.sidebar.number_input(
        "RSI period",
        min_value=2,
        max_value=50,
        value=14,
        step=1,
        help="Lookback length for RSI (e.g. 14). Higher = smoother RSI.",
    )
    oversold = st.sidebar.number_input(
        "Oversold",
        min_value=1.0,
        max_value=50.0,
        value=30.0,
        step=1.0,
        help="RSI level below which the strategy buys (oversold).",
    )
    overbought = st.sidebar.number_input(
        "Overbought",
        min_value=50.0,
        max_value=99.0,
        value=70.0,
        step=1.0,
        help="RSI level above which the strategy sells (overbought).",
    )

run = st.sidebar.button("Run Simulation")
st.sidebar.caption("Load data and run the selected strategy. Results appear below.")

if run and strategy == "MA crossover backtest" and fast_window >= slow_window:
    st.sidebar.error("fast_window must be less than slow_window")
    st.stop()
if run and strategy == "RSI backtest" and oversold >= overbought:
    st.sidebar.error("oversold must be less than overbought")
    st.stop()

st.markdown("**How it works**")
st.markdown(
    "- Pick a currency pair, date range, and interval in the sidebar.\n"
    "- Choose a strategy and click **Run Simulation** to load data and run it.\n"
    "- Read the five sections below to see price, trades, account value, performance, and reflection prompts."
)
st.divider()

st.subheader("What this strategy is doing")
if strategy == "SMA overlay (no trades)":
    st.markdown(
        "Plots **price with a simple moving average (SMA)**. No trades are simulated—visualisation only. "
        "Parameters: **SMA window** (number of bars). Works best when you want to see price relative to an average."
    )
elif strategy == "MA crossover backtest":
    st.markdown(
        "**Buys** when the fast MA crosses above the slow; **sells** when it crosses below. "
        "Parameters: **fast window**, **slow window**, **MA type** (SMA or EMA). "
        "Tends to work in trending markets; can give false signals in choppy or sideways markets."
    )
else:
    st.markdown(
        "**Buys** when RSI is below oversold; **sells** when RSI is above overbought. "
        "Parameters: **period**, **oversold**, **overbought**. "
        "Works when price reverses from extremes; can struggle in strong trends where RSI stays extreme."
    )
st.divider()

if run:
    try:
        req = DataRequest(symbol=symbol, start=start, end=end, interval=interval)
        raw = download_ohlc(req)
        df = clean_ohlc(raw)

        if df is None or len(df) == 0:
            _clear_results_state()
            st.error("No data returned for the selected settings.")
        else:
            trades = []
            equity_curve = None
            metrics = None
            chart_df = df
            overlay_cols = []
            chart_title = f"{symbol} ({interval})"

            if strategy == "SMA overlay (no trades)":
                sma_col = f"SMA_{sma_window}"
                df[sma_col] = sma(df["Close"], sma_window)
                chart_df = df
                overlay_cols = [sma_col]
                chart_title = f"{symbol} ({interval}) with {sma_col}"
            elif strategy == "MA crossover backtest":
                df_sig = ma_crossover_signals(df, fast_window=fast_window, slow_window=slow_window, ma_type=ma_type)
                trades, equity_curve = run_backtest(df_sig)
                metrics = compute_metrics(trades, equity_curve)
                chart_df = df_sig
                overlay_cols = ["fast_ma", "slow_ma"]
                chart_title = f"{symbol} ({interval}) MA crossover"
            elif strategy == "RSI backtest":
                df_sig = rsi_signals(df, period=period, oversold=oversold, overbought=overbought)
                trades, equity_curve = run_backtest(df_sig)
                metrics = compute_metrics(trades, equity_curve)
                chart_df = df_sig
                overlay_cols = []
                chart_title = f"{symbol} ({interval})"

            if strategy in ("MA crossover backtest", "RSI backtest") and metrics is not None:
                summary_row = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol": symbol,
                    "interval": interval,
                    "start": start,
                    "end": end,
                    "strategy": strategy,
                    "fast_window": fast_window if strategy == "MA crossover backtest" else None,
                    "slow_window": slow_window if strategy == "MA crossover backtest" else None,
                    "ma_type": ma_type if strategy == "MA crossover backtest" else None,
                    "period": period if strategy == "RSI backtest" else None,
                    "oversold": oversold if strategy == "RSI backtest" else None,
                    "overbought": overbought if strategy == "RSI backtest" else None,
                    "total_return_pct": round(metrics["total_return_pct"], 2),
                    "num_trades": metrics["num_trades"],
                    "win_rate_pct": round(metrics["win_rate_pct"], 2),
                    "max_drawdown_pct": round(metrics["max_drawdown_pct"], 2),
                }
                st.session_state.run_history.append(summary_row)

            if strategy == "SMA overlay (no trades)":
                st.session_state.last_params = {"sma_window": sma_window}
            elif strategy == "MA crossover backtest":
                st.session_state.last_params = {
                    "fast_window": fast_window,
                    "slow_window": slow_window,
                    "ma_type": ma_type,
                }
            elif strategy == "RSI backtest":
                st.session_state.last_params = {
                    "period": period,
                    "oversold": oversold,
                    "overbought": overbought,
                }

            st.session_state.last_ran = True
            st.session_state.last_strategy = strategy
            st.session_state.last_df = df
            st.session_state.last_chart_df = chart_df
            st.session_state.last_trades = trades
            st.session_state.last_equity_curve = equity_curve
            st.session_state.last_metrics = metrics
            st.session_state.last_overlay_cols = overlay_cols
            st.session_state.last_chart_title = chart_title

    except Exception as e:
        _clear_results_state()
        st.error("Could not retrieve data with the selected settings.")
        st.caption(f"Details: {e}")
        if interval == "1h":
            st.info("Try interval = 1d or choose a more recent date range for intraday data.")

if (
    st.session_state.last_ran
    and st.session_state.get("last_chart_df") is not None
):
    last_df = st.session_state.get("last_df")
    last_chart_df = st.session_state.last_chart_df
    last_trades = st.session_state.get("last_trades") or []
    last_equity_curve = st.session_state.get("last_equity_curve")
    last_metrics = st.session_state.get("last_metrics")
    last_overlay_cols = st.session_state.get("last_overlay_cols") or []
    last_chart_title = st.session_state.get("last_chart_title") or ""
    last_strategy = st.session_state.get("last_strategy")

    if last_df is not None and len(last_df) > 0:
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", f"{len(last_df):,}")
        c2.metric("From", str(last_df.index.min())[:10])
        c3.metric("To", str(last_df.index.max())[:10])
    st.write("")

    _render_how_strategy_calculated()
    st.divider()
    st.write("")

    st.markdown("## 1) Market Movement")
    show_trade_markers = st.checkbox("Show trade markers (recommended)", value=True, key="trade_marker_toggle")
    fig = candlestick_with_overlay(last_chart_df, overlay_cols=last_overlay_cols, title=last_chart_title)
    is_backtest = last_strategy in ("MA crossover backtest", "RSI backtest")
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
    st.divider()
    st.write("")

    st.markdown("## 2) Strategy Decisions")
    st.markdown("**Simulated Trades**")
    st.caption("Each row is one completed trade (buy then sell).")
    if last_strategy == "SMA overlay (no trades)":
        st.info("No trades in this mode; this strategy only overlays an indicator. Try **MA crossover backtest** or **RSI backtest** to see simulated trades.")
    elif len(last_trades) == 0:
        st.warning("No trades were generated. Try a longer date range or adjust strategy parameters.")
    else:
        st.dataframe(pd.DataFrame(last_trades))
    st.divider()
    st.write("")

    st.markdown("## 3) Account Value Over Time")
    if last_equity_curve is not None:
        st.caption("Account value over time starting from a set initial capital. Dips are drawdowns—periods when the strategy was losing.")
        st.line_chart(last_equity_curve.to_frame("Equity"))
    else:
        st.info("Run a backtest strategy (MA crossover or RSI) to see account value over time.")
    st.divider()
    st.write("")

    st.markdown("## 4) Performance Summary")
    if last_metrics is not None:
        r1, r2, r3 = st.columns(3)
        r1.metric("Total return (%)", f"{last_metrics['total_return_pct']:.2f}%")
        r2.metric("Num trades", last_metrics["num_trades"])
        r3.metric("Win rate (%)", f"{last_metrics['win_rate_pct']:.2f}%")
        r4, r5, r6 = st.columns(3)
        r4.metric("Avg trade return (%)", f"{last_metrics['avg_trade_return_pct']:.2f}%")
        r5.metric("Max drawdown (%)", f"{last_metrics['max_drawdown_pct']:.2f}%")
        r6.metric("Max drawdown (value)", f"{last_metrics['max_drawdown_value']:.2f}")
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
    st.divider()
    st.write("")

    st.markdown("## Session Run Summary")
    if st.button("Clear session history"):
        st.session_state.run_history = []
        st.rerun()

    if st.session_state.run_history:
        st.caption("Completed backtest runs in this session (latest at bottom).")
        st.dataframe(pd.DataFrame(st.session_state.run_history), use_container_width=True)
    else:
        st.info("No backtest runs saved yet. Run MA crossover or RSI backtest to build session history.")
    st.divider()
    st.write("")

    st.markdown("## 5) What This Means")
    st.markdown(
        "- **Win rate vs return**: Can you have a high win rate but still lose money? (Think about size of wins vs losses.)\n"
        "- **Drawdown**: How would a large drawdown feel in real trading? Could you hold through it?\n"
        "- **Trends vs sideways**: Do you think this strategy would do better in trending or sideways markets?\n"
        "- **Parameters**: What happens if you change fast/slow windows or RSI levels? Try different settings and compare."
    )

    with st.expander("Show latest data table (advanced)"):
        st.dataframe(last_chart_df.tail(25))

else:
    st.info("Choose settings in the sidebar and click Run.")
    st.markdown(
        """
        **Example settings:**
        - Interval: `1d`
        - Pair: `EURUSD=X`
        - Range: `2024-01-01` to `2024-03-01`
        - SMA: `20`
        """
    )
    