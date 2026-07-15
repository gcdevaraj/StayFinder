"""StayFinder – routes/properties.py"""

import uuid, json
from flask import Blueprint, request, jsonify, g

from database import db, row_to_dict, rows_to_list
from middleware.auth import authenticate, optional_auth

props_bp = Blueprint("properties", __name__, url_prefix="/api/properties")


def _enrich(prop: dict, conn, user_id=None) -> dict:
    """Add amenities, rooms, reviews summary, images, owner to a property dict."""
    pid = prop["id"]

    # amenities
    prop["amenities"] = rows_to_list(conn.execute(
        """SELECT a.id, a.name, a.icon, a.category
           FROM property_amenities pa JOIN amenities a ON a.id = pa.amenity_id
           WHERE pa.property_id = ?""", (pid,)
    ).fetchall())

    # rooms
    prop["rooms"] = rows_to_list(conn.execute(
        "SELECT * FROM rooms WHERE property_id = ?", (pid,)
    ).fetchall())

    # images
    prop["images"] = rows_to_list(conn.execute(
        "SELECT * FROM property_images WHERE property_id = ? ORDER BY sort_order",
        (pid,)
    ).fetchall())

    # reviews summary
    rev = conn.execute(
        "SELECT AVG(rating) as avg, COUNT(*) as cnt FROM reviews WHERE property_id = ?",
        (pid,)
    ).fetchone()
    prop["avg_rating"]   = round(rev["avg"], 1) if rev["avg"] else None
    prop["review_count"] = rev["cnt"]

    # owner
    owner = conn.execute(
        "SELECT id, name, phone, avatar, verified FROM users WHERE id = ?",
        (prop["owner_id"],)
    ).fetchone()
    prop["owner"] = row_to_dict(owner)

    # saved?
    if user_id:
        saved = conn.execute(
            "SELECT 1 FROM saved_properties WHERE user_id=? AND property_id=?",
            (user_id, pid)
        ).fetchone()
        prop["is_saved"] = bool(saved)
    else:
        prop["is_saved"] = False

    return prop


