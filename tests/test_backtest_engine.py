    """Tests for backtest engine and metrics. Synthetic DataFrames only; no live API."""
    from __future__ import annotations

    import pandas as pd
    import pytest

    from src.backtest.engine import run_backtest
    from src.backtest.metrics import compute_metrics


    def _make_df(close_list, signal_list, index=None):
        """Minimal OHLC + signal DataFrame for engine. Index can be range or datetime-like."""
        if index is None:
            index = range(len(close_list))
        return pd.DataFrame(
            {"Close": close_list, "signal": signal_list},
            index=index,
        )


    def test_no_signals_no_trades():
        """When signal is all 0, backtest returns 0 trades and constant equity."""
        df = _make_df([100.0, 101.0, 102.0, 103.0], [0, 0, 0, 0])
        trades, equity_curve = run_backtest(df, initial_capital=10_000.0)
        assert len(trades) == 0
        assert equity_curve.index.equals(df.index)
        assert len(equity_curve) == len(df)
        assert (equity_curve == 10_000.0).all()


    def test_one_entry_one_exit_one_trade():
        """One signal 1 then one signal -1 produces exactly one completed trade with correct keys and P/L sign."""
        # Enter at bar 1 (Close 100), exit at bar 3 (Close 110) -> profit
        df = _make_df([99.0, 100.0, 105.0, 110.0], [0, 1, 0, -1])
        trades, equity_curve = run_backtest(df, initial_capital=10_000.0)
        assert len(trades) == 1
        t = trades[0]
        assert "entry_time" in t and "entry_price" in t and "exit_time" in t
        assert "exit_price" in t and "pnl" in t and "return_pct" in t
        assert t["entry_price"] == 100.0 and t["exit_price"] == 110.0
        assert t["pnl"] > 0
        assert t["return_pct"] == pytest.approx(10.0)  # (110-100)/100 * 100
        assert equity_curve.index.equals(df.index)
        assert len(equity_curve) == len(df)


    def test_one_entry_one_exit_loss():
        """Exit below entry -> negative P/L and return_pct."""
        df = _make_df([99.0, 100.0, 98.0, 90.0], [0, 1, 0, -1])
        trades, equity_curve = run_backtest(df, initial_capital=10_000.0)
        assert len(trades) == 1
        assert trades[0]["pnl"] < 0
        assert trades[0]["return_pct"] == pytest.approx(-10.0)


    def test_open_position_at_end_closed():
        """Open position at end of data is closed on last bar; one trade recorded."""
        df = _make_df([100.0, 102.0, 104.0], [0, 1, 0])  # enter at 1, no exit signal
        trades, equity_curve = run_backtest(df, initial_capital=10_000.0)
        assert len(trades) == 1
        t = trades[0]
        assert t["entry_time"] == df.index[1]
        assert t["exit_time"] == df.index[-1]
        assert t["exit_price"] == 104.0
        assert t["return_pct"] == pytest.approx((104.0 - 102.0) / 102.0 * 100)
        assert equity_curve.iloc[-1] == pytest.approx(10_000.0 * (104.0 / 102.0))


    def test_engine_equity_curve_length():
        """Equity curve has same length and index as input DataFrame."""
        df = _make_df([1.0, 2.0, 3.0, 4.0, 5.0], [0, 1, 0, -1, 0])
        _, equity_curve = run_backtest(df)
        assert len(equity_curve) == len(df)
        assert equity_curve.index.equals(df.index)


    def test_engine_missing_close_raises():
        """DataFrame without Close or signal raises ValueError."""
        with pytest.raises(ValueError, match="Close and signal"):
            run_backtest(pd.DataFrame({"signal": [0, 0]}))
        with pytest.raises(ValueError, match="Close and signal"):
            run_backtest(pd.DataFrame({"Close": [1.0, 2.0]}))


    def test_engine_empty_df_raises():
        """Empty DataFrame raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            run_backtest(pd.DataFrame({"Close": [], "signal": []}))


    def test_initial_capital_affects_equity_scale():
        """Different initial_capital changes equity scale but trade count and return_pct unchanged."""
        df = _make_df([100.0, 102.0], [1, -1])
        trades1, eq1 = run_backtest(df, initial_capital=1000.0)
        trades2, eq2 = run_backtest(df, initial_capital=20_000.0)
        assert len(trades1) == len(trades2) == 1
        assert trades1[0]["return_pct"] == pytest.approx(trades2[0]["return_pct"])
        assert eq1.iloc[-1] == pytest.approx(1000.0 * (102.0 / 100.0))
        assert eq2.iloc[-1] == pytest.approx(20_000.0 * (102.0 / 100.0))


    # ---- Metrics ----


    def test_compute_metrics_num_trades():
        """compute_metrics returns num_trades equal to len(trades)."""
        equity = pd.Series([10_000.0, 10_100.0, 10_050.0], index=range(3))
        trades = [
            {"entry_time": 0, "entry_price": 100.0, "exit_time": 1, "exit_price": 101.0, "pnl": 100.0, "return_pct": 1.0},
            {"entry_time": 1, "entry_price": 101.0, "exit_time": 2, "exit_price": 100.5, "pnl": -50.0, "return_pct": -0.5},
        ]
        m = compute_metrics(trades, equity)
        assert m["num_trades"] == 2


    def test_compute_metrics_win_rate_and_avg_return():
        """With one winning trade, win_rate_pct 100 and avg_trade_return_pct matches."""
        equity = pd.Series([10_000.0, 10_100.0], index=[0, 1])
        trades = [
            {"entry_time": 0, "entry_price": 100.0, "exit_time": 1, "exit_price": 110.0, "pnl": 1000.0, "return_pct": 10.0},
        ]
        m = compute_metrics(trades, equity)
        assert m["win_rate_pct"] == pytest.approx(100.0)
        assert m["avg_trade_return_pct"] == pytest.approx(10.0)


    def test_compute_metrics_empty_trades():
        """With no trades, win_rate_pct and avg_trade_return_pct are 0."""
        equity = pd.Series([10_000.0, 10_000.0], index=[0, 1])
        m = compute_metrics([], equity)
        assert m["num_trades"] == 0
        assert m["win_rate_pct"] == 0.0
        assert m["avg_trade_return_pct"] == 0.0


    def test_compute_metrics_total_return_pct():
        """total_return_pct reflects (last/first - 1) * 100."""
        equity = pd.Series([10_000.0, 11_000.0], index=[0, 1])
        m = compute_metrics([], equity)
        assert m["total_return_pct"] == pytest.approx(10.0)


    def test_compute_metrics_max_drawdown():
        """max_drawdown_value and max_drawdown_pct are consistent with a dip in equity."""
        # Peak 100, then 90, then 95 -> drawdown 10 then 5; max drawdown 10
        equity = pd.Series([100.0, 110.0, 99.0, 104.0], index=range(4))
        m = compute_metrics([], equity)
        assert m["max_drawdown_value"] <= 0
        assert m["max_drawdown_pct"] >= 0


    def test_compute_metrics_empty_equity_raises():
        """Empty equity_curve raises ValueError."""
        with pytest.raises(ValueError, match="equity_curve must be non-empty"):
            compute_metrics([], pd.Series(dtype=float))
