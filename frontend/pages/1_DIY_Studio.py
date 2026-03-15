"""
Page 1 — DIY Studio (Refactored for Multi-Stage Workflow)
1. Upload & Analysis (Multi-Image Support)
2. Confirmation & Dimensions (Consolidated for Master Plan)
3. Top 3 Results with Pricing & Images
"""

from __future__ import annotations
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

# Multi-batch results storage
for key, default in [
    ("batch_results", []),      # List of {material_name, description, image_bytes}
    ("project_plans", []),
    ("confirmed_description", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">🛠️ DIY Studio</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Step-by-step upcycling: From analysis to your Master Plan</p>', unsafe_allow_html=True)
st.divider()

# ── STAGE 1: UPLOAD ───────────────────────────────────────────────────────────
if st.session_state.ui_stage == "UPLOAD":
    section("📸 1. Batch Upload & Identify")
    uploaded_files = st.file_uploader(
        "Drop one or more images of your waste materials",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.write(f"📁 **{len(uploaded_files)}** files selected.")
        
        if st.button("🔍 Start Batch AI Analysis", type="primary", use_container_width=True):
            st.session_state.batch_results = []
            progress_bar = st.progress(0)
            
            for i, file in enumerate(uploaded_files):
                with st.status(f"Analysing item {i+1} of {len(uploaded_files)}: {file.name}...", expanded=False):
                    try:
                        img_bytes = file.read()
                        resp = requests.post(
                            f"{API_BASE}/api/analyze",
                            files={"file": (file.name, img_bytes, file.type)},
                            timeout=60,
                        )
                        resp.raise_for_status()
                        result = resp.json()
                        result["image_bytes"] = img_bytes # Store for display later
                        st.session_state.batch_results.append(result)
                        st.write("✅ Analysis complete.")
                    except Exception as e:
                        st.error(f"❌ Failed to analyze {file.name}: {e}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            if st.session_state.batch_results:
                st.session_state.ui_stage = "CONFIRM"
                st.rerun()

# ── STAGE 2: CONFIRM & DIMENSIONS ─────────────────────────────────────────────
elif st.session_state.ui_stage == "CONFIRM":
    section("📝 2. Review Items & Create Master Plan")
    
    results = st.session_state.batch_results
    if not results:
        st.warning("No items analyzed. Please go back.")
        if st.button("⬅️ Back"):
            st.session_state.ui_stage = "UPLOAD"
            st.rerun()
        st.stop()

    st.markdown("### ✨ The Master Plan Strategy")
    st.markdown(f"AI will focus on combining use of your **{len(results)}** identified materials into single cohesive projects.")
    
    st.divider()

    # Show items in a clean grid/list for editing
    for i, item in enumerate(results):
        with st.container(border=True):
            icol1, icol2 = st.columns([1, 2])
            with icol1:
                if item.get("image_bytes"):
                    st.image(item["image_bytes"], use_container_width=True)
            with icol2:
                st.markdown(f"#### Item {i+1}: {item.get('material_name', 'Material')}")
                
                # Description
                new_desc = st.text_area(
                    "Refine material description:",
                    value=item.get("description", ""),
                    key=f"desc_edit_{i}",
                    height=68
                )
                
                # Dimensions
                d_col1, d_col2, d_col3, d_col4 = st.columns([1, 1, 1, 1.2])
                L = d_col1.text_input("Length", placeholder="0", key=f"dim_l_{i}")
                W = d_col2.text_input("Width", placeholder="0", key=f"dim_w_{i}")
                H = d_col3.text_input("Height", placeholder="0", key=f"dim_h_{i}")
                unit = d_col4.selectbox("Unit", ["cm", "inch"], index=0, key=f"dim_unit_{i}")

    st.divider()

    # Single Primary Action
    ccol1, ccol2 = st.columns([1, 2])
    if ccol1.button("⬅️ Restart Batch", use_container_width=True):
        st.session_state.ui_stage = "UPLOAD"
        st.session_state.batch_results = []
        st.rerun()
        
    if ccol2.button("🚀 Generate Master Plans with ALL Items", type="primary", use_container_width=True):
        # Aggregate all info
        all_descriptions = []
        all_dimensions = []
        for i, res in enumerate(results):
            l = st.session_state.get(f"dim_l_{i}", "0")
            w = st.session_state.get(f"dim_w_{i}", "0")
            h = st.session_state.get(f"dim_h_{i}", "0")
            u = st.session_state.get(f"dim_unit_{i}", "cm")
            
            desc_text = st.session_state.get(f"desc_edit_{i}", res.get("description", ""))
            all_descriptions.append(f"Material {i+1} ({res.get('material_name')}): {desc_text}")
            all_dimensions.append(f"Material {i+1} Size: {l}x{w}x{h} {u}")
        
        combined_desc = " | ".join(all_descriptions)
        combined_dims = " | ".join(all_dimensions)
        
        with st.spinner("🧠 Dreaming of 3 master projects using your batch of materials…"):
            try:
                resp = requests.post(
                    f"{API_BASE}/api/generate-plans",
                    json={"description": combined_desc, "dimensions": combined_dims},
                    timeout=150
                )
                resp.raise_for_status()
                st.session_state.project_plans = resp.json()["plans"]
                st.session_state.ui_stage = "RESULTS"
                st.rerun()
            except Exception as e:
                st.error(f"❌ Combination failed: {e}")

# ── STAGE 3: RESULTS ──────────────────────────────────────────────────────────
elif st.session_state.ui_stage == "RESULTS":
    section("🌟 3 Combined Masterpieces")
    
    if st.button("⬅️ Back to Review", use_container_width=False):
        st.session_state.ui_stage = "CONFIRM"
        st.rerun()

    plans = st.session_state.project_plans
    
    for idx, plan in enumerate(plans):
        with st.container(border=True):
            pcol1, pcol2 = st.columns([2, 3], gap="medium")
            
            with pcol1:
                if plan.get("image_url"):
                    st.image(plan["image_url"], caption=f"Result Preview: {plan['project_name']}", use_container_width=True)
                else:
                    st.warning("🎨 No preview image generated.")
                
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
footer()
