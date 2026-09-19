from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request
)

from database import query_all, query_one, execute_query


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


def admin_required():

    return (
        "user_id" in session
        and session.get("role") == "admin"
    )


@admin_bp.route("/dashboard")
def dashboard():

    if not admin_required():
        return redirect(url_for("auth.login"))

    users = query_one("""
        SELECT COUNT(*) AS total
        FROM users
    """)

    tenants = query_one("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE role = 'tenant'
    """)

    owners = query_one("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE role = 'owner'
    """)

    properties = query_one("""
        SELECT COUNT(*) AS total
        FROM properties
    """)

    requests_count = query_one("""
        SELECT COUNT(*) AS total
        FROM rental_requests
    """)

    return render_template(
        "admin/dashboard.html",
        users=users["total"],
        tenants=tenants["total"],
        owners=owners["total"],
        properties=properties["total"],
        requests=requests_count["total"]
    )


@admin_bp.route("/users")
def users():

    if not admin_required():
        return redirect(url_for("auth.login"))

    users_data = query_all("""
        SELECT
            id,
            name,
            email,
            phone,
            role,
            created_at
        FROM users
        ORDER BY created_at DESC
    """)


    return render_template(
        "admin/users.html",
        users=users_data
    )


@admin_bp.route(
    "/delete-user/<int:user_id>",
    methods=["POST"]
)
def delete_user(user_id):

    if not admin_required():
        return redirect(url_for("auth.login"))

    if user_id == session["user_id"]:
        flash(
            "You cannot delete yourself.",
            "danger"
        )

        return redirect(
            url_for("admin.users")
        )

    execute_query(
        "DELETE FROM users WHERE id = %s",
        (user_id,)
    )

    flash(
        "User deleted successfully.",
        "success"
    )

    return redirect(
        url_for("admin.users")
    )


@admin_bp.route("/properties")
def properties():

    if not admin_required():
        return redirect(url_for("auth.login"))

    properties_data = query_all("""
        SELECT
            p.*,
            u.name AS owner_name
        FROM properties p
        JOIN users u
            ON p.owner_id = u.id
        ORDER BY p.created_at DESC
    """)

    return render_template(
        "admin/properties.html",
        properties=properties_data
    )


@admin_bp.route(
    "/delete-property/<int:property_id>",
    methods=["POST"]
)
def delete_property(property_id):

    if not admin_required():
        return redirect(url_for("auth.login"))

    execute_query(
        "DELETE FROM properties WHERE id = %s",
        (property_id,)
    )

    flash(
        "Property deleted successfully.",
        "success"
    )

    return redirect(
        url_for("admin.properties")
    )


@admin_bp.route("/requests")
def requests():

    if not admin_required():
        return redirect(url_for("auth.login"))

    requests_data = query_all("""
        SELECT
            r.*,
            p.title,
            p.rent,
            p.location,
            tenant.name AS tenant_name,
            owner.name AS owner_name
        FROM rental_requests r
        JOIN properties p
            ON r.property_id = p.id
        JOIN users tenant
            ON r.tenant_id = tenant.id
        JOIN users owner
            ON p.owner_id = owner.id
        ORDER BY r.created_at DESC
    """)

    return render_template(
        "admin/requests.html",
        requests=requests_data
    )