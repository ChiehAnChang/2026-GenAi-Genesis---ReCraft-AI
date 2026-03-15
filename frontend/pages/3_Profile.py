"""
Page 3 — My Profile
Shows user info and all saved DIY items. Only accessible when logged in.
"""

from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
import streamlit as st
from utils import load_css, section, step_card, price_badge, footer

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

load_css()

# ── Auth guard ────────────────────────────────────────────────────────────────
token = st.session_state.get("auth_token")
if not token:
    st.warning("🔑 Please **Log In** first to view your profile.")
    st.page_link("pages/0_Login.py", label="Go to Login →", icon="🔑")
    st.stop()

# ── Fetch Initial Data ───────────────────────────────────────────────────────
try:
    # 1. Fetch user info
    me_resp = requests.get(f"{API_BASE}/api/auth/me", params={"token": token}, timeout=5)
    me_resp.raise_for_status()
    user = me_resp.json()
    
    # 2. Fetch saved items (Needed for CO2 calculation in header)
    saves_resp = requests.get(f"{API_BASE}/api/saves", params={"token": token}, timeout=5)
    saves_resp.raise_for_status()
    saves = saves_resp.json()
    
except Exception as e:
    st.error(f"❌ Session error: {e}")
    st.session_state.auth_token = None
    st.stop()

# ── Data Processing ──────────────────────────────────────────────────────────
avatar = user.get("avatar_emoji", "♻️")
username = user.get("username", "")
email = user.get("email", "")
saved_count = len(saves)

# Calculate total CO2 impact
total_co2 = sum([item.get("co2_saved_kg", 0) for item in saves])
# 1kg CO2 is roughly the amount a standard car emits over 5km
driving_equiv = round(total_co2 * 5, 1)

# ── Profile Header ────────────────────────────────────────────────────────────
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
    m2.metric("🌍 Total CO₂ Impact", f"{total_co2:.1f} kg")
    
    st.info(f"""
    ### 🌱 Your Environmental Impact
    Your saved **{total_co2:.1f} kg** of CO₂ is roughly equivalent to:
    ## 🚗 {driving_equiv} km
    of driving a standard gasoline car. That's a huge win for the planet! 🌍✨
    """)

if st.button("🚪 Log Out", type="secondary"):
    st.session_state.auth_token = None
    st.session_state.auth_username = None
    st.session_state.auth_avatar = None
    st.rerun()

st.divider()

# ── Saved DIY Items ───────────────────────────────────────────────────────────
section("🗂️ My Saved Projects")

if not saves:
    st.info("You haven't saved any DIY projects yet. Head to the 🛠️ DIY Studio and analyse your first waste item!")
else:
    for item in saves:
        with st.expander(f"🛠️ **{item.get('project_name', 'Upcycled Item')}** — _{item.get('material', 'waste')}_", expanded=False):
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
                
                st.caption(f"🌍 CO₂ Saved: {item.get('co2_saved_kg', 0)} kg")

            # Delete button
            saved_id = item.get("saved_id", "")
            if st.button(f"🗑️ Remove", key=f"del-{saved_id}"):
                try:
                    # Point to backend/auth.py handles deletion but backend/main.py needs the route
                    # Check if route exists in main.py
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
