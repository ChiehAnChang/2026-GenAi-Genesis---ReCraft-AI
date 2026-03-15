"""
Page 4 — Community Chat
Real-time community chat with image sharing, links, price queries, and replies.
"""

from __future__ import annotations
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
import streamlit as st
from utils import load_css, footer

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

load_css()

st.markdown('<h1 class="hero-title">💬 Community Chat</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Share ideas, ask prices, post photos — all things upcycling</p>', unsafe_allow_html=True)
st.divider()

token = st.session_state.get("auth_token")
username = st.session_state.get("auth_username", "")

# Which message has its inline reply box open (msg id or None)
if "reply_open_for" not in st.session_state:
    st.session_state.reply_open_for = None


def fetch_messages() -> list:
    try:
        resp = requests.get(f"{API_BASE}/api/chat", params={"limit": 60}, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def send_message(msg_type: str, content: str = None, image_b64: str = None,
                 link_url: str = None, reply_to_id: str = None) -> bool:
    try:
        resp = requests.post(f"{API_BASE}/api/chat", json={
            "token": token,
            "msg_type": msg_type,
            "content": content,
            "image_b64": image_b64,
            "link_url": link_url,
            "reply_to_id": reply_to_id,
        }, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to send: {e}")
        return False


def render_message(msg: dict) -> None:
    is_mine = msg["username"] == username
    avatar = msg.get("avatar_emoji", "♻️")
    name = msg["username"]
    ts = msg.get("created_at", "")[:16].replace("T", " ")
    msg_id = msg["id"]

    with st.container():
        col_avatar, col_body = st.columns([1, 11])

        with col_avatar:
            st.markdown(
                f"<div style='font-size:2rem;text-align:center'>{avatar}</div>",
                unsafe_allow_html=True,
            )

        with col_body:
            name_color = "#16a34a" if is_mine else "#6b7280"
            st.markdown(
                f"<span style='font-weight:700;color:{name_color}'>{name}</span>"
                f"<span style='font-size:0.75rem;color:#9ca3af;margin-left:0.5rem'>{ts}</span>",
                unsafe_allow_html=True,
            )

            # Reply preview
            if msg.get("reply_preview"):
                rp = msg["reply_preview"]
                preview_text = rp.get("content") or f"[{rp['msg_type']}]"
                st.markdown(
                    f"<div style='border-left:3px solid #22c55e;padding:0.2rem 0.6rem;"
                    f"margin-bottom:0.3rem;font-size:0.8rem;color:#6b7280;"
                    f"background:#f0fdf4;border-radius:4px'>"
                    f"↩ <b>{rp['username']}</b>: {preview_text}</div>",
                    unsafe_allow_html=True,
                )

            # Content
            mtype = msg.get("msg_type", "text")
            if mtype == "text":
                st.markdown(msg.get("content", ""))
            elif mtype == "price_ask":
                st.markdown(
                    f"<div style='background:#fef9c3;border:1px solid #fde047;"
                    f"border-radius:8px;padding:0.5rem 0.8rem;color:#713f12'>"
                    f"💰 <b>Price check:</b> {msg.get('content', '')}</div>",
                    unsafe_allow_html=True,
                )
            elif mtype == "image":
                if msg.get("image_b64"):
                    st.image(base64.b64decode(msg["image_b64"]), use_container_width=True)
                if msg.get("content"):
                    st.caption(msg["content"])
            elif mtype == "link":
                url = msg.get("link_url", "")
                caption = msg.get("content") or url
                st.markdown(
                    f"<div style='background:#eff6ff;border:1px solid #bfdbfe;"
                    f"border-radius:8px;padding:0.5rem 0.8rem;color:#1e40af'>"
                    f"🔗 <a href='{url}' target='_blank'>{caption}</a></div>",
                    unsafe_allow_html=True,
                )

            # Reply button (toggle inline box)
            if token:
                is_open = st.session_state.reply_open_for == msg_id
                btn_label = "✕ Cancel" if is_open else "↩ Reply"
                if st.button(btn_label, key=f"reply_btn_{msg_id}", use_container_width=False):
                    st.session_state.reply_open_for = None if is_open else msg_id
                    st.rerun()

            # ── Inline reply box ─────────────────────────────────────────────
            if token and st.session_state.reply_open_for == msg_id:
                with st.container():
                    st.markdown(
                        f"<div style='font-size:0.8rem;color:#6b7280;margin-bottom:0.2rem'>"
                        f"↩ Replying to <b>{name}</b></div>",
                        unsafe_allow_html=True,
                    )
                    reply_text = st.text_area(
                        "Reply",
                        placeholder="Type your reply…",
                        height=70,
                        label_visibility="collapsed",
                        key=f"reply_input_{msg_id}",
                    )
                    if st.button("Send Reply 💬", type="primary",
                                 key=f"reply_send_{msg_id}", use_container_width=False):
                        if reply_text.strip():
                            if send_message("text", content=reply_text.strip(), reply_to_id=msg_id):
                                st.session_state.reply_open_for = None
                                st.session_state.chat_messages = fetch_messages()
                                st.rerun()

        st.markdown("<hr style='margin:0.3rem 0;opacity:0.15'>", unsafe_allow_html=True)


# ── Message feed ───────────────────────────────────────────────────────────────
ref_col, count_col = st.columns([1, 5])
with ref_col:
    if st.button("🔄 Refresh", use_container_width=True):
        st.session_state.chat_messages = fetch_messages()
        st.rerun()
with count_col:
    count = len(st.session_state.get("chat_messages", []))
    st.caption(f"{count} messages")

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = fetch_messages()

messages = st.session_state.chat_messages

if not messages:
    st.info("No messages yet — be the first to say something! 👋")
for msg in messages:
    render_message(msg)

# ── Input area (new messages only, no reply context needed) ────────────────────
st.divider()

if not token:
    st.warning("🔑 Log in to send messages.")
    st.page_link("pages/0_Login.py", label="Go to Login →", icon="🔑")
else:
    tab_text, tab_price, tab_image, tab_link = st.tabs(["💬 Text", "💰 Price Ask", "🖼️ Image", "🔗 Link"])

    with tab_text:
        text_input = st.text_area("Message", placeholder="Share an idea, tip, or question…",
                                  height=80, label_visibility="collapsed")
        if st.button("Send 💬", type="primary", use_container_width=True, key="send_text"):
            if text_input.strip():
                if send_message("text", content=text_input.strip()):
                    st.session_state.chat_messages = fetch_messages()
                    st.rerun()

    with tab_price:
        price_input = st.text_input("What item?",
                                    placeholder="e.g. Denim tote bag made from old jeans, good condition",
                                    label_visibility="collapsed")
        if st.button("Ask Price 💰", type="primary", use_container_width=True, key="send_price"):
            if price_input.strip():
                if send_message("price_ask", content=price_input.strip()):
                    st.session_state.chat_messages = fetch_messages()
                    st.rerun()

    with tab_image:
        uploaded = st.file_uploader("Upload image", type=["jpg", "jpeg", "png", "webp"],
                                    label_visibility="collapsed")
        img_caption = st.text_input("Caption (optional)", key="img_caption")
        if st.button("Share Image 🖼️", type="primary", use_container_width=True, key="send_image"):
            if uploaded:
                img_b64 = base64.b64encode(uploaded.read()).decode()
                if send_message("image", content=img_caption or None, image_b64=img_b64):
                    st.session_state.chat_messages = fetch_messages()
                    st.rerun()
            else:
                st.warning("Please upload an image first.")

    with tab_link:
        link_url = st.text_input("URL", placeholder="https://…", label_visibility="collapsed")
        link_caption = st.text_input("Description (optional)", key="link_caption")
        if st.button("Share Link 🔗", type="primary", use_container_width=True, key="send_link"):
            if link_url.strip():
                if send_message("link", content=link_caption or None, link_url=link_url.strip()):
                    st.session_state.chat_messages = fetch_messages()
                    st.rerun()
            else:
                st.warning("Please enter a URL.")

footer()
