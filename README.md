# Forex Trading Strategy Backtesting & Visualisation Tool

An educational tool for backtesting and visualising technical trading strategies on Forex data. It is intended for learning and analysis only—not for live trading.

## Implemented Features

- **Yahoo Finance OHLC retrieval** via yfinance (`src/data/loader.py`)
- **Data cleaning and validation** (`src/data/cleaning.py`)
- **Indicators**: SMA, EMA, RSI (`src/indicators/sma.py`, `ema.py`, `rsi.py`)
- **Strategies**: MA crossover, RSI strategy (`src/strategies/ma_crossover.py`, `rsi_strategy.py`). The UI also offers an SMA overlay (chart only, no trades), implemented in the app.
- **Sequential backtesting engine** (`src/backtest/engine.py`)
- **Performance metrics** (`src/backtest/metrics.py`)
- **Streamlit dashboard** (`app.py`) with **Plotly visualisations** (`src/viz/charts.py`)

Orchestration (data → clean → strategy → backtest → metrics → viz) currently lives in `app.py`; there is no separate controller package.

## Planned / In Progress

- Session-based trade summary (run history in `st.session_state`)
- Expanded test suite (EMA, RSI, strategies, backtest)
- Evaluation evidence pack (cross-checks, runtime benchmarks, usability feedback)

## Architecture

The project uses a **layered (n-tier) architecture**: separation of concerns, testability, and extensibility. See `docs/architecture.md` for details.

## Repository Structure

```
app.py
src/
  data/       loader.py, cleaning.py
  indicators/ sma.py, ema.py, rsi.py
  strategies/ ma_crossover.py, rsi_strategy.py
  backtest/   engine.py, metrics.py
  viz/        charts.py
requirements.txt
```

There is no `src/controller/` or `tests/` folder at present; tests are planned.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Test

```bash
pytest -q
```

(Add tests under `tests/` when the suite is created.)

## Assumptions and Limitations

- **Educational use only**—not suitable for live trading.
- **Simplified execution model**: long-only, one position at a time, execution at close; see `src/backtest/engine.py` for documented assumptions.
- Results are sensitive to parameters and market regime; past performance does not guarantee future results.
