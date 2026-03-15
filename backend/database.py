"""
SQLite database setup for ReCraft AI.
Single file DB — persists across restarts, zero config.
"""

from __future__ import annotations

import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "recraft.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables if they don't exist. Uses individual execute() calls
    to avoid executescript()'s implicit COMMIT interfering with table creation."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username      TEXT PRIMARY KEY,
                email         TEXT NOT NULL DEFAULT '',
                password_hash TEXT NOT NULL,
                avatar_emoji  TEXT NOT NULL DEFAULT '🌱'
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saves (
                saved_id   TEXT PRIMARY KEY,
                username   TEXT NOT NULL,
                item_json  TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS marketplace (
                id                    TEXT PRIMARY KEY,
                project_name          TEXT NOT NULL,
                material              TEXT NOT NULL,
                tagline               TEXT,
                price                 TEXT,
                recommended_price_usd REAL,
                steps_json            TEXT,
                image_url             TEXT,
                image_b64             TEXT,
                likes                 INTEGER DEFAULT 0
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id           TEXT PRIMARY KEY,
                username     TEXT NOT NULL,
                avatar_emoji TEXT NOT NULL DEFAULT '🌱',
                msg_type     TEXT NOT NULL DEFAULT 'text',
                content      TEXT,
                image_b64    TEXT,
                link_url     TEXT,
                reply_to_id  TEXT,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
        # Migrations — add columns that may be missing in older DB files
        try:
            conn.execute("ALTER TABLE marketplace ADD COLUMN image_b64 TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists
        conn.commit()
    finally:
        conn.close()


def seed_marketplace_if_empty() -> None:
    seed = [
        {
            "id": "seed-1",
            "project_name": "Denim Tote Bag",
            "material": "Old jeans",
            "tagline": "Sturdy zero-waste tote crafted from worn-out denim — built to last another decade",
            "price": "$22 – $35",
            "recommended_price_usd": 28,
            "steps": [
                "Cut both legs off at the crotch seam",
                "Turn inside out and sew the bottom opening shut",
                "Turn right side out — the waistband becomes the bag opening",
                "Cut two 60 cm strips from the leftover legs for straps",
                "Sew straps securely to inside of waistband",
                "Optional: add an interior pocket from the back pocket",
            ],
            "image_url": "https://images.unsplash.com/photo-1547949003-9792a18a2601?w=600&q=80",
            "likes": 42,
        },
        {
            "id": "seed-2",
            "project_name": "Wine Bottle Pendant Lamp",
            "material": "Glass wine bottle",
            "tagline": "Ambient pendant light from an empty wine bottle — zero waste, all atmosphere",
            "price": "$30 – $50",
            "recommended_price_usd": 40,
            "steps": [
                "Score the bottle 10 cm from the base with a glass cutter",
                "Alternate hot and ice-cold water over the score line until it cracks cleanly",
                "Sand the cut edge smooth with 120-grit wet-dry sandpaper",
                "Feed a pendant lamp cord kit through the bottle neck",
                "Install an Edison bulb — 4W LED recommended",
                "Hang and adjust cord length to taste",
            ],
            "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
            "likes": 58,
        },
        {
            "id": "seed-3",
            "project_name": "Pallet Wood Herb Garden",
            "material": "Wooden shipping pallet",
            "tagline": "Vertical herb garden from a single pallet — fresh basil all summer for free",
            "price": "$15 – $25",
            "recommended_price_usd": 20,
            "steps": [
                "Sand the pallet to remove splinters and rough edges",
                "Staple landscape fabric to the back, bottom, and sides",
                "Stand the pallet upright and fill gaps between slats with potting mix",
                "Plant herbs (basil, mint, thyme) into the pockets between slats",
                "Water thoroughly and lay flat for 2 weeks while roots establish",
                "Stand upright and hang on a sunny wall",
            ],
            "image_url": "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600&q=80",
            "likes": 75,
        },
        {
            "id": "seed-4",
            "project_name": "Mason Jar Desk Organiser",
            "material": "Glass mason jars",
            "tagline": "Rustic desk organiser with 3 jars mounted on reclaimed wood — clears your desk instantly",
            "price": "$18 – $28",
            "recommended_price_usd": 23,
            "steps": [
                "Cut a 30 cm length of reclaimed 2×4 timber",
                "Sand and optionally stain or paint the wood",
                "Use hose clamps to attach 3 jars to the board",
                "Pre-drill holes and screw the board to the wall",
                "Sort pens, scissors, and supplies into the jars",
            ],
            "image_url": "https://images.unsplash.com/photo-1544816155-12df9643f363?w=600&q=80",
            "likes": 34,
        },
    ]

    with get_conn() as conn:
        existing_ids = [r[0] for r in conn.execute("SELECT id FROM marketplace WHERE id LIKE 'seed-%'").fetchall()]
        for sid in existing_ids:
            conn.execute("DELETE FROM marketplace WHERE id = ?", (sid,))

        for item in seed:
            conn.execute(
                """INSERT INTO marketplace
                   (id, project_name, material, tagline, price, recommended_price_usd,
                    steps_json, image_url, image_b64, likes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    item["id"], item["project_name"], item["material"],
                    item["tagline"], item["price"], item["recommended_price_usd"],
                    json.dumps(item["steps"]), item["image_url"], None, item["likes"],
                ),
            )
