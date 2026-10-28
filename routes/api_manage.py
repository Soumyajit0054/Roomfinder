"""Owner and admin JSON API for the mobile app (/api/v1/owner, /api/v1/admin).

Mirrors the rules in routes/owner.py and routes/admin.py.
"""
import os
import uuid

from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.utils import secure_filename

from config import ALLOWED_EXTENSIONS
from database import execute_query, query_all, query_one
from routes.api import (
    FIRST_IMAGE, auth_required, error, image_url, serialize_property,
)

api_owner_bp = Blueprint("api_owner", __name__, url_prefix="/api/v1/owner")
api_admin_bp = Blueprint("api_admin", __name__, url_prefix="/api/v1/admin")

# SVG can carry scripts and uploads are served from the app's own origin,
# so the API only accepts raster formats.
API_IMAGE_EXTENSIONS = ALLOWED_EXTENSIONS - {"svg"}
MAX_IMAGES_PER_REQUEST = 10


def iso(value):
    return value.isoformat() if value else None


def count(sql, params=()):
    row = query_one(sql, params)
    return row["total"] if row else 0


# =========================================================
# IMAGE HELPERS
# =========================================================

def save_images(files, property_id):
    """Save uploaded images for a property. Returns (saved_count, rejected_names)."""
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    saved, rejected = 0, []

    for file in files[:MAX_IMAGES_PER_REQUEST]:
        original = (file.filename or "").strip()
        if not original:
            continue
        safe = secure_filename(original)
        ext = safe.rsplit(".", 1)[1].lower() if "." in safe else ""
        if ext not in API_IMAGE_EXTENSIONS:
            rejected.append(original)
            continue

        name = f"property_{property_id}_{uuid.uuid4().hex}.{ext}"
        try:
            file.save(os.path.join(folder, name))
        except OSError:
            rejected.append(original)
            continue
        execute_query(
            "INSERT INTO property_images (property_id, image) VALUES (%s, %s)",
            (property_id, name)
        )
        saved += 1

    rejected += [f.filename for f in files[MAX_IMAGES_PER_REQUEST:]]
    return saved, rejected


def remove_image_file(filename):
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            pass


def parse_property_form(form, current=None):
    """Validate property fields. Returns (values, error_message)."""
    def field(key, default=""):
        fallback = default
        if current and current.get(key) is not None:
            fallback = current[key]
        return str(form.get(key, fallback)).strip()

    title = field("title")
    location = field("location")
    if not title:
        return None, "Property title is required."
    if not location:
        return None, "Property location is required."

    try:
        rent = float(field("rent"))
    except ValueError:
        return None, "Please enter a valid rent amount."
    if rent <= 0:
        return None, "Rent must be greater than 0."

    available = str(form.get("available", current["available"] if current else 1)).lower()

    return {
        "title": title,
        "description": field("description"),
        "location": location,
        "address": field("address"),
        "rent": rent,
        "room_type": field("room_type", "Single") or "Single",
        "furnished": field("furnished", "No") or "No",
        "food_available": field("food_available", "No") or "No",
        "gender_preference": field("gender_preference", "Any") or "Any",
        "available": 1 if available in ("1", "true", "yes", "on") else 0,
    }, None


def owner_property_or_none(property_id):
    return query_one(
        "SELECT * FROM properties WHERE id = %s AND owner_id = %s",
        (property_id, g.user["id"])
    )


def owner_property_payload(row):
    images = query_all(
        "SELECT id, image FROM property_images WHERE property_id = %s ORDER BY id ASC",
        (row["id"],)
    )
    data = serialize_property(row)
    data["images"] = [image_url(i["image"]) for i in images]
    data["image_items"] = [{"id": i["id"], "url": image_url(i["image"])} for i in images]
    data["image"] = data["images"][0] if data["images"] else None
    return data


# =========================================================
# OWNER
# =========================================================

@api_owner_bp.route("/dashboard")
@auth_required(roles=["owner"])
def owner_dashboard():
    uid = g.user["id"]
    return jsonify({
        "property_count": count("SELECT COUNT(*) AS total FROM properties WHERE owner_id = %s", (uid,)),
        "available_count": count(
            "SELECT COUNT(*) AS total FROM properties WHERE owner_id = %s AND available = 1", (uid,)),
        "pending_count": count("""
            SELECT COUNT(*) AS total FROM rental_requests r
            JOIN properties p ON r.property_id = p.id
            WHERE p.owner_id = %s AND r.status = 'pending'
        """, (uid,)),
    })


