"""
ReCraft AI — Entry Point
Streamlit multipage app. Navigation is auto-generated from frontend/pages/.
"""

import os
import sys

# Make frontend/ importable (for utils, styles)
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from utils import render_header, footer

st.set_page_config(
    page_title="ReCraft AI ♻️",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_header(
    title="ReCraft AI",
    subtitle="Turn trash into treasure — upload waste, get AI upcycling ideas, sell on the community marketplace.",
)

st.markdown("""
### 👈 Use the sidebar to navigate

| Page | What it does |
|------|-------------|
| 🛠️ **DIY Studio** | Upload a photo → AI identifies material → generates step-by-step upcycling project → price estimate |
| 🛍️ **Marketplace** | Browse & publish to the shared community marketplace |
""")

footer()
