"""Shared helpers for all Streamlit pages."""

import os
import streamlit as st

_CSS_PATH = os.path.join(os.path.dirname(__file__), "styles.css")


def load_css() -> None:
    """Inject styles.css into the current Streamlit page."""
    with open(_CSS_PATH, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_header(title: str = "♻️ ReCraft AI", subtitle: str = "") -> None:
    """Render the shared hero header."""
    load_css()
    col_logo, col_title = st.columns([1, 6])
    with col_logo:
        st.markdown("<div style='font-size:3.5rem;margin-top:0.3rem'>♻️</div>", unsafe_allow_html=True)
    with col_title:
        st.markdown(f'<h1 class="hero-title">{title}</h1>', unsafe_allow_html=True)
        if subtitle:
            st.markdown(f'<p class="hero-sub">{subtitle}</p>', unsafe_allow_html=True)
    st.divider()


def section(label: str) -> None:
    """Render a green left-bordered section header."""
    st.markdown(f'<div class="section-header">{label}</div>', unsafe_allow_html=True)


def step_card(index: int, text: str) -> None:
    st.markdown(
        f'<div class="step-card"><strong>Step {index}:</strong> {text}</div>',
        unsafe_allow_html=True,
    )


def price_badge(price_str: str) -> None:
    st.markdown(f'<span class="price-badge">{price_str}</span>', unsafe_allow_html=True)


def footer() -> None:
    st.markdown(
        '<div class="footer">Built with ♻️ by Team ReCraft AI | GenAI Genesis 2026 | Google Best Sustainability AI Hack</div>',
        unsafe_allow_html=True,
    )
