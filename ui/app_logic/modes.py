"""Learning mode: Tutor vs Explore (sidebar + session_state)."""
from __future__ import annotations

import streamlit as st

_MODE_KEY = "learning_mode"
_MODE_EXPLORE = "Explore (Full Dashboard)"
_MODE_TUTOR = "Tutor (Guided)"
DEFAULT_LEARNING_MODE = _MODE_TUTOR
_LM_RADIO = "learning_mode_radio"
def _persist_mode_from_radio() -> None:
    label = st.session_state[_LM_RADIO]
    st.session_state[_MODE_KEY] = _MODE_EXPLORE if label == "Explore" else _MODE_TUTOR


def get_mode() -> str:
    st.session_state.setdefault(_MODE_KEY, DEFAULT_LEARNING_MODE)
    v = st.session_state[_MODE_KEY]
    if v == _MODE_TUTOR:
        return "Tutor"
    return "Explore"


def render_mode_selector() -> None:
    """Horizontal Explore / Tutor control (segmented-style radio; same session keys as before)."""
    st.sidebar.header("Learning Mode")
    st.session_state.setdefault(_MODE_KEY, DEFAULT_LEARNING_MODE)
    if _LM_RADIO not in st.session_state:
        st.session_state[_LM_RADIO] = (
            "Explore" if st.session_state[_MODE_KEY] == _MODE_EXPLORE else "Tutor"
        )
    st.sidebar.radio(
        "Learning mode selector",
        ["Explore", "Tutor"],
        horizontal=True,
        key=_LM_RADIO,
        on_change=_persist_mode_from_radio,
        label_visibility="collapsed",
    )
    current = st.session_state[_MODE_KEY]
    st.sidebar.caption("Active: **Tutor**" if current == _MODE_TUTOR else "Active: **Explore**")
