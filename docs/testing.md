# Testing Strategy

## Approach

- **Unit tests for indicators**: Check that SMA, EMA, and RSI computations match expected values (e.g. known inputs and outputs, or formulae).
- **Synthetic dataset tests**: Use small DataFrames with known price/signal sequences to test strategies and the backtester; assert expected trade count, entry/exit times, and P/L where possible.
- **Cross-validation**: Compare indicator or strategy outputs against external references (e.g. TradingView, online RSI/SMA calculators) as evaluation evidence.
- Run a manual UI smoke test with `streamlit run app.py`, then load data, run a strategy, and confirm that charts and metrics render without errors.

## How to run tests

```bash
pytest -q
```

## Current coverage

The test suite contains **76 tests across 10 files** covering all `src/` modules including indicators, strategies, backtest engine, metrics, CSV exports, and edge cases.

The controller layer (`src/controller/run_backtest.py`) is covered by import-level verification in the CI pipeline.

All tests use synthetic data only with no live API calls.

GitLab CI runs `pytest -q --tb=short` automatically on every push to `main` and on merge request events.

## Synthetic testing explained

Synthetic tests use a small, fixed DataFrame (e.g. a few rows of OHLC and known indicator values) so that expected outcomes are known in advance.

**Example — crossover scenario:** Build a series where a fast MA crosses above a slow MA on a specific bar. Run the MA crossover strategy and assert that a long signal (e.g. `signal == 1`) appears on the expected bar and that the backtester opens exactly one trade.

**Example — RSI threshold scenario:** Build a series where RSI drops below 30 then rises. Run the RSI strategy with oversold=30 and assert that a long signal appears when RSI crosses below 30 (or as defined by the strategy), and that the backtester produces the expected number of trades.

This supports evaluation and correctness goals by tying tests to well-defined, reproducible scenarios instead of live data.
