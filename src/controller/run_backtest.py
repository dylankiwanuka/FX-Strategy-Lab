"""Pipeline orchestration for the full backtesting workflow with no Streamlit dependency."""
from __future__ import annotations

import pandas as pd

from src.backtest.engine import run_backtest
from src.backtest.metrics import compute_metrics
from src.data.cleaning import clean_ohlc
from src.data.loader import DataRequest, download_ohlc
from src.strategies.ma_crossover import ma_crossover_signals
from src.strategies.rsi_strategy import rsi_signals
from src.strategies.sma_price_cross import sma_price_cross_signals


def execute_backtest_pipeline(
    symbol: str,
    start: str,
    end: str,
    interval: str,
    strategy: str,
    params: dict,
) -> dict:
    """Runs download through metrics for 'MA crossover backtest', 'RSI backtest', or 'SMA price cross backtest', returning a dict with df, chart_df, trades, equity_curve, metrics, overlay_cols, and chart_title."""
    req = DataRequest(symbol=symbol, start=start, end=end, interval=interval)
    raw = download_ohlc(req)
    df = clean_ohlc(raw)

    if strategy == "MA crossover backtest":
        chart_df = ma_crossover_signals(
            df,
            fast_window=params["fast_window"],
            slow_window=params["slow_window"],
            ma_type=params.get("ma_type", "SMA"),
        )
        overlay_cols = ["fast_ma", "slow_ma"]
        chart_title = f"{symbol} ({interval}) MA crossover"
    elif strategy == "RSI backtest":
        chart_df = rsi_signals(
            df,
            period=params["period"],
            oversold=params["oversold"],
            overbought=params["overbought"],
        )
        overlay_cols = []
        chart_title = f"{symbol} ({interval}) RSI"
    elif strategy == "SMA price cross backtest":
        chart_df = sma_price_cross_signals(df, window=params["window"])
        overlay_cols = ["sma"]
        chart_title = f"{symbol} ({interval}) SMA price cross"
    else:
        raise ValueError(f"Unrecognised strategy: {strategy!r}")

    trades, equity_curve = run_backtest(chart_df)
    metrics_dict = compute_metrics(trades, equity_curve)

    return {
        "df": df,
        "chart_df": chart_df,
        "trades": trades,
        "equity_curve": equity_curve,
        "metrics": metrics_dict,
        "overlay_cols": overlay_cols,
        "chart_title": chart_title,
    }
