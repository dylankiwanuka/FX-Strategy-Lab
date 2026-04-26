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
        fast_window = params.get("fast_window")
        slow_window = params.get("slow_window")
        if fast_window is None or slow_window is None:
            raise ValueError(
                "MA crossover requires 'fast_window' and 'slow_window' in params"
            )
        ma_type = params.get("ma_type", "SMA")
        chart_df = ma_crossover_signals(
            df,
            fast_window=fast_window,
            slow_window=slow_window,
            ma_type=ma_type,
        )
        overlay_cols = ["fast_ma", "slow_ma"]
        chart_title = f"{symbol} ({interval}) MA crossover"
    elif strategy == "RSI backtest":
        period = params.get("period")
        oversold = params.get("oversold")
        overbought = params.get("overbought")
        if any(v is None for v in [period, oversold, overbought]):
            raise ValueError(
                "RSI strategy requires 'period', 'oversold', and 'overbought' in params"
            )
        chart_df = rsi_signals(
            df,
            period=period,
            oversold=oversold,
            overbought=overbought,
        )
        overlay_cols = []
        chart_title = f"{symbol} ({interval}) RSI"
    elif strategy == "SMA price cross backtest":
        window = params.get("window")
        if window is None:
            raise ValueError(
                "SMA price cross requires 'window' in params"
            )
        chart_df = sma_price_cross_signals(df, window=window)
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
