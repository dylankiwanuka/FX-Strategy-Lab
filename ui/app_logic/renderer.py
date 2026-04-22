from __future__ import annotations

import streamlit as st

from ui.components import charts, metrics, tables, text
from ui.helpers.bundle import ResultsBundle
from ui.helpers.layout import narrow_container, tutor_lesson_card
from ui.app_logic import flow as tutor_flow

_TUTOR_STRATEGY_TRACK_KEY = "_tutor_tracked_sidebar_strategy"


def _maybe_reset_tutor_on_strategy_change(strategy_sidebar: str) -> None:
    prev = st.session_state.get(_TUTOR_STRATEGY_TRACK_KEY)
    if prev is not None and prev != strategy_sidebar:
        tutor_flow.reset_steps()
        st.session_state[_TUTOR_STRATEGY_TRACK_KEY] = strategy_sidebar
        st.rerun()
    st.session_state[_TUTOR_STRATEGY_TRACK_KEY] = strategy_sidebar


def _render_data_quality_metrics(last_df) -> None:
    if last_df is not None and len(last_df) > 0:
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", f"{len(last_df):,}")
        c2.metric("From", str(last_df.index.min())[:10])
        c3.metric("To", str(last_df.index.max())[:10])
    st.write("")


def _render_tutor_navigation() -> None:
    step = tutor_flow.get_current_step()
    st.divider()
    b1, b2, b3 = st.columns([1, 1, 1])
    with b1:
        if st.button("← Back", disabled=step <= 0, key="tutor_back", use_container_width=True):
            tutor_flow.prev_step()
            st.rerun()
    with b2:
        if st.button(
            "Restart Tutorial",
            disabled=step == 0,
            key="tutor_restart",
            use_container_width=True,
        ):
            tutor_flow.reset_steps()
            st.rerun()
    with b3:
        if st.button("Next →", disabled=step >= 5, key="tutor_next", use_container_width=True):
            tutor_flow.next_step()
            st.rerun()


_TUTOR_STEPS: dict[int, dict[str, str]] = {
    1: {
        "title": "1) Market Movement",
        "lead": "A quick visual lesson on how price behaved in this run.",
        "what": "This chart shows candlesticks over your selected time range. You can see where momentum sped up or slowed down.",
        "how": "Each candle summarises open, high, low, and close. If markers are visible, they show where the strategy entered and exited.",
        "why": "Traders use this to judge whether signals happened in stable trends or noisy sideways periods.",
    },
    2: {
        "title": "2) Strategy Decisions",
        "lead": "This step explains exactly how your selected strategy creates signals.",
        "what": "You are looking at completed trades (entry and exit) from the latest run.",
        "how": "Signals are created from indicator calculations, then the backtest opens/closes positions from those signals.",
        "why": "Traders use rule-based signals to remove guesswork and stay consistent across market conditions.",
    },
    3: {
        "title": "3) Account Value Over Time",
        "lead": "How the account evolves matters as much as where it finishes.",
        "what": "This line shows your simulated account value over time.",
        "how": "Equity updates bar-by-bar from open position value and cash balance.",
        "why": "Traders watch drawdowns to avoid strategies that are too painful to hold in practice.",
    },
    4: {
        "title": "4) Performance Summary",
        "lead": "These metrics summarise quality, risk, and consistency.",
        "what": "You can see return, number of trades, win rate, average trade return, and drawdown.",
        "how": "They are computed from all trades and the account-value curve.",
        "why": "Traders compare return and risk together to decide if a strategy is usable.",
    },
    5: {
        "title": "5) What This Means",
        "lead": "Turn results into practical decisions for your next run.",
        "what": "Use prompts to reflect on win/loss patterns, drawdowns, and parameter choices.",
        "how": "Compare what improved and what worsened before changing settings.",
        "why": "Traders improve by reviewing evidence, not just chasing a higher single-run return.",
    },
}


def _render_tutor_sections(lesson: dict[str, str]) -> None:
    st.markdown("#### What you are looking at")
    st.markdown(lesson.get("what", ""))
    st.markdown("#### How it works")
    st.markdown(lesson.get("how", ""))
    st.markdown("#### Why traders use this")
    st.markdown(lesson.get("why", ""))


def _render_deeper_step1(lesson: dict[str, str]) -> None:
    st.markdown(
        "If you are new to charts, think of each candle as a short story for one period of time. "
        "The thick part of the candle is the **range between open and close**, and the thin lines (wicks) show how far price "
        "wandered above and below that range. Green (or up) candles mean the period ended higher than it started; red (or down) "
        "means it ended lower."
    )
    st.markdown(
        "When you see long candles in a row, the market is moving with conviction. When candles are small and overlap, the market "
        "is often undecided. Markers on the chart show where this app **opened and closed** a simulated position so you can connect "
        "those moments to what price was doing."
    )
    st.markdown(lesson.get("how", ""))


