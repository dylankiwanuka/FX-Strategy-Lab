# Testing Strategy

## Approach

- **Unit tests for indicators**: Check that SMA, EMA, and RSI computations match expected values (e.g. known inputs and outputs, or formulae).
- **Synthetic dataset tests**: Use small DataFrames with known price/signal sequences to test strategies and the backtester; assert expected trade count, entry/exit times, and P/L where possible.
- **Cross-validation**: Compare indicator or strategy outputs against external references (e.g. TradingView, online RSI/SMA calculators) as evaluation evidence.
- **Manual UI smoke test**: Run `streamlit run app.py`, load data, run a strategy, and confirm that charts and metrics render without errors.

## How to run tests

```bash
pytest -q
```

## Current coverage

At present there is no `tests/` folder in the repository, so there are no automated tests. Once tests are added, this section should list the actual test files (e.g. `tests/test_sma.py` only if that file exists).

## Planned coverage

The following are **planned** (not yet implemented):

- [ ] `tests/test_ema.py` — EMA indicator correctness
- [ ] `tests/test_rsi.py` — RSI indicator correctness
- [ ] `tests/test_strategies.py` — MA crossover and RSI strategy signal logic
- [ ] `tests/test_backtest_engine.py` — backtest engine (trades, equity curve) on synthetic data

## Synthetic testing explained

Synthetic tests use a small, fixed DataFrame (e.g. a few rows of OHLC and known indicator values) so that expected outcomes are known in advance.

**Example — crossover scenario:** Build a series where a fast MA crosses above a slow MA on a specific bar. Run the MA crossover strategy and assert that a long signal (e.g. `signal == 1`) appears on the expected bar and that the backtester opens exactly one trade.

**Example — RSI threshold scenario:** Build a series where RSI drops below 30 then rises. Run the RSI strategy with oversold=30 and assert that a long signal appears when RSI crosses below 30 (or as defined by the strategy), and that the backtester produces the expected number of trades.

This supports evaluation and correctness goals by tying tests to well-defined, reproducible scenarios instead of live data.
