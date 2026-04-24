from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def candlestick_with_overlay(df: pd.DataFrame, overlay_cols: list[str], title: str) -> go.Figure:
    """Plot OHLC candles with optional indicator overlays on a shared time axis."""
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC",
        )
    )

    for col in overlay_cols:
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[col],
                    mode="lines",
                    name=col,
                )
            )

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,  # slider adds clutter for the short ranges this tool uses
        height=650,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig
