"""
Page 1 — DIY Studio (Refactored for Multi-Stage Workflow)
1. Upload & Analysis
2. Confirmation & Dimensions
3. Top 3 Results with Pricing & Images
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # frontend/

import requests
import streamlit as st
from utils import load_css, section, step_card, price_badge, footer

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

load_css()

# ── Session State Initialization ──────────────────────────────────────────────
if "ui_stage" not in st.session_state:
    st.session_state.ui_stage = "UPLOAD"  # UPLOAD -> CONFIRM -> RESULTS

for key, default in [
    ("analysis_result", None),
    ("confirmed_description", ""),
    ("project_plans", []),
    ("uploaded_image_bytes", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">🛠️ DIY Studio</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Step-by-step upcycling: From analysis to 3 perfect plans</p>', unsafe_allow_html=True)
st.divider()

# ── STAGE 1: UPLOAD ───────────────────────────────────────────────────────────
if st.session_state.ui_stage == "UPLOAD":
    section("📸 1. Upload & Identify")
    uploaded_file = st.file_uploader(
        "Drop an image of your waste material",
        type=["jpg", "jpeg", "png", "webp"],
    )

    if uploaded_file:
        img_bytes = uploaded_file.read()
        st.session_state.uploaded_image_bytes = img_bytes
        st.image(img_bytes, caption="📷 Material Preview", use_container_width=True)

        if st.button("🔍 Start AI Analysis", type="primary", use_container_width=True):
            with st.spinner("🤖 Qwen is analyzing your material…"):
                try:
                    resp = requests.post(
                        f"{API_BASE}/api/analyze",
                        files={"file": (uploaded_file.name, img_bytes, uploaded_file.type)},
                        timeout=60,
                    )
                    resp.raise_for_status()
                    st.session_state.analysis_result = resp.json()
                    st.session_state.confirmed_description = st.session_state.analysis_result["description"]
                    st.session_state.ui_stage = "CONFIRM"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Analysis failed: {e}")

# ── STAGE 2: CONFIRM & DIMENSIONS ─────────────────────────────────────────────
elif st.session_state.ui_stage == "CONFIRM":
    section("📝 2. Confirm Description & Size")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        if st.session_state.uploaded_image_bytes:
            st.image(st.session_state.uploaded_image_bytes, use_container_width=True)
    
    with col2:
        st.info(f"🤖 AI identified: **{st.session_state.analysis_result.get('material_name')}**")
        
        # Confirmation / Edit area
        desc = st.text_area(
            "How would you describe this item?",
            value=st.session_state.confirmed_description,
            help="You can edit this if the AI missed anything.",
            height=100
        )
        
        st.markdown("### 📏 Dimensions")
        d_col1, d_col2, d_col3, d_col4 = st.columns([1, 1, 1, 1.2])
        L = d_col1.text_input("Length", placeholder="0", key="dim_l")
        W = d_col2.text_input("Width", placeholder="0", key="dim_w")
        H = d_col3.text_input("Height", placeholder="0", key="dim_h")
        unit = d_col4.selectbox("Unit", ["cm", "inch"], index=0, key="dim_unit")
        
        dims_str = f"{L}x{W}x{H} {unit}" if (L or W or H) else "Standard size"
        
        ccol1, ccol2 = st.columns(2)
        if ccol1.button("⬅️ Back", use_container_width=True):
            st.session_state.ui_stage = "UPLOAD"
            st.rerun()
            
        if ccol2.button("✨ Generate 3 Plans", type="primary", use_container_width=True):
            if not L and not W and not H:
                st.warning("Please enter at least one dimension!")
            else:
                st.session_state.confirmed_description = desc
                with st.spinner("🧠 gpt-oss is dreaming of 3 amazing plans…"):
                    try:
                        resp = requests.post(
                            f"{API_BASE}/api/generate-plans",
                            json={"description": desc, "dimensions": dims_str},
                            timeout=120
                        )
                        resp.raise_for_status()
                        st.session_state.project_plans = resp.json()["plans"]
                        st.session_state.ui_stage = "RESULTS"
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Plan generation failed: {e}")

# ── STAGE 3: RESULTS ──────────────────────────────────────────────────────────
elif st.session_state.ui_stage == "RESULTS":
    section("🌟 3 Upcycling Masterpieces")
    
    if st.button("🔄 Start Over", use_container_width=False):
        st.session_state.ui_stage = "UPLOAD"
        st.session_state.project_plans = []
        st.rerun()

    plans = st.session_state.project_plans
    
    # Display 3 separate columns/sections for the plans
    for idx, plan in enumerate(plans):
        with st.container(border=True):
            pcol1, pcol2 = st.columns([2, 3], gap="medium")
            
            with pcol1:
                # Preview image
                if plan.get("image_url"):
                    st.image(plan["image_url"], caption=f"Result Preview: {plan['project_name']}", use_container_width=True)
                else:
                    st.warning("🎨 No preview image generated.")
                
                # Pricing & Impact info
                pr = plan.get("price_estimate")
                co2 = plan.get("co2_saved_kg", 0)
                
                impact_col1, impact_col2 = st.columns(2)
                with impact_col1:
                    if pr:
                        st.metric("💰 Value", f"${pr.get('recommended_price_usd', 0):.1f}")
                with impact_col2:
                    st.metric("🌱 CO2 Saved", f"{co2} kg")
                
                if pr:
                    st.caption(f"Reasoning: {pr.get('justification')}")
                
                st.divider()
                
                # Save Button for this specific plan
                token = st.session_state.get("auth_token")
                if token:
                    if st.button(f"💾 Save Plan {idx+1}", key=f"save_plan_{idx}", use_container_width=True):
                        try:
                            save_resp = requests.post(
                                f"{API_BASE}/api/saves",
                                json={"token": token, "item": plan},
                                timeout=10
                            )
                            save_resp.raise_for_status()
                            st.toast(f"✅ plan {idx+1} saved!")
                        except Exception as e:
                            st.error(f"Save failed: {e}")
                else:
                    st.caption("🔑 Log in to save this plan")
            
            with pcol2:
                st.markdown(f"## {idx+1}. {plan['project_name']}")
                st.markdown(f"*{plan['tagline']}*")
                
                m1, m2 = st.columns(2)
                m1.metric("⏱️ Time", plan.get("time_estimate", "—"))
                m2.metric("💪 Difficulty", plan.get("difficulty", "—"))
                
                with st.expander("🛠️ View Instructions"):
                    st.markdown("**Materials needed:**")
                    for m in plan.get("materials_needed", []):
                        st.markdown(f"- {m}")
                    
                    st.markdown("**Steps:**")
                    for i, step in enumerate(plan.get("steps", []), 1):
                        step_card(i, step)
                    
                    st.info(f"🌱 {plan.get('sustainability_impact')}")

st.divider()

# ── Past Ideas Section ────────────────────────────────────────────────────────
token = st.session_state.get("auth_token")
if token:
    section("📦 My Profile")
    if st.button("🔄 Load My Saved Designs", use_container_width=True):
        st.info("Your past designs will appear here.")

footer()
