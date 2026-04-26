from __future__ import annotations

from datetime import datetime, timedelta

import streamlit as st

st.set_page_config(page_title="FX Strategy Lab", layout="wide")

from src.backtest.engine import run_backtest
from src.backtest.metrics import compute_metrics
from src.data.cleaning import clean_ohlc
from src.data.loader import DataRequest, download_ohlc
from src.indicators.sma import sma
from src.strategies.ma_crossover import ma_crossover_signals
from src.strategies.rsi_strategy import rsi_signals
from src.strategies.sma_price_cross import sma_price_cross_signals
from ui.app_logic.modes import DEFAULT_LEARNING_MODE, get_mode, render_mode_selector
from ui.app_logic.renderer import render_main_content
from ui.helpers.bundle import ResultsBundle
from ui.helpers.layout import render_app_header
from ui.helpers.postprocess import annotate_forced_exit_trades


def enforce_intraday_limits(start_str: str, end_str: str, interval: str) -> tuple[str, str, str | None]:
    """Clamps intraday start dates to roughly the last 730 days and returns (start, end, warning_message)."""
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


def _clear_results_state() -> None:
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
    "learning_mode": DEFAULT_LEARNING_MODE,
    "step": 0,
}
# setdefault in a loop avoids overwriting state that already exists — Streamlit reruns the whole
# script on every interaction so direct assignment would reset live session data between renders.
for _k, _v in _SESSION_DEFAULTS.items():
    st.session_state.setdefault(_k, _v)

render_app_header("FX Strategy Lab", "Learn how simple trading strategies behave using historical FX data.")

render_mode_selector()

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

if end <= start:
    st.error(
        "The selected date range is too narrow or invalid after adjusting "
        "for intraday interval limits. Please choose a more recent or "
        "wider date range."
    )
    st.stop()

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
    ["SMA overlay (no trades)", "MA crossover backtest", "RSI backtest", "SMA price cross backtest"],
    index=0,
    help="SMA overlay only plots price and MA. MA crossover, RSI, and SMA price cross run a full backtest with trades.",
)

sma_cross_window = 20

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
    st.sidebar.caption("Lower values = fewer buy signals. Default: 30.")
    overbought = st.sidebar.number_input(
        "Overbought",
        min_value=50.0,
        max_value=99.0,
        value=70.0,
        step=1.0,
        help="RSI level above which the strategy sells (overbought).",
    )
    st.sidebar.caption("Higher values = fewer sell signals. Default: 70.")
elif strategy == "SMA price cross backtest":
    sma_cross_window = st.sidebar.slider(
        "SMA window",
        min_value=5,
        max_value=100,
        value=20,
        step=1,
        help="Price must cross this moving average to trigger a signal.",
    )

run = st.sidebar.button("Run Simulation")
st.sidebar.caption("Load data and run the selected strategy. Results appear below.")

if run and strategy == "MA crossover backtest" and fast_window >= slow_window:
    st.sidebar.error("fast_window must be less than slow_window")
    st.stop()
if run and strategy == "RSI backtest" and oversold >= overbought:
    st.sidebar.error("oversold must be less than overbought")
    st.stop()

if run:
    try:
        req = DataRequest(symbol=symbol, start=start, end=end, interval=interval)
        raw = download_ohlc(req)
        df = clean_ohlc(raw)

        if df is None or len(df) == 0:
            _clear_results_state()
            st.error("No data was returned for this combination of currency pair, date range, and interval. If you selected an hourly interval, try a more recent date range (yfinance limits intraday data to the last 730 days).")
        else:
            trades: list = []
            equity_curve = None
            metrics = None
            chart_df = df
            overlay_cols: list[str] = []
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
                trades = annotate_forced_exit_trades(trades, df_sig)
                metrics = compute_metrics(trades, equity_curve)
                chart_df = df_sig
                overlay_cols = ["fast_ma", "slow_ma"]
                chart_title = f"{symbol} ({interval}) MA crossover"
            elif strategy == "RSI backtest":
                df_sig = rsi_signals(df, period=period, oversold=oversold, overbought=overbought)
                trades, equity_curve = run_backtest(df_sig)
                trades = annotate_forced_exit_trades(trades, df_sig)
                metrics = compute_metrics(trades, equity_curve)
                chart_df = df_sig
                overlay_cols = []
                chart_title = f"{symbol} ({interval})"
            elif strategy == "SMA price cross backtest":
                df_sig = sma_price_cross_signals(df, window=sma_cross_window)
                trades, equity_curve = run_backtest(df_sig)
                trades = annotate_forced_exit_trades(trades, df_sig)
                metrics = compute_metrics(trades, equity_curve)
                chart_df = df_sig
                overlay_cols = ["sma"]
                chart_title = f"{symbol} ({interval}) SMA price cross"

            if strategy in (
                "MA crossover backtest",
                "RSI backtest",
                "SMA price cross backtest",
            ) and metrics is not None:
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
                    "window": sma_cross_window if strategy == "SMA price cross backtest" else None,
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
            elif strategy == "SMA price cross backtest":
                st.session_state.last_params = {"window": sma_cross_window}

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

mode = get_mode()
bundle: ResultsBundle | None = None
if st.session_state.last_ran and st.session_state.get("last_chart_df") is not None:
    bundle = ResultsBundle(
        last_df=st.session_state.get("last_df"),
        last_chart_df=st.session_state.last_chart_df,
        last_trades=st.session_state.get("last_trades") or [],
        last_equity_curve=st.session_state.get("last_equity_curve"),
        last_metrics=st.session_state.get("last_metrics"),
        last_overlay_cols=st.session_state.get("last_overlay_cols") or [],
        last_chart_title=st.session_state.get("last_chart_title") or "",
        last_strategy=st.session_state.get("last_strategy"),
        last_params=st.session_state.get("last_params") or {},
        run_history=st.session_state.get("run_history") or [],
    )

render_main_content(mode, bundle, strategy)