@api_owner_bp.route("/properties")
@auth_required(roles=["owner"])
def owner_properties():
    rows = query_all(f"""
        SELECT p.*, {FIRST_IMAGE}
        FROM properties p WHERE p.owner_id = %s ORDER BY p.created_at DESC
    """, (g.user["id"],))
    return jsonify({"properties": [serialize_property(r) for r in rows]})


@api_owner_bp.route("/properties/<int:property_id>")
@auth_required(roles=["owner"])
def owner_property(property_id):
    row = owner_property_or_none(property_id)
    if not row:
        return error("Property not found.", 404)
    return jsonify({"property": owner_property_payload(row)})


@api_owner_bp.route("/properties", methods=["POST"])
@auth_required(roles=["owner"])
def owner_add_property():
    """multipart/form-data: property fields + images (repeatable file field)."""
    values, problem = parse_property_form(request.form)
    if problem:
        return error(problem)

    property_id = execute_query("""
        INSERT INTO properties
        (owner_id, title, description, location, address, rent, room_type,
         furnished, food_available, gender_preference, available)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (g.user["id"], values["title"], values["description"], values["location"],
          values["address"], values["rent"], values["room_type"], values["furnished"],
          values["food_available"], values["gender_preference"], 1))
    if not property_id:
        return error("Property could not be created.", 500)

    saved, rejected = save_images(request.files.getlist("images"), property_id)
    row = owner_property_or_none(property_id)
    return jsonify({
        "property": owner_property_payload(row),
        "images_saved": saved,
        "images_rejected": rejected,
    }), 201


@api_owner_bp.route("/properties/<int:property_id>", methods=["PUT"])
@auth_required(roles=["owner"])
def owner_update_property(property_id):
    """multipart/form-data: any property fields, delete_image_ids (repeatable),
    images (repeatable file field). Omitted fields keep their current value."""
    current = owner_property_or_none(property_id)
    if not current:
        return error("Property not found.", 404)

    values, problem = parse_property_form(request.form, current)
    if problem:
        return error(problem)

    execute_query("""
        UPDATE properties SET title=%s, description=%s, location=%s, address=%s,
            rent=%s, room_type=%s, furnished=%s, food_available=%s,
            gender_preference=%s, available=%s
        WHERE id=%s AND owner_id=%s
    """, (values["title"], values["description"], values["location"], values["address"],
          values["rent"], values["room_type"], values["furnished"], values["food_available"],
          values["gender_preference"], values["available"], property_id, g.user["id"]))

    for raw_id in request.form.getlist("delete_image_ids"):
        if not raw_id.isdigit():
            continue
        image = query_one(
            "SELECT id, image FROM property_images WHERE id = %s AND property_id = %s",
            (int(raw_id), property_id))
        if image:
            remove_image_file(image["image"])
            execute_query("DELETE FROM property_images WHERE id = %s", (image["id"],))

    saved, rejected = save_images(request.files.getlist("images"), property_id)
    return jsonify({
        "property": owner_property_payload(owner_property_or_none(property_id)),
        "images_saved": saved,
        "images_rejected": rejected,
    })


@api_owner_bp.route("/properties/<int:property_id>", methods=["DELETE"])
@auth_required(roles=["owner"])
def owner_delete_property(property_id):
    if not owner_property_or_none(property_id):
        return error("Property not found.", 404)
    for image in query_all(
            "SELECT image FROM property_images WHERE property_id = %s", (property_id,)):
        remove_image_file(image["image"])
    execute_query("DELETE FROM properties WHERE id = %s AND owner_id = %s",
                  (property_id, g.user["id"]))
    return jsonify({"deleted": True})


@api_owner_bp.route("/requests")
@auth_required(roles=["owner"])
def owner_requests():
    rows = query_all(f"""
        SELECT r.id, r.status, r.message, r.created_at, r.property_id,
               p.title, p.location, p.rent, {FIRST_IMAGE},
               u.name AS tenant_name, u.email AS tenant_email, u.phone AS tenant_phone
        FROM rental_requests r
        JOIN properties p ON r.property_id = p.id
        JOIN users u ON r.tenant_id = u.id
        WHERE p.owner_id = %s ORDER BY r.created_at DESC
    """, (g.user["id"],))
    return jsonify({"requests": [{
        "id": r["id"],
        "status": r["status"],
        "message": r["message"],
        "created_at": iso(r["created_at"]),
        "tenant": {"name": r["tenant_name"], "email": r["tenant_email"], "phone": r["tenant_phone"]},
        "property": {"id": r["property_id"], "title": r["title"], "location": r["location"],
                     "rent": float(r["rent"]), "image": image_url(r["image"])},
    } for r in rows]})


@api_owner_bp.route("/requests/<int:request_id>", methods=["POST"])
@auth_required(roles=["owner"])
def owner_decide_request(request_id):
    """JSON body: {"status": "accepted" | "rejected"}"""
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in ("accepted", "rejected"):
        return error("status must be 'accepted' or 'rejected'.")

    row = query_one("""
        SELECT r.id, r.property_id FROM rental_requests r
        JOIN properties p ON r.property_id = p.id
        WHERE r.id = %s AND p.owner_id = %s
    """, (request_id, g.user["id"]))
    if not row:
        return error("Request not found.", 404)

    execute_query("UPDATE rental_requests SET status = %s WHERE id = %s", (status, request_id))
    if status == "accepted":
        execute_query("UPDATE properties SET available = 0 WHERE id = %s", (row["property_id"],))
    return jsonify({"status": status})


# =========================================================
# ADMIN
# =========================================================

@api_admin_bp.route("/dashboard")
@auth_required(roles=["admin"])
def admin_dashboard():
    return jsonify({
        "users": count("SELECT COUNT(*) AS total FROM users"),
        "tenants": count("SELECT COUNT(*) AS total FROM users WHERE role = 'tenant'"),
        "owners": count("SELECT COUNT(*) AS total FROM users WHERE role = 'owner'"),
        "properties": count("SELECT COUNT(*) AS total FROM properties"),
        "requests": count("SELECT COUNT(*) AS total FROM rental_requests"),
    })


@api_admin_bp.route("/users")
@auth_required(roles=["admin"])
def admin_users():
    rows = query_all(
        "SELECT id, name, email, phone, role, created_at FROM users ORDER BY created_at DESC")
    return jsonify({"users": [{**r, "created_at": iso(r["created_at"])} for r in rows]})


@api_admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@auth_required(roles=["admin"])
def admin_delete_user(user_id):
    if user_id == g.user["id"]:
        return error("You cannot delete yourself.", 400)
    if not query_one("SELECT id FROM users WHERE id = %s", (user_id,)):
        return error("User not found.", 404)
    execute_query("DELETE FROM users WHERE id = %s", (user_id,))
    return jsonify({"deleted": True})


@api_admin_bp.route("/properties")
@auth_required(roles=["admin"])
def admin_properties():
    rows = query_all(f"""
        SELECT p.*, u.name AS owner_name, {FIRST_IMAGE}
        FROM properties p JOIN users u ON p.owner_id = u.id
        ORDER BY p.created_at DESC
    """)
    return jsonify({"properties": [serialize_property(r) for r in rows]})


@api_admin_bp.route("/properties/<int:property_id>", methods=["DELETE"])
@auth_required(roles=["admin"])
def admin_delete_property(property_id):
    if not query_one("SELECT id FROM properties WHERE id = %s", (property_id,)):
        return error("Property not found.", 404)
    for image in query_all(
            "SELECT image FROM property_images WHERE property_id = %s", (property_id,)):
        remove_image_file(image["image"])
    execute_query("DELETE FROM properties WHERE id = %s", (property_id,))
    return jsonify({"deleted": True})


@api_admin_bp.route("/requests")
@auth_required(roles=["admin"])
def admin_requests():
    rows = query_all("""
        SELECT r.id, r.status, r.message, r.created_at,
               p.id AS property_id, p.title, p.location, p.rent,
               t.name AS tenant_name, o.name AS owner_name
        FROM rental_requests r
        JOIN properties p ON r.property_id = p.id
        JOIN users t ON r.tenant_id = t.id
        JOIN users o ON p.owner_id = o.id
        ORDER BY r.created_at DESC
    """)
    return jsonify({"requests": [{
        "id": r["id"], "status": r["status"], "message": r["message"],
        "created_at": iso(r["created_at"]),
        "tenant_name": r["tenant_name"], "owner_name": r["owner_name"],
        "property": {"id": r["property_id"], "title": r["title"],
                     "location": r["location"], "rent": float(r["rent"])},
    } for r in rows]})
