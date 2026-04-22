"""Tutor mode step controller (Streamlit session_state only). Steps 0 (welcome) through 5."""
from __future__ import annotations

import streamlit as st

STEP_KEY = "step"
_MIN_STEP = 0
_MAX_STEP = 5


def get_current_step() -> int:
    st.session_state.setdefault(STEP_KEY, _MIN_STEP)
    s = int(st.session_state[STEP_KEY])
    return max(_MIN_STEP, min(_MAX_STEP, s))


def set_step(n: int) -> None:
    st.session_state[STEP_KEY] = max(_MIN_STEP, min(_MAX_STEP, int(n)))


def next_step() -> None:
    set_step(get_current_step() + 1)


def prev_step() -> None:
    set_step(get_current_step() - 1)


def reset_steps() -> None:
    st.session_state[STEP_KEY] = _MIN_STEP
