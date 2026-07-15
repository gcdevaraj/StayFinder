"""StayFinder – routes/other.py  (reviews · enquiries · govt · areas · amenities · admin)"""

import uuid, json
from flask import Blueprint, request, jsonify, g

from database import db, row_to_dict, rows_to_list
from middleware.auth import authenticate, optional_auth, require_admin


# ══════════════════════════════════════════════════════════════════
#  REVIEWS  /api/properties/<pid>/reviews
# ══════════════════════════════════════════════════════════════════
reviews_bp = Blueprint("reviews", __name__)


@reviews_bp.route("/api/properties/<pid>/reviews", methods=["GET"])
def get_reviews(pid):
    with db() as conn:
        rows = rows_to_list(conn.execute(
            """SELECT r.*, u.name as user_name, u.avatar as user_avatar
               FROM reviews r JOIN users u ON u.id = r.user_id
               WHERE r.property_id = ? ORDER BY r.created_at DESC""",
            (pid,)
        ).fetchall())
        avg = conn.execute(
            "SELECT AVG(rating) as a, COUNT(*) as c FROM reviews WHERE property_id=?", (pid,)
        ).fetchone()
    return jsonify({
        "reviews": rows,
        "avg_rating": round(avg["a"], 1) if avg["a"] else None,
        "total": avg["c"],
    })


@reviews_bp.route("/api/properties/<pid>/reviews", methods=["POST"])
@authenticate
def post_review(pid):
    data = request.get_json() or {}
    rating  = data.get("rating")
    comment = (data.get("comment") or "").strip()

    if not rating or not (1 <= float(rating) <= 5):
        return jsonify({"error": "Rating must be 1–5"}), 422
    if len(comment) < 10:
        return jsonify({"error": "Comment must be at least 10 characters"}), 422

    with db() as conn:
        if not conn.execute("SELECT id FROM properties WHERE id=?", (pid,)).fetchone():
            return jsonify({"error": "Property not found"}), 404
        existing = conn.execute(
            "SELECT id FROM reviews WHERE property_id=? AND user_id=?",
            (pid, g.user["id"])
        ).fetchone()
        if existing:
            return jsonify({"error": "You have already reviewed this property"}), 409

        rid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO reviews (id, property_id, user_id, rating, comment) VALUES (?,?,?,?,?)",
            (rid, pid, g.user["id"], float(rating), comment),
        )
        review = row_to_dict(conn.execute(
            """SELECT r.*, u.name as user_name FROM reviews r
               JOIN users u ON u.id=r.user_id WHERE r.id=?""", (rid,)
        ).fetchone())
    return jsonify(review), 201


@reviews_bp.route("/api/properties/<pid>/reviews/<rid>", methods=["DELETE"])
@authenticate
def delete_review(pid, rid):
    with db() as conn:
        row = conn.execute("SELECT user_id FROM reviews WHERE id=?", (rid,)).fetchone()
        if not row:
            return jsonify({"error": "Review not found"}), 404
        if row["user_id"] != g.user["id"] and g.user["role"] != "admin":
            return jsonify({"error": "Not authorized"}), 403
        conn.execute("DELETE FROM reviews WHERE id=?", (rid,))
    return jsonify({"message": "Review deleted"})


# ══════════════════════════════════════════════════════════════════
#  ENQUIRIES
# ══════════════════════════════════════════════════════════════════
enquiries_bp = Blueprint("enquiries", __name__)


@enquiries_bp.route("/api/properties/<pid>/enquiries", methods=["POST"])
@authenticate
def create_enquiry(pid):
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    if len(message) < 5:
        return jsonify({"error": "Message too short"}), 422

    with db() as conn:
        if not conn.execute("SELECT id FROM properties WHERE id=?", (pid,)).fetchone():
            return jsonify({"error": "Property not found"}), 404
        eid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO enquiries (id, property_id, user_id, message, phone) VALUES (?,?,?,?,?)",
            (eid, pid, g.user["id"], message, data.get("phone")),
        )
        enq = row_to_dict(conn.execute("SELECT * FROM enquiries WHERE id=?", (eid,)).fetchone())
    return jsonify(enq), 201


