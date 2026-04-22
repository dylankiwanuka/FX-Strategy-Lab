"""Typed bundle of last-run results passed into UI rendering."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class ResultsBundle:
    last_df: pd.DataFrame | None
    last_chart_df: pd.DataFrame
    last_trades: list[dict[str, Any]]
    last_equity_curve: pd.Series | None
    last_metrics: dict[str, Any] | None
    last_overlay_cols: list[str]
    last_chart_title: str
    last_strategy: str | None
    last_params: dict[str, Any]
    run_history: list[dict[str, Any]]
