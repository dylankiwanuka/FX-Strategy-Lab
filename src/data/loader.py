from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import yfinance as yf


@dataclass(frozen=True)
class DataRequest:
    """Parameters for a single Yahoo Finance OHLC download request."""

    symbol: str          # e.g. "EURUSD=X"
    start: str           # "YYYY-MM-DD"
    end: str             # "YYYY-MM-DD"
    interval: str = "1d" # "1d" or "1h"


def download_ohlc(request: DataRequest) -> pd.DataFrame:
    """
    Downloads OHLC price data using yfinance.
    Returns a DataFrame with columns: Open, High, Low, Close and a datetime index.
    """
    df = yf.download(
        tickers=request.symbol,
        start=request.start,
        end=request.end,
        interval=request.interval,
        auto_adjust=False,  # keep raw OHLC so the backtest uses prices traders would have seen
        progress=False,
        threads=True,
    )

    if df is None or df.empty:
        raise ValueError(
            f"No data returned for {request.symbol} "
            f"({request.start} to {request.end}, interval={request.interval})."
        )

    # yfinance column layout changed across versions — flatten whether it is flat or MultiIndex.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    required = ["Open", "High", "Low", "Close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}. Got: {list(df.columns)}")

    df = df[required].copy()

    df.index = pd.to_datetime(df.index)
    df.index.name = "Datetime"

    # Removes column name like "Price" if it appears
    df.columns.name = None

    return df
