"""
ReCraft AI — Navigation Controller
Uses st.navigation() for full sidebar control:
- Hides this landing page from sidebar
- Sets page order by UX priority
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

# ── Sidebar nav with UX-first ordering ───────────────────────────────────────
# Standard SaaS order: primary action → discovery → account → auth
pg = st.navigation(
    {
        "Create": [
            st.Page("pages/1_DIY_Studio.py", title="DIY Studio", icon="🛠️", default=True),
        ],
        "Community": [
            st.Page("pages/2_Marketplace.py", title="Marketplace", icon="🛍️"),
        ],
        "Account": [
            st.Page("pages/3_Profile.py", title="My Profile", icon="👤"),
            st.Page("pages/0_Login.py", title="Login / Sign Up", icon="🔑"),
        ],
    }
)

pg.run()
