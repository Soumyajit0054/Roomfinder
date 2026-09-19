from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from database import query_all, query_one, execute_query


# =========================================================
# TENANT BLUEPRINT
# =========================================================

tenant_bp = Blueprint(
    "tenant",
    __name__,
    url_prefix="/tenant"
)


# =========================================================
# TENANT AUTHORIZATION
# =========================================================

def tenant_required():

    return (
        "user_id" in session
        and session.get("role") == "tenant"
    )


# =========================================================
# TENANT DASHBOARD
# =========================================================

@tenant_bp.route("/dashboard")
def dashboard():

    if not tenant_required():
        return redirect(url_for("auth.login"))

    properties = query_all("""
        SELECT
            p.*,

            (
                SELECT pi.image
                FROM property_images pi
                WHERE pi.property_id = p.id
                ORDER BY pi.id ASC
                LIMIT 1
            ) AS image

        FROM properties p

        WHERE p.available = 1

        ORDER BY p.created_at DESC

        LIMIT 8
    """)

    return render_template(
        "tenant/dashboard.html",
        properties=properties
    )


# =========================================================
# TENANT PROPERTY SEARCH
# =========================================================

@tenant_bp.route("/search")
def search():

    if not tenant_required():
        return redirect(url_for("auth.login"))


    # =====================================================
    # GET SEARCH FILTERS
    # =====================================================

    location = request.args.get(
        "location",
        ""
    ).strip()

    min_rent = request.args.get(
        "min_rent",
        ""
    ).strip()

    max_rent = request.args.get(
        "max_rent",
        ""
    ).strip()

    room_type = request.args.get(
        "room_type",
        ""
    ).strip()

    furnished = request.args.get(
        "furnished",
        ""
    ).strip()


    # =====================================================
    # RENT VALIDATION
    # =====================================================

    min_rent_value = None
    max_rent_value = None


    if min_rent:

        try:

            min_rent_value = float(min_rent)

            if min_rent_value < 0:

                flash(
                    "Minimum rent cannot be negative.",
                    "warning"
                )

                min_rent = ""
                min_rent_value = None

        except ValueError:

            flash(
                "Please enter a valid minimum rent.",
                "warning"
            )

            min_rent = ""
            min_rent_value = None


    if max_rent:

        try:

            max_rent_value = float(max_rent)

            if max_rent_value < 0:

                flash(
                    "Maximum rent cannot be negative.",
                    "warning"
                )

                max_rent = ""
                max_rent_value = None

        except ValueError:

            flash(
                "Please enter a valid maximum rent.",
                "warning"
            )

            max_rent = ""
            max_rent_value = None


    # =====================================================
    # CHECK RENT RANGE
    # =====================================================

    if (
        min_rent_value is not None
        and
        max_rent_value is not None
        and
        min_rent_value > max_rent_value
    ):

        flash(
            "Minimum rent cannot be greater than maximum rent.",
            "warning"
        )

        return redirect(
            url_for("tenant.search")
        )


    # =====================================================
    # BASE QUERY
    # =====================================================

    sql = """
        SELECT
            p.*,

            u.name AS owner_name,

            (
                SELECT pi.image
                FROM property_images pi
                WHERE pi.property_id = p.id
                ORDER BY pi.id ASC
                LIMIT 1
            ) AS image

        FROM properties p

        LEFT JOIN users u
            ON p.owner_id = u.id

        WHERE p.available = 1
    """


    params = []


    # =====================================================
    # LOCATION SEARCH
    # =====================================================

    if location:

        sql += """
            AND (
                LOWER(COALESCE(p.location, ''))
                    LIKE LOWER(%s)

                OR

                LOWER(COALESCE(p.address, ''))
                    LIKE LOWER(%s)

                OR

                LOWER(COALESCE(p.title, ''))
                    LIKE LOWER(%s)
            )
        """

        location_pattern = f"%{location}%"

        params.extend([
            location_pattern,
            location_pattern,
            location_pattern
        ])


    # =====================================================
    # MINIMUM RENT
    # =====================================================

    if min_rent_value is not None:

        sql += """
            AND p.rent >= %s
        """

        params.append(
            min_rent_value
        )


    # =====================================================
    # MAXIMUM RENT
    # =====================================================

    if max_rent_value is not None:

        sql += """
            AND p.rent <= %s
        """

        params.append(
            max_rent_value
        )


    # =====================================================
    # ROOM TYPE
    # =====================================================

    if room_type:

        sql += """
            AND LOWER(
                COALESCE(p.room_type, '')
            ) = LOWER(%s)
        """

        params.append(
            room_type
        )


    # =====================================================
    # FURNISHED
    # =====================================================

    if furnished:

        sql += """
            AND LOWER(
                COALESCE(p.furnished, '')
            ) = LOWER(%s)
        """

        params.append(
            furnished
        )


    # =====================================================
    # ORDER RESULTS
    # =====================================================

    sql += """
        ORDER BY p.created_at DESC
    """


    # =====================================================
    # EXECUTE SEARCH
    # =====================================================

    properties = query_all(
        sql,
        tuple(params)
    )


    # =====================================================
    # OPEN SEPARATE SEARCH RESULTS PAGE
    # =====================================================

    return render_template(
        "tenant/search_results.html",
        properties=properties,
        location=location,
        min_rent=min_rent,
        max_rent=max_rent,
        room_type=room_type,
        furnished=furnished
    )


