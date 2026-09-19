from flask import Blueprint, render_template, request

from database import query_all, query_one


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():

    properties = query_all("""
        SELECT
            p.*,
            u.name AS owner_name,
            (
                SELECT image
                FROM property_images
                WHERE property_id = p.id
                LIMIT 1
            ) AS image
        FROM properties p
        JOIN users u ON p.owner_id = u.id
        WHERE p.available = 1
        ORDER BY p.created_at DESC
        LIMIT 6
    """)

    return render_template(
        "home.html",
        properties=properties
    )


@main_bp.route("/properties")
def properties():

    location = request.args.get("location", "").strip()
    min_rent = request.args.get("min_rent", "").strip()
    max_rent = request.args.get("max_rent", "").strip()
    room_type = request.args.get("room_type", "").strip()
    furnished = request.args.get("furnished", "").strip()

    sql = """
        SELECT
            p.*,
            u.name AS owner_name,
            (
                SELECT image
                FROM property_images
                WHERE property_id = p.id
                LIMIT 1
            ) AS image
        FROM properties p
        JOIN users u ON p.owner_id = u.id
        WHERE p.available = 1
    """

    params = []

    if location:
        sql += " AND (p.location LIKE %s OR p.address LIKE %s)"
        params.extend([
            f"%{location}%",
            f"%{location}%"
        ])

    if min_rent:
        sql += " AND p.rent >= %s"
        params.append(min_rent)

    if max_rent:
        sql += " AND p.rent <= %s"
        params.append(max_rent)

    if room_type:
        sql += " AND p.room_type = %s"
        params.append(room_type)

    if furnished:
        sql += " AND p.furnished = %s"
        params.append(furnished)

    sql += " ORDER BY p.created_at DESC"

    properties = query_all(sql, params)

    return render_template(
        "home.html",
        properties=properties
    )


@main_bp.route("/property/<int:property_id>")
def property_details(property_id):

    property_data = query_one("""
        SELECT
            p.*,
            u.name AS owner_name,
            u.email AS owner_email,
            u.phone AS owner_phone
        FROM properties p
        JOIN users u ON p.owner_id = u.id
        WHERE p.id = %s
    """, (property_id,))

    if not property_data:
        return "Property not found", 404

    images = query_all("""
        SELECT *
        FROM property_images
        WHERE property_id = %s
    """, (property_id,))

    return render_template(
        "property_details.html",
        property=property_data,
        images=images
    )