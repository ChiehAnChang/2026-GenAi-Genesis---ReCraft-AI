"""
Page 3 — My Profile
Shows user info and all saved DIY items. Only accessible when logged in.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
import streamlit as st
from utils import load_css, section, step_card, price_badge, footer

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="My Profile — ReCraft AI",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_css()

# ── Auth guard ────────────────────────────────────────────────────────────────
token = st.session_state.get("auth_token")
if not token:
    st.warning("🔑 Please **Log In** first to view your profile.")
    st.page_link("pages/0_Login.py", label="Go to Login →", icon="🔑")
    st.stop()

# ── Fetch user info ───────────────────────────────────────────────────────────
try:
    me_resp = requests.get(f"{API_BASE}/api/auth/me", params={"token": token}, timeout=5)
    me_resp.raise_for_status()
    user = me_resp.json()
except Exception:
    st.error("❌ Session expired. Please log in again.")
    st.session_state.auth_token = None
    st.stop()

# ── Profile header ────────────────────────────────────────────────────────────
avatar = user.get("avatar_emoji", "♻️")
username = user.get("username", "")
email = user.get("email", "")
saved_count = user.get("saved_count", 0)

col_avatar, col_info = st.columns([1, 5])
with col_avatar:
    st.markdown(
        f"<div style='font-size:5rem;text-align:center;margin-top:0.5rem'>{avatar}</div>",
        unsafe_allow_html=True,
    )
with col_info:
    st.markdown(f"## {username}")
    if email:
        st.caption(f"📧 {email}")
    m1, m2 = st.columns(2)
    m1.metric("🛠️ Saved Projects", saved_count)
    m2.metric("🌍 Impact", f"{saved_count * 120}g CO₂ saved*")
    st.caption("*Estimated based on average upcycling impact vs landfill")

if st.button("🚪 Log Out", type="secondary"):
    st.session_state.auth_token = None
    st.session_state.auth_username = None
    st.session_state.auth_avatar = None
    st.rerun()

st.divider()

# ── Saved DIY items ───────────────────────────────────────────────────────────
section("🗂️ My Saved Projects")

try:
    saves_resp = requests.get(f"{API_BASE}/api/saves", params={"token": token}, timeout=5)
    saves_resp.raise_for_status()
    saves = saves_resp.json()
except Exception as e:
    st.error(f"❌ Could not load saved items: {e}")
    saves = []

if not saves:
    st.info("You haven't saved any DIY projects yet. Head to the 🛠️ DIY Studio and analyse your first waste item!")
else:
    for item in saves:
        with st.expander(f"🛠️ **{item.get('project_name', 'Upcycled Item')}** — _{item.get('material', '')}_", expanded=False):
            exp_col1, exp_col2 = st.columns([1, 2])

            with exp_col1:
                if item.get("image_url"):
                    try:
                        st.image(item["image_url"], use_container_width=True)
                    except Exception:
                        st.markdown("🖼️ *(image unavailable)*")
                else:
                    st.markdown(
                        "<div style='background:linear-gradient(135deg,#f0fdf4,#dcfce7);"
                        "border-radius:12px;height:160px;display:flex;align-items:center;"
                        "justify-content:center;font-size:3rem'>♻️</div>",
                        unsafe_allow_html=True,
                    )

            with exp_col2:
                st.markdown(f"**{item.get('tagline', '')}**")
                m1, m2 = st.columns(2)
                m1.metric("⏱️ Time", item.get("time_estimate", "—"))
                m2.metric("💪 Difficulty", item.get("difficulty", "—"))

                if item.get("price"):
                    price_badge(item["price"])
                    st.markdown("")

                st.markdown("**Steps:**")
                for i, step in enumerate(item.get("steps", []), 1):
                    step_card(i, step)

                if item.get("sustainability_impact"):
                    st.info(f"🌱 {item['sustainability_impact']}")

            # Delete button
            saved_id = item.get("saved_id", "")
            if st.button(f"🗑️ Remove", key=f"del-{saved_id}"):
                try:
                    requests.delete(
                        f"{API_BASE}/api/saves/{saved_id}",
                        params={"token": token},
                        timeout=5,
                    )
                    st.success("Removed from saved projects.")
                    st.rerun()
                except Exception:
                    st.error("Could not remove item.")

footer()