@enquiries_bp.route("/api/enquiries/mine", methods=["GET"])
@authenticate
def my_enquiries():
    with db() as conn:
        rows = rows_to_list(conn.execute(
            """SELECT e.*, p.name as property_name, p.area, p.type
               FROM enquiries e JOIN properties p ON p.id=e.property_id
               WHERE e.user_id=? ORDER BY e.created_at DESC""",
            (g.user["id"],)
        ).fetchall())
    return jsonify(rows)


@enquiries_bp.route("/api/enquiries/received", methods=["GET"])
@authenticate
def received_enquiries():
    with db() as conn:
        rows = rows_to_list(conn.execute(
            """SELECT e.*, p.name as property_name, p.area,
                      u.name as user_name, u.email as user_email, u.phone as user_phone
               FROM enquiries e
               JOIN properties p ON p.id=e.property_id
               JOIN users u ON u.id=e.user_id
               WHERE p.owner_id=? ORDER BY e.created_at DESC""",
            (g.user["id"],)
        ).fetchall())
    return jsonify(rows)


@enquiries_bp.route("/api/enquiries/<eid>/status", methods=["PATCH"])
@authenticate
def update_enquiry_status(eid):
    data   = request.get_json() or {}
    status = data.get("status")
    if status not in ("pending", "replied", "closed"):
        return jsonify({"error": "Invalid status"}), 400

    with db() as conn:
        row = conn.execute(
            "SELECT e.*, p.owner_id FROM enquiries e JOIN properties p ON p.id=e.property_id WHERE e.id=?",
            (eid,)
        ).fetchone()
        if not row:
            return jsonify({"error": "Enquiry not found"}), 404
        if row["owner_id"] != g.user["id"] and g.user["role"] != "admin":
            return jsonify({"error": "Not authorized"}), 403
        conn.execute("UPDATE enquiries SET status=? WHERE id=?", (status, eid))
    return jsonify({"id": eid, "status": status})


# ══════════════════════════════════════════════════════════════════
#  GOVT HOSTELS   /api/govt-hostels
# ══════════════════════════════════════════════════════════════════
govt_bp = Blueprint("govt", __name__, url_prefix="/api/govt-hostels")


def _parse_hostel(h: dict) -> dict:
    try:
        h["eligibility"] = json.loads(h["eligibility"])
    except Exception:
        h["eligibility"] = [h.get("eligibility", "")]
    return h


@govt_bp.route("/", methods=["GET"])
def list_govt():
    p           = request.args
    eligibility = p.get("eligibility")
    city        = p.get("city")
    cost_type   = p.get("costType")
    search      = p.get("search")

    where, args = ["active = 1"], []
    if city:      where.append("city LIKE ?");        args.append(f"%{city}%")
    if cost_type: where.append("cost_type = ?");      args.append(cost_type)
    if search:
        where.append("(name LIKE ? OR organisation LIKE ? OR area LIKE ?)")
        args += [f"%{search}%"] * 3

    with db() as conn:
        rows = rows_to_list(conn.execute(
            f"SELECT * FROM govt_hostels WHERE {' AND '.join(where)} ORDER BY name",
            args
        ).fetchall())

    hostels = [_parse_hostel(r) for r in rows]

    if eligibility and eligibility != "All":
        hostels = [h for h in hostels if eligibility in (h["eligibility"] or [])]

    return jsonify({"data": hostels, "total": len(hostels)})


@govt_bp.route("/<hid>", methods=["GET"])
def get_govt(hid):
    with db() as conn:
        row = conn.execute("SELECT * FROM govt_hostels WHERE id=?", (hid,)).fetchone()
        if not row:
            return jsonify({"error": "Hostel not found"}), 404
    return jsonify(_parse_hostel(dict(row)))


