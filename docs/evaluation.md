# Evaluation

This document summarises how the FX Strategy Lab was evaluated for an interim report: **correctness**, **robustness**, **performance**, and **usability**. Claims are kept modest and aligned with what was actually built and tested.

## 1. Evaluation overview

The tool was assessed in four areas:

- **Correctness** — Do indicators, signals, backtesting, and metrics behave as intended on controlled inputs?
- **Robustness** — Does the app handle normal use (data load, strategy run, empty edge cases in tests) without breaking core assumptions?
- **Performance** — Is the project responsive enough for interactive, educational exploration (not a formal production benchmark)?
- **Usability** — Does the Streamlit interface support learning: controls, charts, metrics, session comparison, and explainability?

Formal **user studies or moderated usability tests have not been completed**; usability is described from design intent and informal use, not from survey or lab results.

## 2. Correctness validation

### Automated tests

The repository includes a **pytest** suite under `tests/`:

- `tests/test_ema.py` — EMA shape, edge cases, and agreement with `pandas` `ewm(span=..., adjust=False)` (same approach as `src/indicators/ema.py`).
- `tests/test_rsi.py` — RSI range, trend behaviour, flat series, and alignment with `src/indicators/rsi.py` (rolling averages of gains/losses).
- `tests/test_strategies.py` — `ma_crossover_signals` and `rsi_signals`: known synthetic paths for buy/sell timing and parameter validation errors.
- `tests/test_backtest_engine.py` — `run_backtest` (no trades, profitable exit, losing exit, open position closed at last bar) and `compute_metrics` (trade counts, win rate, returns, drawdown helpers, empty equity edge).

These tests use **synthetic** pandas `Series` / `DataFrame` data only (no live Yahoo Finance calls in tests). Synthetic data makes **expected outcomes** knowable in advance, which supports clear pass/fail assertions and documentation of behaviour.

### Consistency with implementation

Test expectations are written against the **actual** code paths in `src/indicators/`, `src/strategies/`, `src/backtest/engine.py`, and `src/backtest/metrics.py`, not against textbook-only definitions. For example, RSI tests reflect **rolling mean** gains/losses as implemented, not Wilder-style smoothing.

Run the suite with:

```bash
pytest -q
```

## 3. Backtesting validation

The backtest engine is checked (in tests) for representative situations:

- **No actionable signals** — equity stays flat; no trades.
- **One complete round-trip** — single buy then sell; P/L and `return_pct` match price direction.
- **Losing trade** — negative P/L when exit is below entry.
- **Open position at end of series** — engine closes at the last bar; one trade recorded with expected return.
- **Metrics** — `compute_metrics` respects trade list length, win rate, and basic drawdown-related outputs on simple equity paths.

These scenarios support claims that **sequential long-only backtesting** and **metric aggregation** were validated under known conditions, not only via the GUI.

## 4. Performance

- **Tests** complete in under a few seconds on a typical developer machine (suitable for CI and frequent runs).
- **Interactive app** performance depends on date range, interval (e.g. `1d` vs `1h`), and network latency for **yfinance** downloads; no formal latency or throughput benchmarks have been published for this project.

For an **educational** tool, the emphasis is on acceptable responsiveness during exploration rather than on trading-system benchmarks.

## 5. Usability

The Streamlit app is designed to support **educational exploration**:

- **Sidebar** — data range, pair, interval, strategy, and parameters.
- **Charts** — candlesticks with optional MA overlays and trade markers for backtests.
- **Metrics** — return, trade count, win rate, drawdown (with an in-app explanation expander).
- **Session run summary** — compares multiple backtest runs within one session.
- **How This Strategy Is Calculated** — `app.py` includes this block: formulas, step-by-step logic, why signals occur, and a short preview table driven only by **last-run** session state (`last_strategy`, `last_chart_df`, `last_params`, `last_overlay_cols`), so the text always matches the chart you are viewing.

**Formal usability evaluation** (e.g. structured tasks, timing, error rates, questionnaires) is **out of scope for the current submission** and is listed as a possible **next step** rather than a completed study.

## 6. Limitations

- **Educational tool only** — not financial advice and not a live trading system.
- **Simplified execution** — see `src/backtest/engine.py` (e.g. long-only, one position, fills at bar **Close**).
- **Market and parameter sensitivity** — results depend on symbol, horizon, strategy settings, and regime; strong claims about profitability are inappropriate.
- **Data dependency** — historical data comes from **Yahoo Finance** via **yfinance**; gaps or vendor quirks can affect any visual or metric output.
