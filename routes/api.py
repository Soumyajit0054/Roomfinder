"""JSON API for the mobile app (mounted at /api/v1).

Auth is a signed bearer token (Authorization: Bearer <token>) instead of the
cookie session used by the web UI.
"""
from functools import wraps

from flask import Blueprint, jsonify, request, current_app, g
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import check_password_hash, generate_password_hash

from config import API_TOKEN_MAX_AGE, UPLOAD_BASE_URL
from database import query_all, query_one, execute_query
from routes.auth import COUNTRY_ID_RULES, validate_government_id, save_government_id


api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

TOKEN_SALT = "roomfinder-api-token"


# =========================================================
# HELPERS
# =========================================================

def error(message, status=400):
    return jsonify({"error": message}), status


def _serializer():
    return URLSafeTimedSerializer(current_app.secret_key, salt=TOKEN_SALT)


def make_token(user_id, role):
    return _serializer().dumps({"uid": user_id, "role": role})


def _read_token():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        return _serializer().loads(header[7:], max_age=API_TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def auth_required(roles=None):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            data = _read_token()
            if not data:
                return error("Authentication required.", 401)
            if not data.get("role"):
                return error("Role selection required.", 403)
            if roles and data["role"] not in roles:
                return error("Not allowed for this role.", 403)
            user = query_one(
                "SELECT id, name, email, phone, role FROM users WHERE id = %s",
                (data["uid"],)
            )
            if not user:
                return error("Account no longer exists.", 401)
            g.user = user
            g.role = data["role"]
            return view(*args, **kwargs)
        return wrapper
    return decorator


def image_url(filename):
    if not filename:
        return None
    if UPLOAD_BASE_URL:
        return f"{UPLOAD_BASE_URL}/{filename}"
    return f"{request.host_url.rstrip('/')}/static/uploads/{filename}"


def serialize_property(row, with_contact=False):
    out = {
        "id": row["id"],
        "title": row["title"],
        "description": row.get("description"),
        "location": row["location"],
        "address": row.get("address"),
        "rent": float(row["rent"]),
        "room_type": row["room_type"],
        "furnished": row.get("furnished"),
        "food_available": row.get("food_available"),
        "gender_preference": row.get("gender_preference"),
        "available": bool(row["available"]),
        "owner_name": row.get("owner_name"),
        "image": image_url(row.get("image")),
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
    }
    if with_contact:
        out["owner_email"] = row.get("owner_email")
        out["owner_phone"] = row.get("owner_phone")
    return out


def serialize_user(user, role):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "phone": user.get("phone"),
        "role": role,
    }


FIRST_IMAGE = """(
    SELECT image FROM property_images
    WHERE property_id = p.id ORDER BY id ASC LIMIT 1
) AS image"""


# =========================================================
# AUTH
# =========================================================

