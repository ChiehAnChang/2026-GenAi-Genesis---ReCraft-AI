"""
Page 1 — DIY Studio
Upload waste photo → AI identifies material → 5-step DIY plan → price estimate → publish
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # frontend/

import requests
import streamlit as st
from utils import load_css, section, step_card, price_badge, footer

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


load_css()

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("upcycle_result", None),
    ("price_result", None),
    ("uploaded_image_bytes", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">🛠️ DIY Studio</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Upload any household waste → get an AI-generated upcycling plan + market price estimate</p>', unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — UPLOAD & ANALYSE
# ─────────────────────────────────────────────────────────────────────────────
section("📸 Upload & Analyse")

upload_col, result_col = st.columns([1, 1], gap="large")

with upload_col:
    uploaded_file = st.file_uploader(
        "Drop an image of your waste material",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        img_bytes = uploaded_file.read()
        st.session_state.uploaded_image_bytes = img_bytes
        st.image(img_bytes, caption="📷 Uploaded material", use_container_width=True)

        if st.button("🔍 Analyse & Generate Ideas", type="primary", use_container_width=True):
            with st.spinner("🤖 ReCraft AI is thinking…"):
                try:
                    resp = requests.post(
                        f"{API_BASE}/api/upcycle",
                        files={"file": (uploaded_file.name, img_bytes, uploaded_file.type)},
                        timeout=120,
                    )
                    resp.raise_for_status()
                    st.session_state.upcycle_result = resp.json()
                    st.session_state.price_result = None
                    st.rerun()
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot reach the API. Is the backend running?")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

with result_col:
    res = st.session_state.upcycle_result
    if res:
        st.success(f"✅ Identified: **{res.get('material', 'Unknown material')}**")

        # Image tabs: AI Vision vs Original
        if res.get("image_url"):
            tab_ai, tab_orig = st.tabs(["🖼️ AI Vision", "📷 Original Photo"])
            with tab_ai:
                st.image(res["image_url"], caption="Flux-1 AI Visualisation", use_container_width=True)
            with tab_orig:
                if st.session_state.uploaded_image_bytes:
                    st.image(st.session_state.uploaded_image_bytes, use_container_width=True)
        elif res.get("edited_image_url"):
            st.image(res["edited_image_url"], caption="🎨 AI-Edited Vision", use_container_width=True)

        st.markdown(f"### 🛠️ {res.get('project_name', 'Your Upcycled Project')}")
        st.caption(res.get("tagline", ""))

        m1, m2 = st.columns(2)
        m1.metric("⏱️ Time", res.get("time_estimate", "—"))
        m2.metric("💪 Difficulty", res.get("difficulty", "—"))

        st.markdown("**Step-by-step instructions:**")
        for i, step in enumerate(res.get("steps", []), 1):
            step_card(i, step)

        if res.get("sustainability_impact"):
            st.info(f"🌱 {res['sustainability_impact']}")

        if res.get("materials_needed"):
            st.markdown("**Additional materials needed:**")
            for mat in res["materials_needed"]:
                st.markdown(f"- {mat}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — PRICE ESTIMATE
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.upcycle_result:
    section("💰 Market Price Estimate")

    price_col, slider_col = st.columns([2, 1], gap="large")

    res = st.session_state.upcycle_result

    with slider_col:
        # Parse default labor hours from time_estimate string
        try:
            default_hours = float(res.get("time_estimate", "2 hours").split()[0])
        except (ValueError, IndexError):
            default_hours = 2.0

        labor_hours = st.slider(
            "⏱️ Your estimated labor hours",
            min_value=0.5,
            max_value=12.0,
            value=default_hours,
            step=0.5,
        )

        if st.button("💡 Get Price Estimate", type="primary", use_container_width=True):
            with st.spinner("📊 Analysing market trends…"):
                try:
                    resp = requests.post(
                        f"{API_BASE}/api/price",
                        json={"upcycle_result": res, "labor_hours": labor_hours},
                        timeout=30,
                    )
                    resp.raise_for_status()
                    st.session_state.price_result = resp.json()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Pricing error: {e}")

    with price_col:
        pr = st.session_state.price_result
        if pr:
            p1, p2, p3 = st.columns(3)
            p1.metric("💰 Recommended", f"${pr.get('recommended_price_usd', 0):.2f}")
            p2.metric("📉 Low", f"${pr.get('price_range_low_usd', 0):.2f}")
            p3.metric("📈 High", f"${pr.get('price_range_high_usd', 0):.2f}")
            st.caption(f"💬 {pr.get('justification', '')}")

            with st.expander("📊 Full Price Breakdown"):
                for label, val in {
                    "Materials Cost": f"${pr.get('materials_cost_usd', 0):.2f}",
                    "Labor Cost": f"${pr.get('labor_cost_usd', 0):.2f}",
                    "Platform Fee": f"${pr.get('platform_fee_usd', 0):.2f}",
                    "Labor Hours": pr.get("labor_hours", "-"),
                    "Hourly Rate": f"${pr.get('suggested_hourly_rate_usd', 0):.2f}",
                }.items():
                    st.markdown(f"- **{label}:** {val}")



    # ── Save + Publish ─────────────────────────────────────────────────────────
    st.divider()

    pr = st.session_state.price_result
    price_str = (
        f"${pr['price_range_low_usd']:.0f} – ${pr['price_range_high_usd']:.0f}"
        if pr else "Price TBD"
    )

    action_col1, action_col2 = st.columns(2)

    # Save to account (only if logged in)
    token = st.session_state.get("auth_token")
    with action_col1:
        if token:
            if st.button("💾 Save to My Account", type="primary", use_container_width=True):
                try:
                    save_payload = {
                        **res,
                        "price": price_str,
                        "recommended_price_usd": pr["recommended_price_usd"] if pr else 0,
                    }
                    save_resp = requests.post(
                        f"{API_BASE}/api/saves",
                        json={"token": token, "item": save_payload},
                        timeout=10,
                    )
                    save_resp.raise_for_status()
                    st.success("✅ Saved to your profile!")
                except Exception as e:
                    st.error(f"❌ Could not save: {e}")
        else:
            st.page_link("pages/0_Login.py", label="🔑 Log in to Save", icon="🔑")

    with action_col2:
        if st.button("🌍 Publish to Marketplace", type="secondary", use_container_width=True):
            try:
                payload = {
                    "project_name": res.get("project_name", "Upcycled Item"),
                    "material": res.get("material", ""),
                    "tagline": res.get("tagline", ""),
                    "price": price_str,
                    "recommended_price_usd": pr["recommended_price_usd"] if pr else 0,
                    "steps": res.get("steps", []),
                    "image_url": res.get("image_url"),
                }
                resp = requests.post(f"{API_BASE}/api/marketplace", json=payload, timeout=10)
                resp.raise_for_status()
                st.success("🎉 Published to the Community Marketplace!")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Could not publish: {e}")

footer()

