# FX Strategy Lab: A Transparent Educational Tool for Forex Strategy Backtesting and Visualisation

An educational Streamlit application that translates technical forex indicators and backtesting mechanics into plain-English explanations for non-technical users, while still giving experienced users full analytical depth.

Built end-to-end from requirements gathering through to delivery: user needs were mapped across three distinct personas, prioritised using MoSCoW, and validated through a structured think-aloud usability study whose findings were translated directly into shipped product improvements. Along the way it involved working with real market data, applying core technical analysis concepts (moving averages, RSI, trend and momentum signals), and reasoning about the practical limitations of backtesting — spread, slippage, and overfitting — that separate simulated performance from real trading outcomes.

## Features

- **Data**: Yahoo Finance downloads via `yfinance` (`src/data/loader.py`) and cleaning helpers (`src/data/cleaning.py`).
- **Indicators**: SMA, EMA, and RSI (`src/indicators/`).
- **Strategies**:
  - **SMA overlay (chart only)**: plots price with a configurable SMA; no simulated trades in `app.py`.
  - **MA crossover backtest**: fast/slow MA cross signals (`src/strategies/ma_crossover.py`).
  - **RSI backtest**: discrete buys/sells from RSI thresholds (`src/strategies/rsi_strategy.py`). RSI averages gains and losses with a simple rolling mean (not Wilder smoothing) for educational readability.
  - **SMA price cross backtest**: buy/sell when price crosses its own SMA (`src/strategies/sma_price_cross.py`).
- **Backtesting and metrics**: sequential engine (`src/backtest/engine.py`) and summary metrics (`src/backtest/metrics.py`).
- Charts: candlesticks with overlays (`src/viz/charts.py`).
- **Controller layer**: reusable download → clean → strategy → backtest → metrics pipeline without Streamlit (`src/controller/run_backtest.py`).
- **UI package**: Streamlit layout and tutor/explore rendering under `ui/`.

## Repository layout

```
app.py
main.py
requirements.txt
README.md
.gitlab-ci.yml
docs/
  architecture.md
tests/
  conftest.py
  test_backtest_edge_cases.py
  test_backtest_engine.py
  test_csv_exports.py
  test_ema.py
  test_metrics.py
  test_rsi.py
  test_sma.py
  test_strategies.py
  test_strategy_behaviour.py
src/
  __init__.py
  controller/
    __init__.py
    run_backtest.py
  data/
    __init__.py
    loader.py
    cleaning.py
  indicators/
    __init__.py
    sma.py
    ema.py
    rsi.py
  strategies/
    __init__.py
    ma_crossover.py
    rsi_strategy.py
    sma_price_cross.py
  backtest/
    __init__.py
    engine.py
    metrics.py
  viz/
    __init__.py
    charts.py
ui/
  app_logic/
  components/
  helpers/
```

## Setup

```bash
pip install -r requirements.txt
```

Alternatively, run the one-command setup script which creates a
virtual environment and installs all dependencies automatically:

```bash
./setup.sh
```

Then activate the environment with:

```bash
source venv/bin/activate
```

## Run the app

```bash
streamlit run app.py
```

## Tests

```bash
pytest -q
```

Test modules live under `tests/` and cover indicators, strategies, the backtest engine, metrics, CSV helpers, and edge cases.

## Assumptions and limitations

- **Educational use only** — not a substitute for professional trading or risk controls.
- **Long-only execution model** — one position at a time, entries and exits on bar close; see `src/backtest/engine.py`.
- **No market frictions** — no slippage, spreads, financing, or transaction costs.
- **RSI simplification** — rolling mean of gains/losses instead of Wilder smoothing; chosen for clarity, not as a production default.
- Prices come from Yahoo Finance/yfinance. Availability and quality depend on that service and the chosen symbol or interval.