# =========================================================
# ADD / REMOVE FAVORITE
# =========================================================

@tenant_bp.route(
    "/favorite/<int:property_id>",
    methods=["POST"]
)
def favorite(property_id):

    if not tenant_required():
        return redirect(url_for("auth.login"))

    tenant_id = session["user_id"]


    property_data = query_one("""
        SELECT
            id,
            available
        FROM properties
        WHERE id = %s
    """, (
        property_id,
    ))


    if not property_data:

        flash(
            "Property not found.",
            "danger"
        )

        return redirect(
            request.referrer
            or
            url_for("tenant.dashboard")
        )


    existing = query_one("""
        SELECT id
        FROM favorites
        WHERE tenant_id = %s
        AND property_id = %s
    """, (
        tenant_id,
        property_id
    ))


    if existing:

        execute_query(
            """
                DELETE FROM favorites
                WHERE id = %s
            """,
            (
                existing["id"],
            )
        )

        flash(
            "Property removed from favorites.",
            "success"
        )

    else:

        execute_query("""
            INSERT INTO favorites
            (
                tenant_id,
                property_id
            )
            VALUES
            (
                %s,
                %s
            )
        """, (
            tenant_id,
            property_id
        ))

        flash(
            "Property added to favorites.",
            "success"
        )


    return redirect(
        request.referrer
        or
        url_for("tenant.dashboard")
    )


# =========================================================
# FAVORITES
# =========================================================

@tenant_bp.route("/favorites")
def favorites():

    if not tenant_required():
        return redirect(url_for("auth.login"))


    properties = query_all("""
        SELECT
            p.*,

            f.id AS favorite_id,

            (
                SELECT pi.image
                FROM property_images pi
                WHERE pi.property_id = p.id
                ORDER BY pi.id ASC
                LIMIT 1
            ) AS image

        FROM favorites f

        INNER JOIN properties p
            ON f.property_id = p.id

        WHERE f.tenant_id = %s

        ORDER BY f.created_at DESC
    """, (
        session["user_id"],
    ))


    return render_template(
        "tenant/favorites.html",
        properties=properties
    )


# =========================================================
# SEND RENTAL REQUEST
# =========================================================

@tenant_bp.route(
    "/request/<int:property_id>",
    methods=["POST"]
)
def rental_request(property_id):

    if not tenant_required():
        return redirect(url_for("auth.login"))


    tenant_id = session["user_id"]


    message = request.form.get(
        "message",
        ""
    ).strip()


    if len(message) > 1000:

        flash(
            "Message cannot exceed 1000 characters.",
            "warning"
        )

        return redirect(
            url_for(
                "main.property_details",
                property_id=property_id
            )
        )


    property_data = query_one("""
        SELECT
            id,
            title,
            available
        FROM properties
        WHERE id = %s
    """, (
        property_id,
    ))


    if not property_data:

        flash(
            "Property not found.",
            "danger"
        )

        return redirect(
            url_for("tenant.dashboard")
        )


    if not property_data["available"]:

        flash(
            "This property is no longer available.",
            "warning"
        )

        return redirect(
            url_for(
                "main.property_details",
                property_id=property_id
            )
        )


    existing = query_one("""
        SELECT
            id,
            status
        FROM rental_requests
        WHERE tenant_id = %s
        AND property_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (
        tenant_id,
        property_id
    ))


    if existing:

        if existing["status"] == "pending":

            flash(
                "You already have a pending request for this property.",
                "warning"
            )

            return redirect(
                url_for(
                    "main.property_details",
                    property_id=property_id
                )
            )


        if existing["status"] == "accepted":

            flash(
                "Your request for this property has already been accepted.",
                "info"
            )

            return redirect(
                url_for(
                    "main.property_details",
                    property_id=property_id
                )
            )


    execute_query("""
        INSERT INTO rental_requests
        (
            property_id,
            tenant_id,
            message,
            status
        )
        VALUES
        (
            %s,
            %s,
            %s,
            'pending'
        )
    """, (
        property_id,
        tenant_id,
        message
    ))


    flash(
        "Rental request sent successfully.",
        "success"
    )


    return redirect(
        url_for(
            "main.property_details",
            property_id=property_id
        )
    )


# =========================================================
# TENANT RENTAL REQUESTS
# =========================================================

@tenant_bp.route("/requests")
def requests():

    if not tenant_required():
        return redirect(url_for("auth.login"))


    requests_data = query_all("""
        SELECT
            r.*,

            p.title,
            p.location,
            p.rent,

            (
                SELECT pi.image
                FROM property_images pi
                WHERE pi.property_id = p.id
                ORDER BY pi.id ASC
                LIMIT 1
            ) AS image

        FROM rental_requests r

        INNER JOIN properties p
            ON r.property_id = p.id

        WHERE r.tenant_id = %s

        ORDER BY r.created_at DESC
    """, (
        session["user_id"],
    ))


    return render_template(
        "tenant/requests.html",
        requests=requests_data
    )


# =========================================================
# TENANT PROFILE
# =========================================================

@tenant_bp.route("/profile")
def profile():

    if not tenant_required():
        return redirect(url_for("auth.login"))


    user = query_one(
        """
            SELECT *
            FROM users
            WHERE id = %s
        """,
        (
            session["user_id"],
        )
    )


    if not user:

        session.clear()

        flash(
            "Your account could not be found. Please login again.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )


    return render_template(
        "tenant/profile.html",
        user=user
    )