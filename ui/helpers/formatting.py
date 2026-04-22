"""Pure formatting helpers for previews and CSV exports (no Streamlit)."""
from __future__ import annotations

import html

import pandas as pd

_SECTION_TONES: dict[str, dict[str, str]] = {
    "edu": {"bg": "#e8f1fb", "border": "#3d6fa8"},
    "market": {"bg": "#efe8f7", "border": "#5c4d8a"},
    "strategy": {"bg": "#fdf3e4", "border": "#b87a2c"},
    "equity": {"bg": "#e6f4f2", "border": "#2d7a6e"},
    "performance": {"bg": "#e8f5e9", "border": "#3a7d44"},
    "session": {"bg": "#f5f0e4", "border": "#8a7030"},
    "reflect": {"bg": "#f8eaea", "border": "#a14d4d"},
}


def section_heading_html(title: str, tone: str) -> str:
    """Build a small HTML heading block for a section tone."""
    colors = _SECTION_TONES.get(tone, _SECTION_TONES["edu"])
    safe = html.escape(title)
    return (
        f'<div style="background:{colors["bg"]};border-left:4px solid {colors["border"]};'
        f"padding:0.45rem 0.75rem;border-radius:6px;margin:0.35rem 0 0.55rem 0;"
        f'"><h2 style="margin:0;font-size:1.12rem;font-weight:600;color:#1a1a1a;">{safe}</h2></div>'
    )


def rename_first_index_column(out: pd.DataFrame) -> pd.DataFrame:
    """Label the first column after reset_index as Date when it is datetime-like."""
    if out.empty or len(out.columns) == 0:
        return out
    first = out.columns[0]
    if pd.api.types.is_datetime64_any_dtype(out[first]):
        return out.rename(columns={first: "Date"})
    return out.rename(columns={first: "Index"})


def format_calculation_preview(df: pd.DataFrame, cols: list[str], max_rows: int = 8) -> pd.DataFrame:
    """Return the last few rows of selected columns with a readable index column."""
    existing = [c for c in cols if c in df.columns]
    if not existing:
        return pd.DataFrame()
    preview = df[existing].tail(max_rows).copy()
    out = preview.reset_index()
    return rename_first_index_column(out)


def equity_curve_export_df(equity: pd.Series) -> pd.DataFrame:
    """Turn an equity series into a tidy two-column export frame."""
    out = equity.to_frame("Equity").reset_index()
    return rename_first_index_column(out)


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def num_float(x: object) -> float | None:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def num_int(x: object) -> int | None:
    if x is None:
        return None
    try:
        return int(x)
    except (TypeError, ValueError):
        try:
            return int(float(x))
        except (TypeError, ValueError):
            return None