@govt_bp.route("/", methods=["POST"])
@require_admin
def create_govt():
    data = request.get_json() or {}
    required = ["name", "organisation", "area", "eligibility", "costType", "totalSeats", "description"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"Field '{f}' is required"}), 422

    hid = str(uuid.uuid4())
    with db() as conn:
        conn.execute(
            """INSERT INTO govt_hostels
               (id, name, organisation, area, city, address, lat, lng,
                eligibility, cost_type, cost_amount, total_seats, avail_seats,
                contact, apply_url, description)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                hid, data["name"], data["organisation"], data["area"],
                data.get("city", "Bengaluru"), data.get("address"),
                data.get("lat"), data.get("lng"),
                json.dumps(data["eligibility"]),
                data["costType"], data.get("costAmount"),
                int(data["totalSeats"]),
                int(data["availSeats"]) if data.get("availSeats") else None,
                data.get("contact"), data.get("applyUrl"), data["description"],
            )
        )
        hostel = _parse_hostel(dict(
            conn.execute("SELECT * FROM govt_hostels WHERE id=?", (hid,)).fetchone()
        ))
    return jsonify(hostel), 201


@govt_bp.route("/<hid>", methods=["DELETE"])
@require_admin
def deactivate_govt(hid):
    with db() as conn:
        conn.execute("UPDATE govt_hostels SET active=0 WHERE id=?", (hid,))
    return jsonify({"message": "Hostel deactivated"})


# ══════════════════════════════════════════════════════════════════
#  AREA GUIDES   /api/areas
# ══════════════════════════════════════════════════════════════════
areas_bp = Blueprint("areas", __name__, url_prefix="/api/areas")


def _parse_area(a: dict) -> dict:
    for col in ("tags", "nearby_tech_parks", "nearby_colleges"):
        try:
            a[col] = json.loads(a[col] or "[]")
        except Exception:
            a[col] = []
    return a


@areas_bp.route("/", methods=["GET"])
def list_areas():
    p      = request.args
    city   = p.get("city")
    search = p.get("search")
    where, args = ["1=1"], []
    if city:   where.append("city LIKE ?");  args.append(f"%{city}%")
    if search: where.append("name LIKE ?");  args.append(f"%{search}%")

    with db() as conn:
        rows = rows_to_list(conn.execute(
            f"SELECT * FROM area_guides WHERE {' AND '.join(where)} ORDER BY name", args
        ).fetchall())
    return jsonify({"data": [_parse_area(r) for r in rows], "total": len(rows)})


@areas_bp.route("/<name>", methods=["GET"])
def get_area(name):
    with db() as conn:
        row = conn.execute("SELECT * FROM area_guides WHERE name LIKE ?", (f"%{name}%",)).fetchone()
        if not row:
            return jsonify({"error": "Area not found"}), 404
        area = _parse_area(dict(row))

        stats = conn.execute(
            """SELECT COUNT(*) as cnt,
                      AVG(price_min) as avg_price,
                      MIN(price_min) as min_price,
                      MAX(price_max) as max_price
               FROM properties WHERE area LIKE ? AND available=1""",
            (f"%{name}%",)
        ).fetchone()
        area["live_stats"] = {
            "total_listings": stats["cnt"],
            "avg_price": round(stats["avg_price"]) if stats["avg_price"] else None,
            "min_price": stats["min_price"],
            "max_price": stats["max_price"],
        }
    return jsonify(area)


@areas_bp.route("/", methods=["POST"])
@require_admin
def create_area():
    data = request.get_json() or {}
    aid  = str(uuid.uuid4())
    with db() as conn:
        conn.execute(
            """INSERT INTO area_guides
               (id, name, city, description, tags, safety_score, safety_label,
                transit_score, transit_label, avg_price_min, avg_price_max,
                emoji, nearby_tech_parks, nearby_colleges)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                aid, data["name"], data.get("city", "Bengaluru"),
                data["description"],
                json.dumps(data.get("tags", [])),
                float(data["safetyScore"]), data.get("safetyLabel", ""),
                float(data["transitScore"]), data.get("transitLabel", ""),
                int(data["avgPriceMin"]), int(data["avgPriceMax"]),
                data.get("emoji", "📍"),
                json.dumps(data.get("nearbyTechParks", [])),
                json.dumps(data.get("nearbyColleges", [])),
            )
        )
        area = _parse_area(dict(
            conn.execute("SELECT * FROM area_guides WHERE id=?", (aid,)).fetchone()
        ))
    return jsonify(area), 201


