"""
Auth module — SQLite-backed user store for ReCraft AI.
Tokens remain in-memory (intentional: sessions reset on restart).
"""

from __future__ import annotations

import hashlib
import os
import uuid

try:
    from database import get_conn
except ImportError:
    from backend.database import get_conn

# In-memory only — tokens intentionally reset on restart
_tokens: dict[str, str] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    salt = os.getenv("SECRET_SALT", "recraft-ai-hackathon-2026")
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def _pick_avatar(username: str) -> str:
    avatars = ["🌱", "♻️", "🌿", "🍃", "🌊", "🌻", "🦋", "🐝", "🌍", "⚡"]
    return avatars[sum(ord(c) for c in username) % len(avatars)]


def _issue_token(username: str) -> str:
    token = str(uuid.uuid4())
    _tokens[token] = username
    return token


def _seed_test_user() -> None:
    with get_conn() as conn:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE username = ?", ("test",)
        ).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO users (username, email, password_hash, avatar_emoji) VALUES (?, ?, ?, ?)",
                ("test", "test@recraft.ai", _hash("test"), "🌱"),
            )


_seed_test_user()


# ── Public API ────────────────────────────────────────────────────────────────

def register(username: str, email: str, password: str) -> dict:
    username = username.strip().lower()
    if not username or not password:
        raise ValueError("Username and password are required.")

    with get_conn() as conn:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()
        if exists:
            raise ValueError("Username already taken.")

        conn.execute(
            "INSERT INTO users (username, email, password_hash, avatar_emoji) VALUES (?, ?, ?, ?)",
            (username, email.strip(), _hash(password), _pick_avatar(username)),
        )

    token = _issue_token(username)
    return {"token": token, "username": username}


def login(username: str, password: str) -> dict:
    username = username.strip().lower()

    with get_conn() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()

    if not row or row["password_hash"] != _hash(password):
        raise ValueError("Invalid username or password.")

    token = _issue_token(username)
    return {"token": token, "username": username}


def get_user_by_token(token: str) -> dict | None:
    username = _tokens.get(token)
    if not username:
        return None

    with get_conn() as conn:
        row = conn.execute(
            "SELECT username, email, avatar_emoji FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not row:
            return None
        saved_count = conn.execute(
            "SELECT COUNT(*) FROM saves WHERE username = ?", (username,)
        ).fetchone()[0]

    return {
        "username": row["username"],
        "email": row["email"],
        "avatar_emoji": row["avatar_emoji"],
        "saved_count": saved_count,
    }


def save_diy(token: str, item: dict) -> dict:
    import json
    username = _tokens.get(token)
    if not username:
        raise ValueError("Invalid or expired token.")

    saved_id = str(uuid.uuid4())
    item["saved_id"] = saved_id

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO saves (saved_id, username, item_json) VALUES (?, ?, ?)",
            (saved_id, username, json.dumps(item)),
        )

    return {"saved_id": saved_id}


def get_saves(token: str) -> list:
    import json
    username = _tokens.get(token)
    if not username:
        raise ValueError("Invalid or expired token.")

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT item_json FROM saves WHERE username = ? ORDER BY created_at DESC",
            (username,),
        ).fetchall()

    return [json.loads(r["item_json"]) for r in rows]


def delete_save(token: str, saved_id: str) -> bool:
    username = _tokens.get(token)
    if not username:
        raise ValueError("Invalid or expired token.")

    with get_conn() as conn:
        cursor = conn.execute(
            "DELETE FROM saves WHERE saved_id = ? AND username = ?",
            (saved_id, username),
        )

    return cursor.rowcount > 0
