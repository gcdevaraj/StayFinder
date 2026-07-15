"""
StayFinder – middleware/auth.py
JWT authentication helpers and Flask decorators
"""

import os
import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify, g

from database import db, row_to_dict

JWT_SECRET          = os.getenv("JWT_SECRET", "dev_secret_change_me")
REFRESH_SECRET      = os.getenv("REFRESH_TOKEN_SECRET", "dev_refresh_change_me")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "15"))
REFRESH_EXPIRES_DAYS= int(os.getenv("REFRESH_EXPIRES_DAYS", "7"))


# ── Token creation ─────────────────────────────────────────────────

def create_access_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def create_refresh_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRES_DAYS),
        "type": "refresh",
    }
    return jwt.encode(payload, REFRESH_SECRET, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])


def decode_refresh_token(token: str) -> dict:
    return jwt.decode(token, REFRESH_SECRET, algorithms=["HS256"])


# ── Flask decorators ───────────────────────────────────────────────

def _load_user_from_token():
    """Extract and verify Bearer token; return user dict or None."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, None
    token = auth[7:]
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        return None, "TOKEN_EXPIRED"
    except jwt.InvalidTokenError:
        return None, "INVALID_TOKEN"

    with db() as conn:
        row = conn.execute(
            "SELECT id, name, email, role, verified FROM users WHERE id = ?",
            (payload["user_id"],),
        ).fetchone()
    return row_to_dict(row), None


def authenticate(f):
    """Require valid JWT. Sets g.user."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        user, err = _load_user_from_token()
        if err == "TOKEN_EXPIRED":
            return jsonify({"error": "Token expired", "code": "TOKEN_EXPIRED"}), 401
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        g.user = user
        return f(*args, **kwargs)
    return wrapper


def optional_auth(f):
    """Attach g.user if token present, continue regardless."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        user, _ = _load_user_from_token()
        g.user = user
        return f(*args, **kwargs)
    return wrapper


def require_role(*roles):
    """Require authenticated user to have one of the given roles."""
    def decorator(f):
        @wraps(f)
        @authenticate
        def wrapper(*args, **kwargs):
            if g.user["role"] not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


require_owner = require_role("owner", "admin")
require_admin = require_role("admin")