# ══════════════════════════════════════════════════════════════════
#  AMENITIES   /api/amenities
# ══════════════════════════════════════════════════════════════════
amenities_bp = Blueprint("amenities", __name__, url_prefix="/api/amenities")


@amenities_bp.route("/", methods=["GET"])
def list_amenities():
    cat = request.args.get("category")
    with db() as conn:
        if cat:
            rows = rows_to_list(conn.execute(
                "SELECT * FROM amenities WHERE category=? ORDER BY name", (cat,)
            ).fetchall())
        else:
            rows = rows_to_list(conn.execute(
                "SELECT * FROM amenities ORDER BY category, name"
            ).fetchall())
    return jsonify(rows)


@amenities_bp.route("/", methods=["POST"])
@require_admin
def create_amenity():
    data = request.get_json() or {}
    for f in ("name", "icon", "category"):
        if not data.get(f):
            return jsonify({"error": f"Field '{f}' is required"}), 422

    aid = str(uuid.uuid4())
    with db() as conn:
        conn.execute(
            "INSERT INTO amenities (id, name, icon, category) VALUES (?,?,?,?)",
            (aid, data["name"], data["icon"], data["category"]),
        )
        am = row_to_dict(conn.execute("SELECT * FROM amenities WHERE id=?", (aid,)).fetchone())
    return jsonify(am), 201


# ══════════════════════════════════════════════════════════════════
#  ADMIN   /api/admin
# ══════════════════════════════════════════════════════════════════
admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/stats", methods=["GET"])
@require_admin
def admin_stats():
    with db() as conn:
        def count(table, where="1=1", args=()):
            return conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", args).fetchone()[0]

        stats = {
            "users":               count("users", "role='user'"),
            "owners":              count("users", "role='owner'"),
            "total_properties":    count("properties"),
            "available_properties":count("properties", "available=1"),
            "enquiries":           count("enquiries"),
            "pending_enquiries":   count("enquiries", "status='pending'"),
            "reviews":             count("reviews"),
            "govt_hostels":        count("govt_hostels", "active=1"),
        }

        by_type = rows_to_list(conn.execute(
            "SELECT type, COUNT(*) as count FROM properties GROUP BY type"
        ).fetchall())
        by_area = rows_to_list(conn.execute(
            "SELECT area, COUNT(*) as count FROM properties GROUP BY area ORDER BY count DESC LIMIT 10"
        ).fetchall())
        recent_users = rows_to_list(conn.execute(
            "SELECT id, name, email, role, created_at FROM users ORDER BY created_at DESC LIMIT 5"
        ).fetchall())
        recent_props = rows_to_list(conn.execute(
            "SELECT id, name, type, area, verified, created_at FROM properties ORDER BY created_at DESC LIMIT 5"
        ).fetchall())

    return jsonify({
        "counts": stats,
        "breakdowns": {"by_type": by_type, "by_area": by_area},
        "recent": {"users": recent_users, "properties": recent_props},
    })


@admin_bp.route("/users", methods=["GET"])
@require_admin
def admin_users():
    p = request.args
    page   = max(1, p.get("page", 1, type=int))
    limit  = min(50, p.get("limit", 20, type=int))
    offset = (page - 1) * limit
    role   = p.get("role")
    search = p.get("search")

    where, args = ["1=1"], []
    if role:   where.append("role=?");                   args.append(role)
    if search: where.append("(name LIKE ? OR email LIKE ?)"); args += [f"%{search}%"]*2

    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM users WHERE {' AND '.join(where)}", args
        ).fetchone()[0]
        rows = rows_to_list(conn.execute(
            f"SELECT id,name,email,phone,role,verified,created_at FROM users "
            f"WHERE {' AND '.join(where)} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            args + [limit, offset]
        ).fetchall())

    return jsonify({"data": rows, "meta": {"total": total, "page": page, "limit": limit}})


