from __future__ import annotations

from datetime import datetime, timedelta

import streamlit as st

from src.data.loader import DataRequest, download_ohlc
from src.data.cleaning import clean_ohlc
from src.indicators.sma import sma
from src.viz.charts import candlestick_with_overlay


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


st.set_page_config(page_title="FX Tool (MVP)", layout="wide")

st.title("Forex Strategy Backtesting & Visualisation Tool (MVP)")
st.caption("Data retrieval + cleaning + SMA overlay chart")

st.sidebar.header("Data Settings")

symbol = st.sidebar.selectbox(
    "Currency pair (Yahoo Finance ticker)",
    ["EURUSD=X", "GBPUSD=X", "USDJPY=X"],
    index=0,
)

start = st.sidebar.text_input("Start date (YYYY-MM-DD)", value="2024-01-01")
end = st.sidebar.text_input("End date (YYYY-MM-DD)", value="2024-03-01")

interval = st.sidebar.selectbox("Interval", ["1d", "1h"], index=0)

start, end, warning = enforce_intraday_limits(start, end, interval)
if warning:
    st.sidebar.warning(warning)

st.sidebar.header("Indicator Settings")
sma_window = st.sidebar.slider("SMA window", min_value=5, max_value=60, value=20, step=1)

run = st.sidebar.button("Run")

if run:
    try:
        req = DataRequest(symbol=symbol, start=start, end=end, interval=interval)
        raw = download_ohlc(req)
        df = clean_ohlc(raw)

        sma_col = f"SMA_{sma_window}"
        df[sma_col] = sma(df["Close"], sma_window)

        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", f"{len(df):,}")
        c2.metric("From", str(df.index.min())[:10])
        c3.metric("To", str(df.index.max())[:10])

        st.subheader("Chart")
        fig = candlestick_with_overlay(
            df,
            overlay_cols=[sma_col],
            title=f"{symbol} ({interval}) with {sma_col}",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Latest data")
        st.dataframe(df.tail(25))

    except Exception as e:
        st.error("Could not retrieve data with the selected settings.")
        st.caption(f"Details: {e}")
        if interval == "1h":
            st.info("Try interval = 1d or choose a more recent date range for intraday data.")
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
