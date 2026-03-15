"""
Page 0 — Login / Sign Up
Handles authentication via session_state token.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
import streamlit as st
from utils import load_css, footer

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


load_css()

# ── Already logged in? ────────────────────────────────────────────────────────
if st.session_state.get("auth_token"):
    username = st.session_state.get("auth_username", "")
    st.success(f"✅ You're logged in as **{username}**")
    if st.button("🚪 Log Out", type="secondary"):
        st.session_state.auth_token = None
        st.session_state.auth_username = None
        st.session_state.auth_avatar = None
        st.rerun()
    st.stop()

# ── Auth form ─────────────────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">Welcome to ReCraft AI ♻️</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Log in or create an account to save your upcycling creations.</p>', unsafe_allow_html=True)
st.divider()

tab_login, tab_signup = st.tabs(["🔑 Log In", "🌱 Sign Up"])

with tab_login:
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="your_username")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)

    if submitted:
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            try:
                resp = requests.post(
                    f"{API_BASE}/api/auth/login",
                    json={"username": username, "password": password},
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
                st.session_state.auth_token = data["token"]
                st.session_state.auth_username = data["username"]
                # Fetch avatar
                me = requests.get(f"{API_BASE}/api/auth/me", params={"token": data["token"]}, timeout=5).json()
                st.session_state.auth_avatar = me.get("avatar_emoji", "♻️")
                st.success(f"Welcome back, **{data['username']}**! 🎉")
                st.rerun()
            except requests.exceptions.HTTPError as e:
                detail = e.response.json().get("detail", "Login failed.")
                st.error(f"❌ {detail}")
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot reach the API. Is the backend running?")

with tab_signup:
    with st.form("signup_form"):
        new_username = st.text_input("Choose a username", placeholder="eco_crafter_42")
        new_email = st.text_input("Email (optional)", placeholder="you@example.com")
        new_password = st.text_input("Password", type="password", placeholder="••••••••")
        new_password2 = st.text_input("Confirm Password", type="password", placeholder="••••••••")
        submitted2 = st.form_submit_button("Create Account", type="primary", use_container_width=True)

    if submitted2:
        if not new_username or not new_password:
            st.error("Username and password are required.")
        elif new_password != new_password2:
            st.error("Passwords don't match.")
        elif len(new_password) < 4:
            st.error("Password must be at least 4 characters.")
        else:
            try:
                resp = requests.post(
                    f"{API_BASE}/api/auth/register",
                    json={"username": new_username, "email": new_email, "password": new_password},
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
                st.session_state.auth_token = data["token"]
                st.session_state.auth_username = data["username"]
                me = requests.get(f"{API_BASE}/api/auth/me", params={"token": data["token"]}, timeout=5).json()
                st.session_state.auth_avatar = me.get("avatar_emoji", "♻️")
                st.success(f"Account created! Welcome, **{data['username']}**! 🌱")
                st.rerun()
            except requests.exceptions.HTTPError as e:
                detail = e.response.json().get("detail", "Sign up failed.")
                st.error(f"❌ {detail}")
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot reach the API.")

footer()