@api_bp.route("/auth/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip()
    password = body.get("password") or ""

    user = query_one("SELECT * FROM users WHERE email = %s", (email,))
    if not user or not check_password_hash(user["password"], password):
        return error("Invalid email or password.", 401)

    return jsonify({
        "token": make_token(user["id"], user["role"]),
        "user": serialize_user(user, user["role"]),
    })


@api_bp.route("/auth/register", methods=["POST"])
def register():
    """multipart/form-data: name, email, phone, password, role, country,
    government_id (PDF)."""
    form = request.form
    name = form.get("name", "").strip()
    email = form.get("email", "").strip()
    phone = form.get("phone", "").strip()
    password = form.get("password", "")
    role = form.get("role", "tenant")
    country = form.get("country", "").strip()
    government_id = request.files.get("government_id")

    if not name or not email or not password:
        return error("Please fill all required fields.")
    if country not in COUNTRY_ID_RULES:
        return error("Please select a supported country.")
    if role not in ("tenant", "owner"):
        role = "tenant"

    check = validate_government_id(government_id, country)
    if not check["valid"]:
        return error(check["error"])

    if query_one("SELECT id FROM users WHERE email = %s", (email,)):
        return error("Email already registered.", 409)

    id_file = save_government_id(government_id)
    execute_query("""
        INSERT INTO users
        (name, email, phone, password, role, country, government_id_file,
         government_id_verified, government_id_status,
         government_id_validation_method, government_id_validation_notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s, %s, %s)
    """, (name, email, phone, generate_password_hash(password), role, country,
          id_file, "auto_verified", check["method"], check["notes"]))

    return jsonify({"message": "Registration successful."}), 201


@api_bp.route("/auth/countries")
def countries():
    return jsonify({"countries": sorted(COUNTRY_ID_RULES.keys())})


@api_bp.route("/auth/me")
@auth_required()
def me():
    return jsonify({"user": serialize_user(g.user, g.role)})


@api_bp.route("/profile")
@auth_required()
def profile():
    row = query_one("""
        SELECT id, name, email, phone, country, government_id_status,
               government_id_verified, created_at
        FROM users WHERE id = %s
    """, (g.user["id"],))
    return jsonify({"profile": {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"],
        "role": g.role,
        "country": row.get("country"),
        "id_status": row.get("government_id_status"),
        "id_verified": bool(row.get("government_id_verified")),
        "member_since": row["created_at"].isoformat() if row.get("created_at") else None,
    }})


# =========================================================
# PROPERTIES (public read; owner contact only when signed in)
# =========================================================

@api_bp.route("/properties")
def list_properties():
    args = request.args
    sql = f"""
        SELECT p.*, u.name AS owner_name, {FIRST_IMAGE}
        FROM properties p JOIN users u ON p.owner_id = u.id
        WHERE p.available = 1
    """
    params = []

    location = args.get("location", "").strip()
    if location:
        sql += " AND (p.location LIKE %s OR p.address LIKE %s)"
        params += [f"%{location}%"] * 2

    for key, op in (("min_rent", ">="), ("max_rent", "<=")):
        val = args.get(key, "").strip()
        if val:
            try:
                params.append(float(val))
            except ValueError:
                return error(f"{key} must be a number.")
            sql += f" AND p.rent {op} %s"

    for key in ("room_type", "furnished"):
        val = args.get(key, "").strip()
        if val:
            sql += f" AND p.{key} = %s"
            params.append(val)

    try:
        limit = min(max(int(args.get("limit", 20)), 1), 100)
        offset = max(int(args.get("offset", 0)), 0)
    except ValueError:
        return error("limit and offset must be integers.")

    sql += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
    params += [limit, offset]

    rows = query_all(sql, params)
    return jsonify({
        "properties": [serialize_property(r) for r in rows],
        "limit": limit,
        "offset": offset,
    })


@api_bp.route("/properties/<int:property_id>")
def property_detail(property_id):
    row = query_one("""
        SELECT p.*, u.name AS owner_name,
               u.email AS owner_email, u.phone AS owner_phone
        FROM properties p JOIN users u ON p.owner_id = u.id
        WHERE p.id = %s
    """, (property_id,))
    if not row:
        return error("Property not found.", 404)

    images = query_all(
        "SELECT image FROM property_images WHERE property_id = %s ORDER BY id ASC",
        (property_id,)
    )
    data = serialize_property(row, with_contact=_read_token() is not None)
    data["images"] = [image_url(i["image"]) for i in images]
    data["image"] = data["images"][0] if data["images"] else None
    return jsonify({"property": data})


# =========================================================
# FAVORITES (tenant)
# =========================================================

@api_bp.route("/favorites")
@auth_required(roles=["tenant"])
def list_favorites():
    rows = query_all(f"""
        SELECT p.*, u.name AS owner_name, {FIRST_IMAGE}
        FROM favorites f
        JOIN properties p ON f.property_id = p.id
        JOIN users u ON p.owner_id = u.id
        WHERE f.tenant_id = %s ORDER BY f.created_at DESC
    """, (g.user["id"],))
    return jsonify({"properties": [serialize_property(r) for r in rows]})


@api_bp.route("/favorites/<int:property_id>", methods=["PUT", "DELETE"])
@auth_required(roles=["tenant"])
def set_favorite(property_id):
    if not query_one("SELECT id FROM properties WHERE id = %s", (property_id,)):
        return error("Property not found.", 404)

    existing = query_one(
        "SELECT id FROM favorites WHERE tenant_id = %s AND property_id = %s",
        (g.user["id"], property_id)
    )

    if request.method == "PUT" and not existing:
        execute_query(
            "INSERT INTO favorites (tenant_id, property_id) VALUES (%s, %s)",
            (g.user["id"], property_id)
        )
    elif request.method == "DELETE" and existing:
        execute_query("DELETE FROM favorites WHERE id = %s", (existing["id"],))

    return jsonify({"favorite": request.method == "PUT"})


# =========================================================
# RENTAL REQUESTS (tenant)
# =========================================================

@api_bp.route("/requests")
@auth_required(roles=["tenant"])
def list_requests():
    rows = query_all(f"""
        SELECT r.id, r.status, r.message, r.created_at, r.property_id,
               p.title, p.location, p.rent, {FIRST_IMAGE}
        FROM rental_requests r JOIN properties p ON r.property_id = p.id
        WHERE r.tenant_id = %s ORDER BY r.created_at DESC
    """, (g.user["id"],))
    return jsonify({"requests": [{
        "id": r["id"],
        "status": r["status"],
        "message": r["message"],
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        "property": {
            "id": r["property_id"],
            "title": r["title"],
            "location": r["location"],
            "rent": float(r["rent"]),
            "image": image_url(r["image"]),
        },
    } for r in rows]})


@api_bp.route("/properties/<int:property_id>/request", methods=["POST"])
@auth_required(roles=["tenant"])
def create_request(property_id):
    message = ((request.get_json(silent=True) or {}).get("message") or "").strip()
    if len(message) > 1000:
        return error("Message cannot exceed 1000 characters.")

    prop = query_one(
        "SELECT id, available FROM properties WHERE id = %s", (property_id,)
    )
    if not prop:
        return error("Property not found.", 404)
    if not prop["available"]:
        return error("This property is no longer available.", 409)

    existing = query_one("""
        SELECT status FROM rental_requests
        WHERE tenant_id = %s AND property_id = %s
        ORDER BY created_at DESC LIMIT 1
    """, (g.user["id"], property_id))
    if existing and existing["status"] in ("pending", "accepted"):
        return error(
            f"You already have a {existing['status']} request for this property.",
            409
        )

    execute_query(
        "INSERT INTO rental_requests (property_id, tenant_id, message, status) "
        "VALUES (%s, %s, %s, 'pending')",
        (property_id, g.user["id"], message)
    )
    return jsonify({"message": "Rental request sent."}), 201
