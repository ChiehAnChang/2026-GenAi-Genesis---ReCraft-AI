"""
ReCraft AI — Streamlit Frontend
Member 2 (FE) file: app.py
"""

import os
import base64
import io
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ReCraft AI ♻️",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.hero-title {
    font-size: 3.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #22c55e, #16a34a, #15803d);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0;
}
.hero-sub {
    font-size: 1.1rem;
    color: #6b7280;
    margin-top: 0.2rem;
}
.step-card {
    background: linear-gradient(135deg, #f0fdf4, #dcfce7);
    border: 1px solid #bbf7d0;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin: 0.4rem 0;
    font-size: 0.95rem;
}
.market-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 1rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s;
}
.market-card:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.12); }
.price-badge {
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: white;
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-weight: 600;
    font-size: 0.85rem;
    display: inline-block;
}
.section-header {
    font-size: 1.6rem;
    font-weight: 700;
    color: #111827;
    border-left: 4px solid #22c55e;
    padding-left: 0.8rem;
    margin: 1.5rem 0 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "upcycle_result" not in st.session_state:
    st.session_state.upcycle_result = None
if "price_result" not in st.session_state:
    st.session_state.price_result = None
if "uploaded_image_bytes" not in st.session_state:
    st.session_state.uploaded_image_bytes = None


# ─────────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.markdown("<div style='font-size:3.5rem;margin-top:0.3rem'>♻️</div>", unsafe_allow_html=True)
with col_title:
    st.markdown('<h1 class="hero-title">ReCraft AI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Upload household waste → Get AI-powered upcycling ideas → Sell on the community marketplace</p>', unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — UPLOAD & ANALYSE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📸 Upload & Analyse</div>', unsafe_allow_html=True)

upload_col, result_col = st.columns([1, 1], gap="large")

with upload_col:
    uploaded_file = st.file_uploader(
        "Drop an image of your waste material",
        type=["jpg", "jpeg", "png", "webp"],
        help="Supports JPG, PNG, WEBP",
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
                    st.session_state.price_result = None  # Reset price on new upload
                    st.rerun()
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot reach the API. Is the backend running?")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

with result_col:
    res = st.session_state.upcycle_result
    if res:
        st.success(f"✅ Identified: **{res.get('material', 'Unknown material')}**")

        # Flux-1 generated image
        if res.get("image_url"):
            with st.tabs(["🖼️ AI Vision", "📷 Original"]):
                pass
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

        meta_col1, meta_col2 = st.columns(2)
        meta_col1.metric("⏱️ Time", res.get("time_estimate", "—"))
        meta_col2.metric("💪 Difficulty", res.get("difficulty", "—"))

        st.markdown("**Step-by-step instructions:**")
        for i, step in enumerate(res.get("steps", []), 1):
            st.markdown(
                f'<div class="step-card"><strong>Step {i}:</strong> {step}</div>',
                unsafe_allow_html=True,
            )

        if res.get("sustainability_impact"):
            st.info(f"🌱 {res['sustainability_impact']}")

        st.markdown("**Additional materials needed:**")
        for mat in res.get("materials_needed", []):
            st.markdown(f"- {mat}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — PRICE ESTIMATE
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.upcycle_result:
    st.markdown('<div class="section-header">💰 Market Price Estimate</div>', unsafe_allow_html=True)

    price_col, slider_col = st.columns([2, 1], gap="large")

    with slider_col:
        labor_hours = st.slider(
            "⏱️ Your estimated labor hours",
            min_value=0.5,
            max_value=12.0,
            value=float(st.session_state.upcycle_result.get("time_estimate", "2 hours").split()[0]) if st.session_state.upcycle_result.get("time_estimate", "").split()[0].replace(".", "").isdigit() else 2.0,
            step=0.5,
            help="Adjusting this recalculates the suggested price",
        )

        if st.button("💡 Get Price Estimate", type="primary", use_container_width=True):
            with st.spinner("📊 Analysing market trends…"):
                try:
                    resp = requests.post(
                        f"{API_BASE}/api/price",
                        json={
                            "upcycle_result": st.session_state.upcycle_result,
                            "labor_hours": labor_hours,
                        },
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
            p_col1, p_col2, p_col3 = st.columns(3)
            p_col1.metric(
                "💰 Recommended Price",
                f"${pr.get('recommended_price_usd', 0):.2f}",
            )
            p_col2.metric(
                "📉 Price Range Low",
                f"${pr.get('price_range_low_usd', 0):.2f}",
            )
            p_col3.metric(
                "📈 Price Range High",
                f"${pr.get('price_range_high_usd', 0):.2f}",
            )
            st.caption(f"💬 {pr.get('justification', '')}")

            with st.expander("📊 Full Price Breakdown"):
                breakdown = {
                    "Materials Cost": f"${pr.get('materials_cost_usd', 0):.2f}",
                    "Labor Cost": f"${pr.get('labor_cost_usd', 0):.2f}",
                    "Platform Fee": f"${pr.get('platform_fee_usd', 0):.2f}",
                    "Labor Hours": pr.get("labor_hours", "-"),
                    "Hourly Rate": f"${pr.get('suggested_hourly_rate_usd', 0):.2f}",
                }
                for k, v in breakdown.items():
                    st.markdown(f"- **{k}:** {v}")

    # ── Publish button ────────────────────────────────────────────────────────
    st.divider()
    res = st.session_state.upcycle_result
    pr = st.session_state.price_result
    price_str = f"${pr['price_range_low_usd']:.0f} – ${pr['price_range_high_usd']:.0f}" if pr else "Price TBD"

    if st.button("🌍 Publish to Community Marketplace", type="secondary", use_container_width=True):
        try:
            payload = {
                "project_name": res.get("project_name", "Upcycled Item"),
                "material": res.get("material", ""),
                "tagline": res.get("tagline", ""),
                "price": price_str,
                "recommended_price_usd": pr.get("recommended_price_usd", 0) if pr else 0,
                "steps": res.get("steps", []),
                "image_url": res.get("image_url"),
            }
            resp = requests.post(f"{API_BASE}/api/marketplace", json=payload, timeout=10)
            resp.raise_for_status()
            st.success("🎉 Published to the Community Marketplace!")
            st.balloons()
        except Exception as e:
            st.error(f"❌ Could not publish: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — COMMUNITY MARKETPLACE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🛍️ Community Marketplace</div>', unsafe_allow_html=True)

try:
    market_resp = requests.get(f"{API_BASE}/api/marketplace", timeout=5)
    market_resp.raise_for_status()
    items = market_resp.json()
except Exception:
    items = []
    st.warning("⚠️ Could not reach marketplace API. Showing local session items only.")

if not items:
    st.info("The marketplace is empty — be the first to publish your upcycled creation!")
else:
    cols = st.columns(3)
    for idx, item in enumerate(items):
        col = cols[idx % 3]
        with col:
            with st.container():
                if item.get("image_url"):
                    try:
                        st.image(item["image_url"], use_container_width=True)
                    except Exception:
                        st.markdown("🖼️ *(image unavailable)*")
                else:
                    st.markdown(
                        f"<div style='background:linear-gradient(135deg,#f0fdf4,#dcfce7);border-radius:12px;height:140px;display:flex;align-items:center;justify-content:center;font-size:2.5rem'>♻️</div>",
                        unsafe_allow_html=True,
                    )

                st.markdown(f"**{item.get('project_name', 'Upcycled Item')}**")
                st.caption(item.get("tagline", ""))
                st.markdown(
                    f"<span class='price-badge'>{item.get('price', 'Price TBD')}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"❤️ {item.get('likes', 0)} likes")

                # Like button (advanced)
                if st.button(f"❤️ Like", key=f"like-{item.get('id', idx)}"):
                    try:
                        requests.post(
                            f"{API_BASE}/api/marketplace/{item.get('id')}/like",
                            timeout=5,
                        )
                        st.rerun()
                    except Exception:
                        st.warning("Could not record like.")

                st.markdown("---")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<br><center style='color:#9ca3af;font-size:0.8rem'>Built with ♻️ by Team ReCraft AI | GenAI Genesis 2026 | Google Best Sustainability AI Hack</center>",
    unsafe_allow_html=True,
)
