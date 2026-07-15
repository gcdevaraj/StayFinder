"""
StayFinder – database.py
SQLite connection pool + schema bootstrap
"""

import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.getenv("DATABASE_PATH", "stayfinder.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # dict-like rows
    conn.execute("PRAGMA journal_mode=WAL") # concurrent reads
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db():
    """Context manager: yields a connection, commits on success, rolls back on error."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def row_to_dict(row):
    return dict(row) if row else None


def rows_to_list(rows):
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────
# Schema DDL
# ─────────────────────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    email        TEXT NOT NULL UNIQUE,
    phone        TEXT,
    password_hash TEXT NOT NULL,
    role         TEXT NOT NULL DEFAULT 'user',   -- user | owner | admin
    avatar       TEXT,
    verified     INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS properties (
    id               TEXT PRIMARY KEY,
    owner_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name             TEXT NOT NULL,
    type             TEXT NOT NULL,   -- PG | Private Hostel | Govt Hostel
    gender           TEXT NOT NULL,   -- Men | Women | Co-ed
    area             TEXT NOT NULL,
    address          TEXT NOT NULL,
    city             TEXT NOT NULL DEFAULT 'Bengaluru',
    lat              REAL,
    lng              REAL,
    description      TEXT NOT NULL,
    nearby_landmarks TEXT,
    price_min        INTEGER NOT NULL,
    price_max        INTEGER NOT NULL,
    deposit          INTEGER,
    verified         INTEGER NOT NULL DEFAULT 0,
    available        INTEGER NOT NULL DEFAULT 1,
    featured         INTEGER NOT NULL DEFAULT 0,
    total_rooms      INTEGER NOT NULL DEFAULT 1,
    avail_rooms      INTEGER NOT NULL DEFAULT 1,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_prop_area      ON properties(area);
CREATE INDEX IF NOT EXISTS idx_prop_type      ON properties(type);
CREATE INDEX IF NOT EXISTS idx_prop_city      ON properties(city);
CREATE INDEX IF NOT EXISTS idx_prop_available ON properties(available);
CREATE INDEX IF NOT EXISTS idx_prop_price_min ON properties(price_min);

CREATE TABLE IF NOT EXISTS rooms (
    id           TEXT PRIMARY KEY,
    property_id  TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    sharing_type TEXT NOT NULL,  -- Single | Double | Triple | Dorm
    price        INTEGER NOT NULL,
    available    INTEGER NOT NULL DEFAULT 1,
    count        INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS property_images (
    id          TEXT PRIMARY KEY,
    property_id TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    url         TEXT NOT NULL,
    caption     TEXT,
    is_primary  INTEGER NOT NULL DEFAULT 0,
    sort_order  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS amenities (
    id       TEXT PRIMARY KEY,
    name     TEXT NOT NULL UNIQUE,
    icon     TEXT NOT NULL,
    category TEXT NOT NULL  -- basic | comfort | security | food | transport
);

CREATE TABLE IF NOT EXISTS property_amenities (
    property_id TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    amenity_id  TEXT NOT NULL REFERENCES amenities(id),
    PRIMARY KEY (property_id, amenity_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id          TEXT PRIMARY KEY,
    property_id TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    user_id     TEXT NOT NULL REFERENCES users(id),
    rating      REAL NOT NULL CHECK(rating >= 1 AND rating <= 5),
    comment     TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS enquiries (
    id          TEXT PRIMARY KEY,
    property_id TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    user_id     TEXT NOT NULL REFERENCES users(id),
    message     TEXT NOT NULL,
    phone       TEXT,
    status      TEXT NOT NULL DEFAULT 'pending',  -- pending | replied | closed
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS saved_properties (
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    property_id TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    saved_at    TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, property_id)
);

CREATE TABLE IF NOT EXISTS govt_hostels (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    organisation TEXT NOT NULL,
    area         TEXT NOT NULL,
    city         TEXT NOT NULL DEFAULT 'Bengaluru',
    address      TEXT,
    lat          REAL,
    lng          REAL,
    eligibility  TEXT NOT NULL,  -- JSON array: '["SC/ST","Women"]'
    cost_type    TEXT NOT NULL,  -- Free | Subsidized | Paid
    cost_amount  TEXT,
    total_seats  INTEGER NOT NULL,
    avail_seats  INTEGER,
    contact      TEXT,
    apply_url    TEXT,
    description  TEXT NOT NULL,
    active       INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS area_guides (
    id               TEXT PRIMARY KEY,
    name             TEXT NOT NULL UNIQUE,
    city             TEXT NOT NULL DEFAULT 'Bengaluru',
    description      TEXT NOT NULL,
    tags             TEXT NOT NULL,  -- JSON
    safety_score     REAL NOT NULL,
    safety_label     TEXT NOT NULL,
    transit_score    REAL NOT NULL,
    transit_label    TEXT NOT NULL,
    avg_price_min    INTEGER NOT NULL,
    avg_price_max    INTEGER NOT NULL,
    emoji            TEXT NOT NULL,
    nearby_tech_parks TEXT,  -- JSON
    nearby_colleges   TEXT,  -- JSON
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token      TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def init_db():
    """Create all tables if they don't exist."""
    with db() as conn:
        conn.executescript(SCHEMA)
    print(f"[OK] Database initialised at {DB_PATH}")
