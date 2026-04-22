"""Streamlit layout primitives (centering, section chrome, tables/charts)."""
from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any

import pandas as pd
import streamlit as st

from ui.helpers.formatting import section_heading_html

_WIDE_COLUMNS = [0.4, 11.2, 0.4]
_CENTER_COLUMNS = [0.7, 10.6, 0.7]
_NARROW_COLUMNS = [1.2, 9.6, 1.2]


@contextmanager
def centered_container() -> Generator[None, None, None]:
    left, mid, right = st.columns(_CENTER_COLUMNS)
    with mid:
        yield


@contextmanager
def narrow_container() -> Generator[None, None, None]:
    left, mid, right = st.columns(_NARROW_COLUMNS)
    with mid:
        yield


@contextmanager
def section_block(
    title: str | None = None,
    tone: str | None = None,
    *,
    tutor_chrome: bool = False,
) -> Generator[None, None, None]:
    """Bordered Streamlit container with optional tone heading."""
    with st.container(border=True):
        if title and tone:
            render_section_heading(title, tone)
        inner_open = (
            "<div style='padding:0.05rem 0.25rem 0.25rem 0.25rem;'>"
            if tutor_chrome
            else "<div style='padding:0.25rem 0.2rem 0.2rem 0.2rem;'>"
        )
        st.markdown(inner_open, unsafe_allow_html=True)
        yield
        st.markdown("</div>", unsafe_allow_html=True)


_TUTOR_CARD_SHADOW_CSS = """
<style>
section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] {
  box-shadow: 0 14px 44px -14px rgba(0, 0, 0, 0.38),
    0 6px 16px -6px rgba(0, 0, 0, 0.22) !important;
  border-radius: 14px !important;
  overflow: hidden !important;
}
section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stProgress"] {
  margin-top: 0 !important;
  padding-top: 0 !important;
}
</style>
"""


@contextmanager
def tutor_lesson_card() -> Generator[None, None, None]:
    """Apply tutor styling (shadowed bordered card) around main lesson content."""
    st.markdown(_TUTOR_CARD_SHADOW_CSS, unsafe_allow_html=True)
    with section_block(tutor_chrome=True):
        yield


@contextmanager
def centered_main_block() -> Generator[None, None, None]:
    """Centre primary content in the wide middle column."""
    left, mid, right = st.columns(_WIDE_COLUMNS)
    with mid:
        yield


def render_centered_button_pair(left_fn: Callable[[], None], right_fn: Callable[[], None]) -> None:
    """Render two buttons side by side within the centred layout."""
    left, mid, right = st.columns(_WIDE_COLUMNS)
    with mid:
        c1, c2 = st.columns(2, gap="small")
        with c1:
            left_fn()
        with c2:
            right_fn()


def render_section_heading(title: str, tone: str) -> None:
    st.markdown(section_heading_html(title, tone), unsafe_allow_html=True)


def render_section_heading_centered(title: str, tone: str) -> None:
    """Centre a tone-styled section heading in the active column."""
    inner = section_heading_html(title, tone)
    st.markdown(
        f'<div style="display:flex;justify-content:center;width:100%;">{inner}</div>',
        unsafe_allow_html=True,
    )


def render_app_header(
    title: str,
    subtitle: str,
    *,
    subtitle_color: str = "#60a5fa",
) -> None:
    """Render the centred title and subtitle block."""
    left, mid, right = st.columns(_CENTER_COLUMNS)
    with mid:
        st.markdown(
            f"""
<div style="text-align:center; margin-top: 0.1rem; margin-bottom: 1rem;">
  <h1 style="margin-bottom:0.3rem;">{title}</h1>
  <p style="margin:0; color:{subtitle_color};">{subtitle}</p>
</div>
""",
            unsafe_allow_html=True,
        )


def render_centered_table(df: pd.DataFrame, height: int = 300, **dataframe_kwargs: Any) -> None:
    kwargs = dict(use_container_width=True, height=height)
    kwargs.update(dataframe_kwargs)
    left, mid, right = st.columns(_WIDE_COLUMNS)
    with mid:
        st.dataframe(df, **kwargs)


def render_centered_chart(render_fn: Callable[[], None]) -> None:
    left, mid, right = st.columns(_WIDE_COLUMNS)
    with mid:
        render_fn()


def render_wide_button_row(render_fn: Callable[[], None]) -> None:
    """Place controls in the same wide centred column as charts."""
    left, mid, right = st.columns(_WIDE_COLUMNS)
    with mid:
        render_fn()
