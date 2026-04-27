# Architecture Overview

The application uses a **Layered Architecture (n-tier)** with a dedicated controller layer and Streamlit UI composition in `app.py`.

## High-level flow

```
UI (Streamlit app.py) → Controller (in app.py) → Strategies → Indicators → Data → Backtest → Metrics / Viz
```

## Layer responsibilities

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **UI** | `app.py` | User inputs (symbol, dates, strategy, parameters) and display of results, charts, and metrics. |
| **Controller** | `src/controller/run_backtest.py`, `app.py` | `src/controller/run_backtest.py` orchestrates the full pipeline (download → clean → strategy signals → backtest → metrics) without any Streamlit dependency, making the pipeline independently testable; `app.py` orchestrates UI/session flow. |
| **Data** | `src/data/loader.py`, `src/data/cleaning.py` | Download OHLC via yfinance; clean and validate the DataFrame. |
| **Indicators** | `src/indicators/sma.py`, `ema.py`, `rsi.py` | Pure computations (SMA, EMA, RSI) on price series. |
| **Strategies** | `src/strategies/ma_crossover.py`, `rsi_strategy.py`, `sma_price_cross.py` | Signal generation: add `signal` (and optionally indicator) columns to the DataFrame. |
| **Backtest** | `src/backtest/engine.py`, `src/backtest/metrics.py` | Sequential simulation (long-only, one position, at close); then compute P/L, win rate, drawdown, etc. |
| **Visualisation** | `src/viz/charts.py` | Plotly candlestick chart and overlays (e.g. MAs). |

## Execution flow (run path)

When the user clicks **Run Simulation**:

1. **Inputs** are read from the sidebar (symbol, start/end, interval, strategy, parameters).
2. A **DataRequest** is built and passed to **download_ohlc** (yfinance).
3. The raw DataFrame is passed to **clean_ohlc** for validation and cleaning.
4. **Strategy branch**:
   - **SMA overlay**: `sma()` is applied, overlay columns are set; no backtest.
   - **MA crossover backtest**: `ma_crossover_signals()` produces a DataFrame with `signal` (and `fast_ma`, `slow_ma`).
   - **RSI backtest**: `rsi_signals()` produces a DataFrame with `signal`.
   - **SMA price cross backtest**: `sma_price_cross_signals()` produces a DataFrame with `signal` and `sma`.
5. For backtest strategies, **run_backtest** is called on the signal DataFrame; it returns trades and an equity curve.
6. **compute_metrics** is called on trades and equity curve.
7. **Session state** is updated (last run, chart DataFrame, trades, metrics, overlay columns, title).
8. Results are rendered: **candlestick_with_overlay** (from `src/viz/charts.py`), trade markers, and metrics.

## Design rationale

Modular layering keeps data, indicators, strategies, and backtest logic separate from the UI. That improves maintainability and testability (each layer can be unit-tested) and makes it easier to add new indicators, strategies, or visualisations without changing the rest of the pipeline.
