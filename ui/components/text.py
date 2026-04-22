"""Text-heavy sections: explainability, reflection, onboarding, tutor welcome."""
from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from ui.app_logic.flow import set_step
from ui.helpers.formatting import format_calculation_preview
from ui.helpers.layout import render_section_heading


def render_onboarding(strategy: str) -> None:
    """Legacy onboarding (Explore); prefer tutor welcome in Tutor mode."""
    st.markdown("**How it works**")
    st.markdown(
        "- Pick a currency pair, date range, and interval in the sidebar.\n"
        "- Choose a strategy and click **Run Simulation** to load data and run it.\n"
        "- Read the five sections below to see price, trades, account value, performance, and reflection prompts."
    )
    st.divider()

    st.subheader("What this strategy is doing")
    if strategy == "SMA overlay (no trades)":
        st.markdown(
            "Plots **price with a simple moving average (SMA)**. No trades are simulated—visualisation only. "
            "Parameters: **SMA window** (number of bars). Works best when you want to see price relative to an average."
        )
    elif strategy == "MA crossover backtest":
        st.markdown(
            "**Buys** when the fast MA crosses above the slow; **sells** when it crosses below. "
            "Parameters: **fast window**, **slow window**, **MA type** (SMA or EMA). "
            "Tends to work in trending markets; can give false signals in choppy or sideways markets."
        )
    elif strategy == "SMA price cross backtest":
        st.markdown(
            "**Buys** when price crosses above one SMA line; **sells** when price crosses below it. "
            "Parameter: **SMA window**. "
            "It is simpler than MA crossover because it uses one moving-average line tied directly to price."
        )
    else:
        st.markdown(
            "**Buys** when RSI is below oversold; **sells** when RSI is above overbought. "
            "Parameters: **period**, **oversold**, **overbought**. "
            "Works when price reverses from extremes; can struggle in strong trends where RSI stays extreme."
        )
    st.divider()


def render_empty_state() -> None:
    st.info("Choose settings in the sidebar and click Run.")
    st.markdown(
        """
        **Example settings:**
        - Interval: `1d`
        - Pair: `EURUSD=X`
        - Range: `2024-01-01` to `2024-03-01`
        - SMA: `20`
        """
    )


def render_tutor_welcome(strategy_run: str) -> None:
    """Tutor step 0: intro moved from sidebar onboarding + strategy blurb."""
    st.header("FX Strategy Lab")
    st.markdown(f"#### **{strategy_run}**")
    st.markdown(
        "This tutorial walks you through one idea at a time using your latest run. "
        "You can see what the strategy did, why it did it, and what the results mean. "
        "Look at how each section builds from market movement to performance insight."
    )
    st.markdown(
        "**How it works**\n"
        "- Pick a currency pair, dates, and interval in the sidebar.\n"
        "- Choose a strategy and click **Run Simulation**.\n"
        "- This walkthrough highlights price, trades, equity, performance, and reflection."
    )
    st.markdown("**You will explore**")
    st.markdown(
        "- **Price movement** on the candlestick chart.\n"
        "- **Strategy decisions** as a table of trades.\n"
        "- **Performance** with return and drawdown."
    )
    st.subheader("What this strategy is doing")
    if strategy_run == "SMA overlay (no trades)":
        st.markdown(
            "This shows **price with a simple moving average (SMA)**. You can see when price is generally above or below its recent average."
        )
    elif strategy_run == "MA crossover backtest":
        st.markdown(
            "This strategy compares a fast and slow moving average. "
            "You can see trades when the fast average crosses above (buy) or below (sell) the slow average."
        )
    elif strategy_run == "SMA price cross backtest":
        st.markdown(
            "This strategy compares price to one simple moving average line. "
            "You can see trades when price crosses above that line (buy) or below it (sell)."
        )
    else:
        st.markdown(
            "This strategy uses RSI momentum values. It buys near oversold levels and sells near overbought levels."
        )
    if st.button("Start Tutorial →", type="primary", key="tutor_start_tutorial", use_container_width=True):
        set_step(1)
        st.rerun()


def render_tutor_step_header(title: str, lead: str) -> None:
    st.subheader(title)
    st.markdown(lead)