@admin_bp.route("/users/<uid>", methods=["PATCH"])
@require_admin
def admin_update_user(uid):
    data = request.get_json() or {}
    fields, vals = [], []
    if "role"     in data: fields.append("role=?");     vals.append(data["role"])
    if "verified" in data: fields.append("verified=?"); vals.append(int(data["verified"]))
    if not fields:
        return jsonify({"error": "Nothing to update"}), 422
    vals.append(uid)
    with db() as conn:
        conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id=?", vals)
        user = row_to_dict(conn.execute(
            "SELECT id,name,email,role,verified FROM users WHERE id=?", (uid,)
        ).fetchone())
    return jsonify(user)


@admin_bp.route("/users/<uid>", methods=["DELETE"])
@require_admin
def admin_delete_user(uid):
    if uid == g.user["id"]:
        return jsonify({"error": "Cannot delete your own account"}), 400
    with db() as conn:
        conn.execute("DELETE FROM users WHERE id=?", (uid,))
    return jsonify({"message": "User deleted"})


@admin_bp.route("/properties", methods=["GET"])
@require_admin
def admin_properties():
    p = request.args
    page  = max(1, p.get("page", 1, type=int))
    limit = min(50, p.get("limit", 20, type=int))
    offset = (page - 1) * limit
    where, args = ["1=1"], []
    if p.get("verified") is not None: where.append("verified=?"); args.append(int(p.get("verified")=="true"))
    if p.get("type"):                 where.append("type=?");     args.append(p["type"])
    if p.get("search"):               where.append("(name LIKE ? OR area LIKE ?)"); args += [f"%{p['search']}%"]*2

    with db() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM properties WHERE {' AND '.join(where)}", args).fetchone()[0]
        rows  = rows_to_list(conn.execute(
            f"SELECT * FROM properties WHERE {' AND '.join(where)} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            args + [limit, offset]
        ).fetchall())
    return jsonify({"data": rows, "meta": {"total": total, "page": page, "limit": limit}})


@admin_bp.route("/properties/<pid>/verify", methods=["PATCH"])
@require_admin
def admin_verify(pid):
    data = request.get_json() or {}
    with db() as conn:
        conn.execute("UPDATE properties SET verified=? WHERE id=?", (int(data.get("verified", True)), pid))
    return jsonify({"id": pid, "verified": data.get("verified", True)})


@admin_bp.route("/properties/<pid>/feature", methods=["PATCH"])
@require_admin
def admin_feature(pid):
    data = request.get_json() or {}
    with db() as conn:
        conn.execute("UPDATE properties SET featured=? WHERE id=?", (int(data.get("featured", True)), pid))
    return jsonify({"id": pid, "featured": data.get("featured", True)})


@admin_bp.route("/properties/<pid>", methods=["DELETE"])
@require_admin
def admin_delete_prop(pid):
    with db() as conn:
        conn.execute("DELETE FROM properties WHERE id=?", (pid,))
    return jsonify({"message": "Property deleted"})


@admin_bp.route("/reviews", methods=["GET"])
@require_admin
def admin_reviews():
    with db() as conn:
        rows = rows_to_list(conn.execute(
            """SELECT r.*, u.name as user_name, u.email,
                      p.name as property_name
               FROM reviews r JOIN users u ON u.id=r.user_id
               JOIN properties p ON p.id=r.property_id
               ORDER BY r.created_at DESC LIMIT 100"""
        ).fetchall())
    return jsonify(rows)


@admin_bp.route("/reviews/<rid>", methods=["DELETE"])
@require_admin
def admin_delete_review(rid):
    with db() as conn:
        conn.execute("DELETE FROM reviews WHERE id=?", (rid,))
    return jsonify({"message": "Review deleted"})
