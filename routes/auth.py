"""StayFinder – routes/auth.py"""

import uuid
import bcrypt
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, g

from database import db, row_to_dict
from middleware.auth import (
    authenticate, create_access_token, create_refresh_token,
    decode_refresh_token,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

SAFE_FIELDS = "id, name, email, phone, role, avatar, verified, created_at"


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(12)).decode()


def check_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def _save_refresh_token(conn, user_id: str, token: str):
    expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    conn.execute(
        "INSERT INTO refresh_tokens (id, user_id, token, expires_at) VALUES (?,?,?,?)",
        (str(uuid.uuid4()), user_id, token, expires_at),
    )


# ── POST /api/auth/register ────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name  = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")
    phone = data.get("phone")
    role  = data.get("role", "user")

    if not name or len(name) < 2:
        return jsonify({"error": "Name must be at least 2 characters"}), 422
    if "@" not in email:
        return jsonify({"error": "Valid email required"}), 422
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 422
    if role not in ("user", "owner"):
        role = "user"

    with db() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return jsonify({"error": "Email already registered"}), 409

        uid = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO users (id, name, email, phone, password_hash, role)
               VALUES (?,?,?,?,?,?)""",
            (uid, name, email, phone, hash_password(password), role),
        )
        user = row_to_dict(conn.execute(
            f"SELECT {SAFE_FIELDS} FROM users WHERE id = ?", (uid,)
        ).fetchone())

        access  = create_access_token(uid)
        refresh = create_refresh_token(uid)
        _save_refresh_token(conn, uid, refresh)

    return jsonify({"user": user, "accessToken": access, "refreshToken": refresh}), 201


# ── POST /api/auth/login ───────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data  = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not row or not check_password(password, row["password_hash"]):
            return jsonify({"error": "Invalid credentials"}), 401

        user = {k: row[k] for k in (SAFE_FIELDS.split(", "))}
        access  = create_access_token(row["id"])
        refresh = create_refresh_token(row["id"])
        _save_refresh_token(conn, row["id"], refresh)

    return jsonify({"user": user, "accessToken": access, "refreshToken": refresh})


# ── POST /api/auth/refresh ─────────────────────────────────────────
@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    data  = request.get_json() or {}
    token = data.get("refreshToken")
    if not token:
        return jsonify({"error": "Refresh token required"}), 401

    with db() as conn:
        stored = conn.execute(
            "SELECT * FROM refresh_tokens WHERE token = ?", (token,)
        ).fetchone()
        if not stored:
            return jsonify({"error": "Invalid refresh token"}), 401
        if stored["expires_at"] < datetime.now(timezone.utc).isoformat():
            return jsonify({"error": "Refresh token expired"}), 401

        try:
            payload = decode_refresh_token(token)
        except Exception:
            return jsonify({"error": "Invalid refresh token"}), 401

        # Rotate
        conn.execute("DELETE FROM refresh_tokens WHERE token = ?", (token,))
        new_refresh = create_refresh_token(payload["user_id"])
        _save_refresh_token(conn, payload["user_id"], new_refresh)
        new_access = create_access_token(payload["user_id"])

    return jsonify({"accessToken": new_access, "refreshToken": new_refresh})


# ── POST /api/auth/logout ──────────────────────────────────────────
@auth_bp.route("/logout", methods=["POST"])
@authenticate
def logout():
    data = request.get_json() or {}
    refresh_token = data.get("refreshToken")
    if refresh_token:
        with db() as conn:
            conn.execute(
                "DELETE FROM refresh_tokens WHERE token = ? AND user_id = ?",
                (refresh_token, g.user["id"]),
            )
    return jsonify({"message": "Logged out"})


# ── GET /api/auth/me ───────────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@authenticate
def me():
    with db() as conn:
        user = row_to_dict(conn.execute(
            f"SELECT {SAFE_FIELDS} FROM users WHERE id = ?", (g.user["id"],)
        ).fetchone())
    return jsonify(user)


# ── PATCH /api/auth/me ─────────────────────────────────────────────
@auth_bp.route("/me", methods=["PATCH"])
@authenticate
def update_me():
    data = request.get_json() or {}
    fields, vals = [], []
    for col in ("name", "phone", "avatar"):
        if col in data:
            fields.append(f"{col} = ?")
            vals.append(data[col])
    if not fields:
        return jsonify({"error": "No fields to update"}), 422

    vals.append(g.user["id"])
    with db() as conn:
        conn.execute(
            f"UPDATE users SET {', '.join(fields)}, updated_at = datetime('now') WHERE id = ?",
            vals,
        )
        user = row_to_dict(conn.execute(
            f"SELECT {SAFE_FIELDS} FROM users WHERE id = ?", (g.user["id"],)
        ).fetchone())
    return jsonify(user)


# ── POST /api/auth/change-password ────────────────────────────────
@auth_bp.route("/change-password", methods=["POST"])
@authenticate
def change_password():
    data = request.get_json() or {}
    current = data.get("currentPassword", "")
    new_pw  = data.get("newPassword", "")

    if len(new_pw) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 422

    with db() as conn:
        row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (g.user["id"],)).fetchone()
        if not check_password(current, row["password_hash"]):
            return jsonify({"error": "Current password is incorrect"}), 400

        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = datetime('now') WHERE id = ?",
            (hash_password(new_pw), g.user["id"]),
        )
        conn.execute("DELETE FROM refresh_tokens WHERE user_id = ?", (g.user["id"],))

    return jsonify({"message": "Password changed successfully"})