def render_explainability(
    last_strategy: str | None,
    last_chart_df: pd.DataFrame | None,
    last_overlay_cols: list[str],
    last_params: dict[str, Any],
) -> None:
    if last_strategy is None or last_chart_df is None:
        return

    render_section_heading("How This Strategy Is Calculated", "edu")
    st.caption("Formulas and preview match your last successful run, not the current sidebar until you run again.")

    if last_strategy == "SMA overlay (no trades)":
        n = last_params.get("sma_window", "?")
        overlay = last_overlay_cols[0] if last_overlay_cols else None
        with st.expander("Formula", expanded=False):
            st.markdown(
                f"- **Simple Moving Average (SMA)** smooths price by averaging the last **{n}** closing prices.\n"
                "- **SMA** = average of closing prices over the selected window."
            )
        with st.expander("Step-by-step logic", expanded=False):
            st.markdown(
                "1. Take **Close** for each bar.\n"
                f"2. Compute a **rolling average** over the last **{n}** closes.\n"
                "3. Plot the SMA on the same chart as price (no trades)."
            )
        with st.expander("Why signals happen", expanded=False):
            st.markdown(
                "This mode **does not generate buy or sell signals**—it is for **visual learning** only. "
                "You compare price to the SMA to see whether price is generally above or below its recent average."
            )
        with st.expander("Calculation preview", expanded=False):
            cols = ["Close"]
            if overlay and overlay in last_chart_df.columns:
                cols.append(overlay)
            prev = format_calculation_preview(last_chart_df, cols)
            if prev.empty:
                st.caption("No preview columns available for this run.")
            else:
                st.dataframe(prev, use_container_width=True)

    elif last_strategy == "MA crossover backtest":
        fw = last_params.get("fast_window", "?")
        sw = last_params.get("slow_window", "?")
        mt = last_params.get("ma_type", "?")
        with st.expander("Formula", expanded=False):
            st.markdown(
                "- **Fast MA** and **slow MA** use the window lengths from your last run (**fast** < **slow**).\n"
            )
            if mt == "SMA":
                st.markdown(
                    "- **SMA** = average of closing prices over the window.\n"
                    f"- Fast SMA uses **{fw}** bars; slow SMA uses **{sw}** bars."
                )
            elif mt == "EMA":
                st.markdown(
                    "- **EMA** gives more weight to recent prices. One common recursive form:\n"
                    "  - **EMA_t** = alpha × **Close_t** + (1 − alpha) × **EMA_(t−1)**\n"
                    "  - **alpha** = 2 / (**n** + 1), where **n** is the window length.\n"
                    f"- This app uses **pandas** `ewm(span=n, adjust=False)` for EMA (fast **n**={fw}, slow **n**={sw})."
                )
            else:
                st.markdown("- MA type comes from your last run parameters.")
            st.markdown(
                "- The strategy **compares** fast vs slow MAs and looks for a **cross** from one side to the other."
            )
        with st.expander("Step-by-step logic", expanded=False):
            st.markdown(
                "1. Calculate the **fast MA** on **Close**.\n"
                "2. Calculate the **slow MA** on **Close**.\n"
                "3. Compare **current** and **previous** bars for both MAs.\n"
                "4. **Buy** when the fast MA **crosses above** the slow MA.\n"
                "5. **Sell** when the fast MA **crosses below** the slow MA."
            )
        with st.expander("Why signals happen", expanded=False):
            st.markdown(
                "- A **buy** tries to catch **upward momentum** when the faster average moves above the slower one.\n"
                "- A **sell** tries to exit when **momentum weakens** and the fast average drops back below the slow one.\n"
                "- Crossovers often appear when a **trend** may be starting or ending; they can **whipsaw** in sideways markets."
            )
        with st.expander("Calculation preview", expanded=False):
            prev = format_calculation_preview(last_chart_df, ["Close", "fast_ma", "slow_ma", "signal"])
            if prev.empty:
                st.caption("No preview columns available for this run.")
            else:
                st.dataframe(prev, use_container_width=True)

    elif last_strategy == "RSI backtest":
        p = last_params.get("period", "?")
        ob = last_params.get("oversold", "?")
        oa = last_params.get("overbought", "?")
        with st.expander("Formula", expanded=False):
            st.markdown(
                "- Price **change** each bar: previous close to current close.\n"
                "- **Gains** and **losses** are separated from those changes.\n"
                "- **RS** = (average gain) / (average loss) over the lookback.\n"
                "- **RSI** = 100 − (100 / (1 + **RS**)).\n"
                f"- This implementation uses **rolling averages** of gains and losses over **{p}** bars "
                "(not Wilder smoothing). When both averages are zero, RSI is set to **50**."
            )
        with st.expander("Step-by-step logic", expanded=False):
            st.markdown(
                "1. Calculate **price changes** from **Close**.\n"
                "2. Split changes into **gains** (up moves) and **losses** (down moves).\n"
                "3. Compute **rolling average** gains and **rolling average** losses over the RSI period.\n"
                "4. Compute **RS** = average gain / average loss.\n"
                "5. Compute **RSI** from **RS**.\n"
                f"6. **Buy** when RSI is **below** the oversold level (**{ob}**).\n"
                f"7. **Sell** when RSI is **above** the overbought level (**{oa}**)."
            )
        with st.expander("Why signals happen", expanded=False):
            st.markdown(
                f"- A **buy** when RSI is **below {ob}** assumes the market may have **sold off** and could bounce (mean-reversion idea).\n"
                f"- A **sell** when RSI is **above {oa}** assumes the rally may be **stretched**.\n"
                "- RSI is a **momentum oscillator**: in a **strong trend**, RSI can **stay extreme** for a long time, so signals are not guaranteed wins or losses."
            )
        with st.expander("Calculation preview", expanded=False):
            prev = format_calculation_preview(last_chart_df, ["Close", "rsi", "signal"])
            if prev.empty:
                st.caption("No preview columns available for this run.")
            else:
                st.dataframe(prev, use_container_width=True)

    elif last_strategy == "SMA price cross backtest":
        w = last_params.get("window", "?")
        overlay = "sma" if "sma" in last_overlay_cols else None
        with st.expander("Formula", expanded=False):
            st.markdown(
                f"The strategy builds a **simple moving average (SMA)** from the rolling mean of the last **{w}** closing prices, "
                "so each new bar updates the average by dropping the oldest close and adding the newest one."
            )
        with st.expander("Step-by-step logic", expanded=False):
            st.markdown(
                "The app compares price and SMA on the current bar and the previous bar to catch the exact crossing moment: a **buy** "
                "signal is created when **Close** > **SMA** and previous **Close** ≤ previous **SMA**, while a **sell** signal is "
                "created when **Close** < **SMA** and previous **Close** ≥ previous **SMA**. Using the previous bar avoids flagging "
                "every bar that stays above or below the SMA after the cross has already happened."
            )
        with st.expander("Why signals happen", expanded=False):
            st.markdown(
                "With one window setting, this is easy to experiment with and easy to interpret because each signal comes directly from "
                "price moving through its own recent average. It is a useful stepping stone before MA crossover, which needs two moving "
                "average lines and an extra parameter choice."
            )
        with st.expander("Calculation preview", expanded=False):
            cols = ["Close", "signal"]
            if overlay and overlay in last_chart_df.columns:
                cols.insert(1, overlay)
            prev = format_calculation_preview(last_chart_df, cols)
            if prev.empty:
                st.caption("No preview columns available for this run.")
            else:
                st.dataframe(prev, use_container_width=True)



def render_reflection_and_advanced(
    last_chart_df: pd.DataFrame, *, show_heading: bool = True, show_advanced: bool = True
) -> None:
    if show_heading:
        render_section_heading("5) What This Means", "reflect")
    st.markdown(
        "- **Win rate vs return**: Can you have a high win rate but still lose money? (Think about size of wins vs losses.)\n"
        "- **Drawdown**: How would a large drawdown feel in real trading? Could you hold through it?\n"
        "- **Trends vs sideways**: Do you think this strategy would do better in trending or sideways markets?\n"
        "- **Parameters**: What happens if you change fast/slow windows or RSI levels? Try different settings and compare."
    )

    if show_advanced:
        with st.expander("Show latest data table (advanced)"):
            st.dataframe(last_chart_df.tail(25))
