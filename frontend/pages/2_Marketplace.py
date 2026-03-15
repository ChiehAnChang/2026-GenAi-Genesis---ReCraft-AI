"""
Page 2 — Community Marketplace
Browse all published upcycled items in a 3-column grid. Like items.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # frontend/

import requests
import streamlit as st
from utils import load_css, section, price_badge, footer

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


load_css()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">🛍️ Community Marketplace</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Explore upcycled creations published by the community. Find inspiration or buy something unique.</p>', unsafe_allow_html=True)
st.divider()

# ── Fetch items ───────────────────────────────────────────────────────────────
try:
    resp = requests.get(f"{API_BASE}/api/marketplace", timeout=5)
    resp.raise_for_status()
    items = resp.json()
except requests.exceptions.ConnectionError:
    st.error("❌ Cannot reach the backend API. Make sure it's running.")
    items = []
except Exception as e:
    st.warning(f"⚠️ Could not load marketplace: {e}")
    items = []

# ── Controls ──────────────────────────────────────────────────────────────────
if items:
    ctrl_col, refresh_col = st.columns([4, 1])
    with ctrl_col:
        st.markdown(f"**{len(items)} item{'s' if len(items) != 1 else ''} listed**")
    with refresh_col:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    # ── 3-column grid ─────────────────────────────────────────────────────────
    section("🌿 Latest Creations")

    cols = st.columns(3)
    for idx, item in enumerate(items):
        with cols[idx % 3]:
            # Thumbnail
            if item.get("image_url"):
                try:
                    st.image(item["image_url"], use_container_width=True)
                except Exception:
                    st.markdown(
                        "<div style='background:linear-gradient(135deg,#f0fdf4,#dcfce7);"
                        "border-radius:12px;height:140px;display:flex;align-items:center;"
                        "justify-content:center;font-size:2.5rem'>♻️</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    "<div style='background:linear-gradient(135deg,#f0fdf4,#dcfce7);"
                    "border-radius:12px;height:140px;display:flex;align-items:center;"
                    "justify-content:center;font-size:2.5rem'>♻️</div>",
                    unsafe_allow_html=True,
                )

            # Info
            st.markdown(f"**{item.get('project_name', 'Upcycled Item')}**")
            st.caption(item.get("tagline", ""))
            price_badge(item.get("price", "Price TBD"))

            like_col, count_col = st.columns([1, 1])
            with like_col:
                if st.button("❤️ Like", key=f"like-{item.get('id', idx)}"):
                    try:
                        requests.post(
                            f"{API_BASE}/api/marketplace/{item.get('id')}/like",
                            timeout=5,
                        )
                        st.rerun()
                    except Exception:
                        st.toast("Could not record like", icon="⚠️")
            with count_col:
                st.markdown(f"<span style='line-height:2.2'>{item.get('likes', 0)} likes</span>", unsafe_allow_html=True)

            # Preview first step
            steps = item.get("steps", [])
            if steps:
                with st.expander("👀 Preview steps"):
                    for i, s in enumerate(steps[:3], 1):
                        st.markdown(f"{i}. {s}")
                    if len(steps) > 3:
                        st.caption(f"+ {len(steps) - 3} more steps…")

            st.markdown("---")
else:
    st.info("The marketplace is empty — publish something from the 🛠️ DIY Studio!")

footer()
