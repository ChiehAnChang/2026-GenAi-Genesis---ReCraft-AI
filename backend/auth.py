"""
Auth module — in-memory user store for hackathon.
Production would swap this for a real DB + proper JWT.
"""

import uuid
import hashlib
import os

# In-memory stores (resets on restart — fine for hackathon demo)
_users: dict[str, dict] = {}       # username → {password_hash, email, created_at}
_tokens: dict[str, str] = {}       # token → username
_saves: dict[str, list] = {}       # username → [saved_items]


def _seed_test_user() -> None:
    """Pre-create test/test account so demo works without registration."""
    _users["test"] = {
        "username": "test",
        "email": "test@recraft.ai",
        "password_hash": _hash("test"),
        "avatar_emoji": "🌱",
    }
    _saves["test"] = []


def _hash(password: str) -> str:
    salt = os.getenv("SECRET_SALT", "recraft-ai-hackathon-2026")
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


# Run seed immediately on import
_seed_test_user()


def register(username: str, email: str, password: str) -> dict:
    """Create a new user. Returns token on success, raises ValueError on conflict."""
    username = username.strip().lower()
    if not username or not password:
        raise ValueError("Username and password are required.")
    if username in _users:
        raise ValueError("Username already taken.")
    _users[username] = {
        "username": username,
        "email": email.strip(),
        "password_hash": _hash(password),
        "avatar_emoji": _pick_avatar(username),
    }
    _saves[username] = []
    token = _issue_token(username)
    return {"token": token, "username": username}


def login(username: str, password: str) -> dict:
    """Verify credentials and return token. Raises ValueError on bad creds."""
    username = username.strip().lower()
    user = _users.get(username)
    if not user or user["password_hash"] != _hash(password):
        raise ValueError("Invalid username or password.")
    token = _issue_token(username)
    return {"token": token, "username": username}


def get_user_by_token(token: str) -> dict | None:
    """Return user dict or None if token is invalid."""
    username = _tokens.get(token)
    if not username:
        return None
    user = _users.get(username, {}).copy()
    user.pop("password_hash", None)
    user["saved_count"] = len(_saves.get(username, []))
    return user


def save_diy(token: str, item: dict) -> dict:
    """Save a DIY item to the authenticated user's collection."""
    username = _tokens.get(token)
    if not username:
        raise ValueError("Invalid or expired token.")
    item["saved_id"] = str(uuid.uuid4())
    _saves.setdefault(username, []).insert(0, item)
    return {"saved_id": item["saved_id"]}


def get_saves(token: str) -> list:
    """Return all saved items for the authenticated user."""
    username = _tokens.get(token)
    if not username:
        raise ValueError("Invalid or expired token.")
    return _saves.get(username, [])


def delete_save(token: str, saved_id: str) -> bool:
    """Delete a saved item. Returns True if deleted."""
    username = _tokens.get(token)
    if not username:
        raise ValueError("Invalid or expired token.")
    items = _saves.get(username, [])
    original_len = len(items)
    _saves[username] = [i for i in items if i.get("saved_id") != saved_id]
    return len(_saves[username]) < original_len


def _issue_token(username: str) -> str:
    token = str(uuid.uuid4())
    _tokens[token] = username
    return token


def _pick_avatar(username: str) -> str:
    avatars = ["🌱", "♻️", "🌿", "🍃", "🌊", "🌻", "🦋", "🐝", "🌍", "⚡"]
    return avatars[sum(ord(c) for c in username) % len(avatars)]