def _render_deeper_step2_beginner(bundle: ResultsBundle) -> None:
    strategy = bundle.last_strategy
    if strategy == "SMA overlay (no trades)":
        n = bundle.last_params.get("sma_window", "?")
        st.markdown(
            f"In this mode the app draws a **simple moving average** using the last **{n}** closing prices. "
            "Imagine you add up the last few daily closing prices and divide by how many days you used—that is the average for today. "
            "Tomorrow you drop the oldest day and add the newest day, so the line slowly follows price."
        )
        st.markdown(
            "This view **does not place trades**. It is like turning on a ruler on top of the chart so you can see whether price is "
            "mostly above or below its recent middle ground. That helps beginners build intuition before adding buy and sell rules."
        )
    elif strategy == "MA crossover backtest":
        fw = bundle.last_params.get("fast_window", "?")
        sw = bundle.last_params.get("slow_window", "?")
        mt = bundle.last_params.get("ma_type", "?")
        st.markdown(
            f"Here the app calculates two lines from the same closing prices: a **faster** {mt} that reacts quickly (window **{fw}**) "
            f"and a **slower** {mt} that smooths noise more (window **{sw}**). When the fast line crosses **above** the slow line, "
            "the app treats that as a possible start of upward movement and **buys**. When the fast line crosses **below**, it **sells**."
        )
        st.markdown(
            "You do not need to know the exact maths yet—just that the strategy is trying to **ride trends** and step aside when momentum "
            "weakens. In choppy sideways markets those lines can cross often, which is why results can look noisy in some periods."
        )
    elif strategy == "RSI backtest":
        p = bundle.last_params.get("period", "?")
        ob = bundle.last_params.get("oversold", "?")
        oa = bundle.last_params.get("overbought", "?")
        st.markdown(
            f"The app measures how strongly price has moved up versus down over the last **{p}** bars and turns that into a score from "
            "0 to 100 called **RSI**. When the score is very low, the market has sold off quickly; when it is very high, the market has "
            "rallied quickly. This strategy **buys** when RSI falls below the oversold line and **sells** when RSI rises above the overbought line."
        )
        st.markdown(
            f"For your run the oversold level is **{ob}** and the overbought level is **{oa}**. Think of it as a simple rule: try to buy "
            "after a stretch of weakness and exit after a stretch of strength. Strong trends can keep RSI extreme for a long time, so "
            "this style is not a guarantee—it is a structured way to practice reading momentum."
        )
    elif strategy == "SMA price cross backtest":
        w = bundle.last_params.get("window", "?")
        st.markdown(
            f"Here the app draws one **simple moving average** using the last **{w}** closing prices, so you can compare the current close "
            "to its recent average with a single line. A **buy** is triggered when price crosses up through that SMA, and a **sell** is "
            "triggered when price crosses down through it, which keeps the rule easy to read while still showing clear shifts in momentum."
        )
    else:
        st.markdown(
            "Pick a strategy in the sidebar and run again to see a beginner-friendly explanation matched to your last successful run."
        )


def _render_deeper_step3(bundle: ResultsBundle, lesson: dict[str, str]) -> None:
    if bundle.last_strategy == "RSI backtest":
        ob = bundle.last_params.get("oversold", "?")
        oa = bundle.last_params.get("overbought", "?")
        st.markdown(
            f"The equity line is your **pretend account balance** after each simulated trade. In this RSI run, thresholds are "
            f"**oversold {ob}** and **overbought {oa}**. When RSI spends a long time near the bottom, you may see the account bounce if "
            "buy rules triggered; when RSI stays high, sells may appear more often."
        )
    st.markdown(
        "Drawdown means the largest drop from a peak to a trough along the way—not just the final result. A strategy can end positive "
        "but still have a scary dip in the middle. Watching the curve helps you decide whether you could have stayed calm in real life."
    )
    st.markdown(lesson.get("why", ""))


def _render_deeper_step4(lesson: dict[str, str]) -> None:
    st.markdown(
        "**Total return** answers whether the whole journey was profitable in percentage terms. **Win rate** tells you what share of "
        "individual trades finished green, but it does not tell you how large wins were compared to losses—two strategies can share "
        "a win rate yet feel very different to trade."
    )
    st.markdown(
        "**Average trade return** averages each round-trip trade as a percentage, which helps you see whether typical wins outweigh "
        "typical losses. **Max drawdown** is the worst peak-to-trough loss along the path; it is often the number people care about most "
        "for sleep-at-night risk."
    )
    st.markdown(lesson.get("how", ""))