# ── GET /api/properties ────────────────────────────────────────────
@props_bp.route("/", methods=["GET"])
@optional_auth
def list_properties():
    p = request.args
    prop_type = p.get("type")
    gender    = p.get("gender")
    area      = p.get("area")
    city      = p.get("city")
    price_min = p.get("priceMin", type=int)
    price_max = p.get("priceMax", type=int)
    amenities = p.get("amenities")        # comma-separated names
    available = p.get("available")
    search    = p.get("search")
    sort_by   = p.get("sortBy", "rating")
    page      = max(1, p.get("page", 1, type=int))
    limit     = min(50, p.get("limit", 12, type=int))
    offset    = (page - 1) * limit

    where, args = ["1=1"], []

    if prop_type:
        where.append("type = ?"); args.append(prop_type)
    if gender and gender != "All":
        where.append("(gender = ? OR gender = 'Co-ed')"); args.append(gender)
    if area:
        where.append("area LIKE ?"); args.append(f"%{area}%")
    if city:
        where.append("city LIKE ?"); args.append(f"%{city}%")
    if price_min is not None:
        where.append("price_min >= ?"); args.append(price_min)
    if price_max is not None:
        where.append("price_max <= ?"); args.append(price_max)
    if available is not None:
        where.append("available = ?"); args.append(1 if available == "true" else 0)
    if search:
        where.append("(name LIKE ? OR area LIKE ? OR description LIKE ? OR address LIKE ?)")
        args += [f"%{search}%"] * 4

    # Amenity filter: property must have ALL listed amenities
    if amenities:
        names = [n.strip() for n in amenities.split(",")]
        for n in names:
            where.append("""id IN (
                SELECT pa.property_id FROM property_amenities pa
                JOIN amenities a ON a.id = pa.amenity_id
                WHERE a.name = ?)""")
            args.append(n)

    order_map = {
        "price-asc":  "price_min ASC",
        "price-desc": "price_min DESC",
        "newest":     "created_at DESC",
        "rating":     "featured DESC, created_at DESC",
    }
    order = order_map.get(sort_by, "featured DESC, created_at DESC")
    where_clause = " AND ".join(where)

    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM properties WHERE {where_clause}", args
        ).fetchone()[0]

        rows = conn.execute(
            f"SELECT * FROM properties WHERE {where_clause} ORDER BY {order} LIMIT ? OFFSET ?",
            args + [limit, offset]
        ).fetchall()

        user_id = g.user["id"] if g.user else None
        results = [_enrich(dict(r), conn, user_id) for r in rows]

    return jsonify({
        "data": results,
        "meta": {"total": total, "page": page, "limit": limit, "totalPages": -(-total // limit)},
    })


# ── GET /api/properties/saved ──────────────────────────────────────
@props_bp.route("/saved", methods=["GET"])
@authenticate
def saved_list():
    with db() as conn:
        rows = conn.execute(
            """SELECT p.*, sp.saved_at FROM properties p
               JOIN saved_properties sp ON sp.property_id = p.id
               WHERE sp.user_id = ? ORDER BY sp.saved_at DESC""",
            (g.user["id"],)
        ).fetchall()
        results = [_enrich(dict(r), conn, g.user["id"]) for r in rows]
    return jsonify(results)


# ── GET /api/properties/owner/mine ────────────────────────────────
@props_bp.route("/owner/mine", methods=["GET"])
@authenticate
def owner_listings():
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM properties WHERE owner_id = ? ORDER BY created_at DESC",
            (g.user["id"],)
        ).fetchall()
        results = [_enrich(dict(r), conn) for r in rows]
    return jsonify(results)


# ── GET /api/properties/:id ────────────────────────────────────────
@props_bp.route("/<pid>", methods=["GET"])
@optional_auth
def get_property(pid):
    with db() as conn:
        row = conn.execute("SELECT * FROM properties WHERE id = ?", (pid,)).fetchone()
        if not row:
            return jsonify({"error": "Property not found"}), 404

        prop = _enrich(dict(row), conn, g.user["id"] if g.user else None)

        # Full reviews with user info
        reviews = rows_to_list(conn.execute(
            """SELECT r.*, u.name as user_name, u.avatar as user_avatar
               FROM reviews r JOIN users u ON u.id = r.user_id
               WHERE r.property_id = ? ORDER BY r.created_at DESC""",
            (pid,)
        ).fetchall())
        prop["reviews"] = reviews

    return jsonify(prop)


# ── POST /api/properties ───────────────────────────────────────────
@props_bp.route("/", methods=["POST"])
@authenticate
def create_property():
    if g.user["role"] not in ("owner", "admin"):
        return jsonify({"error": "Only owners can create properties"}), 403

    data = request.get_json() or {}
    required = ["name", "type", "gender", "area", "address", "description", "priceMin", "priceMax"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"Field '{f}' is required"}), 422

    pid = str(uuid.uuid4())
    with db() as conn:
        conn.execute(
            """INSERT INTO properties
               (id, owner_id, name, type, gender, area, address, city,
                lat, lng, description, nearby_landmarks,
                price_min, price_max, deposit, total_rooms, avail_rooms)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                pid, g.user["id"],
                data["name"], data["type"], data["gender"],
                data["area"], data["address"],
                data.get("city", "Bengaluru"),
                data.get("lat"), data.get("lng"),
                data["description"], data.get("nearbyLandmarks"),
                int(data["priceMin"]), int(data["priceMax"]),
                int(data["deposit"]) if data.get("deposit") else None,
                int(data.get("totalRooms", 1)),
                int(data.get("totalRooms", 1)),
            ),
        )

        # Amenities
        for aid in data.get("amenityIds", []):
            conn.execute(
                "INSERT OR IGNORE INTO property_amenities (property_id, amenity_id) VALUES (?,?)",
                (pid, aid),
            )

        # Rooms
        for r in data.get("rooms", []):
            conn.execute(
                "INSERT INTO rooms (id, property_id, sharing_type, price, count) VALUES (?,?,?,?,?)",
                (str(uuid.uuid4()), pid, r["sharingType"], int(r["price"]), int(r.get("count", 1))),
            )

        prop = _enrich(
            dict(conn.execute("SELECT * FROM properties WHERE id = ?", (pid,)).fetchone()),
            conn
        )

    return jsonify(prop), 201


# ── PATCH /api/properties/:id ──────────────────────────────────────
@props_bp.route("/<pid>", methods=["PATCH"])
@authenticate
def update_property(pid):
    with db() as conn:
        row = conn.execute("SELECT * FROM properties WHERE id = ?", (pid,)).fetchone()
        if not row:
            return jsonify({"error": "Property not found"}), 404
        if row["owner_id"] != g.user["id"] and g.user["role"] != "admin":
            return jsonify({"error": "Not authorized"}), 403

        data = request.get_json() or {}
        col_map = {
            "name": "name", "type": "type", "gender": "gender",
            "area": "area", "address": "address", "city": "city",
            "description": "description", "nearbyLandmarks": "nearby_landmarks",
            "priceMin": "price_min", "priceMax": "price_max", "deposit": "deposit",
            "available": "available", "totalRooms": "total_rooms",
            "availRooms": "avail_rooms", "lat": "lat", "lng": "lng",
        }
        fields, vals = [], []
        for key, col in col_map.items():
            if key in data:
                fields.append(f"{col} = ?")
                vals.append(data[key])

        if fields:
            vals.append(pid)
            conn.execute(
                f"UPDATE properties SET {', '.join(fields)}, updated_at=datetime('now') WHERE id=?",
                vals,
            )

        prop = _enrich(
            dict(conn.execute("SELECT * FROM properties WHERE id=?", (pid,)).fetchone()),
            conn
        )
    return jsonify(prop)


# ── DELETE /api/properties/:id ─────────────────────────────────────
@props_bp.route("/<pid>", methods=["DELETE"])
@authenticate
def delete_property(pid):
    with db() as conn:
        row = conn.execute("SELECT owner_id FROM properties WHERE id = ?", (pid,)).fetchone()
        if not row:
            return jsonify({"error": "Property not found"}), 404
        if row["owner_id"] != g.user["id"] and g.user["role"] != "admin":
            return jsonify({"error": "Not authorized"}), 403
        conn.execute("DELETE FROM properties WHERE id = ?", (pid,))
    return jsonify({"message": "Property deleted"})


# ── POST /api/properties/:id/save  &  DELETE ──────────────────────
@props_bp.route("/<pid>/save", methods=["POST"])
@authenticate
def save_property(pid):
    with db() as conn:
        if not conn.execute("SELECT id FROM properties WHERE id=?", (pid,)).fetchone():
            return jsonify({"error": "Property not found"}), 404
        conn.execute(
            "INSERT OR IGNORE INTO saved_properties (user_id, property_id) VALUES (?,?)",
            (g.user["id"], pid),
        )
    return jsonify({"saved": True})


@props_bp.route("/<pid>/save", methods=["DELETE"])
@authenticate
def unsave_property(pid):
    with db() as conn:
        conn.execute(
            "DELETE FROM saved_properties WHERE user_id=? AND property_id=?",
            (g.user["id"], pid),
        )
    return jsonify({"saved": False})
