"""
ReCraft AI — Navigation Controller
- Account section comes first (UX: identity before action)
- Login/Sign Up hidden from sidebar when already logged in
- User info + Logout always shown in sidebar when authenticated
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

st.set_page_config(
    page_title="ReCraft AI ♻️",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar: user info + logout (shown on every page when logged in) ──────────
token = st.session_state.get("auth_token")
if token:
    avatar = st.session_state.get("auth_avatar", "♻️")
    username = st.session_state.get("auth_username", "")
    with st.sidebar:
        st.markdown(f"### {avatar} {username}")
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.auth_token = None
            st.session_state.auth_username = None
            st.session_state.auth_avatar = None
            st.rerun()
        st.divider()

# ── Navigation — Account section first, Login hidden when logged in ───────────
account_pages = [
    st.Page("pages/3_Profile.py", title="My Profile", icon="👤"),
]
if not token:
    # Only show Login/Sign Up in sidebar when NOT logged in
    account_pages.append(
        st.Page("pages/0_Login.py", title="Login / Sign Up", icon="🔑")
    )

pg = st.navigation(
    {
        "Account": account_pages,
        "Create": [
            st.Page("pages/1_DIY_Studio.py", title="DIY Studio", icon="🛠️", default=True),
        ],
        "Community": [
            st.Page("pages/2_Marketplace.py", title="Marketplace", icon="🛍️"),
            st.Page("pages/4_Community.py", title="Community Chat", icon="💬"),
        ],
    }
)

pg.run()