def _render_deeper_step5(lesson: dict[str, str]) -> None:
    st.markdown(
        "A single backtest is a story about one set of dates and parameters. The useful question is not only “did it make money?” but "
        "**what kind of market** produced those trades and whether the drawdowns felt acceptable for your goals."
    )
    st.markdown(
        "Use the prompts below as a checklist: compare runs after small parameter changes, notice whether trades cluster in trends or "
        "chop, and decide what you would want to see repeated before trusting a rule in real markets."
    )
    st.markdown(lesson.get("what", ""))


def _render_tutor_shell(bundle: ResultsBundle, strategy_sidebar: str) -> None:
    step = tutor_flow.get_current_step()
    strategy_run = bundle.last_strategy or strategy_sidebar

    with narrow_container():
        with tutor_lesson_card():
            st.progress(step / 5.0)

            if step == 0:
                text.render_tutor_welcome(strategy_run)
            else:
                lesson = _TUTOR_STEPS.get(step, {})
                title = lesson.get("title", "")
                lead = lesson.get("lead", "")
                text.render_tutor_step_header(title, lead)
                _render_tutor_sections(lesson)
                with st.expander("Deeper explanation", expanded=False):
                    if step == 1:
                        _render_deeper_step1(lesson)
                    elif step == 2:
                        _render_deeper_step2_beginner(bundle)
                    elif step == 3:
                        _render_deeper_step3(bundle, lesson)
                    elif step == 4:
                        _render_deeper_step4(lesson)
                    elif step == 5:
                        _render_deeper_step5(lesson)
                    else:
                        st.markdown(lesson.get("how", ""))

                with st.container():
                    suffix = "_tutor"
                    if step == 1:
                        charts.render_market_movement(
                            bundle.last_chart_df,
                            bundle.last_trades,
                            bundle.last_overlay_cols,
                            bundle.last_chart_title,
                            bundle.last_strategy,
                            last_params=bundle.last_params,
                            checkbox_key=f"trade_marker_toggle{suffix}",
                            show_heading=False,
                        )
                    elif step == 2:
                        tables.render_strategy_decisions(
                            bundle.last_strategy,
                            bundle.last_trades,
                            download_key=f"download_latest_trades{suffix}",
                            show_heading=False,
                        )
                    elif step == 3:
                        charts.render_equity_section(
                            bundle.last_equity_curve,
                            download_key=f"download_latest_equity{suffix}",
                            show_heading=False,
                        )
                    elif step == 4:
                        metrics.render_performance_summary(
                            bundle.last_metrics,
                            show_heading=False,
                            show_details_expander=False,
                            nested_in_column=True,
                        )
                    elif step == 5:
                        text.render_reflection_and_advanced(bundle.last_chart_df, show_heading=False, show_advanced=False)

            _render_tutor_navigation()


def _render_explore(bundle: ResultsBundle, strategy_sidebar: str) -> None:
    text.render_onboarding(strategy_sidebar)
    _render_data_quality_metrics(bundle.last_df)

    text.render_explainability(
        bundle.last_strategy,
        bundle.last_chart_df,
        bundle.last_overlay_cols,
        bundle.last_params,
    )
    st.divider()

    charts.render_market_movement(
        bundle.last_chart_df,
        bundle.last_trades,
        bundle.last_overlay_cols,
        bundle.last_chart_title,
        bundle.last_strategy,
        last_params=bundle.last_params,
        checkbox_key="trade_marker_toggle",
    )
    st.divider()

    tables.render_strategy_decisions(bundle.last_strategy, bundle.last_trades, download_key="download_latest_trades")
    st.divider()

    charts.render_equity_section(bundle.last_equity_curve, download_key="download_latest_equity")
    st.divider()

    metrics.render_performance_summary(bundle.last_metrics)
    st.divider()

    tables.render_session_summary(
        bundle.run_history, download_key="download_session_run_summary", clear_key="clear_session_history"
    )
    st.divider()

    text.render_reflection_and_advanced(bundle.last_chart_df)


def render_main_content(mode: str, bundle: ResultsBundle | None, strategy_sidebar: str) -> None:
    if bundle is None:
        text.render_empty_state()
        return
    if mode == "Tutor":
        _maybe_reset_tutor_on_strategy_change(strategy_sidebar)
        _render_tutor_shell(bundle, strategy_sidebar)
    else:
        _render_explore(bundle, strategy_sidebar)


render_app_sections = render_main_content
