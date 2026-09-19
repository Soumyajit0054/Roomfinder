import os
import uuid


from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app
)


from werkzeug.utils import secure_filename


from database import (
    query_all,
    query_one,
    execute_query
)


from config import ALLOWED_EXTENSIONS


# =========================================================
# OWNER BLUEPRINT
# =========================================================

owner_bp = Blueprint(
    "owner",
    __name__,
    url_prefix="/owner"
)


# =========================================================
# OWNER AUTHORIZATION
# =========================================================

def owner_required():

    return (
        "user_id" in session
        and session.get("role") == "owner"
    )


# =========================================================
# CHECK ALLOWED IMAGE
# =========================================================

def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


# =========================================================
# OWNER DASHBOARD
# =========================================================

@owner_bp.route("/dashboard")
def dashboard():

    if not owner_required():

        return redirect(
            url_for("auth.login")
        )


    owner_id = session["user_id"]


    property_count = query_one("""
        SELECT COUNT(*) AS total
        FROM properties
        WHERE owner_id = %s
    """, (
        owner_id,
    ))


    available_count = query_one("""
        SELECT COUNT(*) AS total
        FROM properties
        WHERE owner_id = %s
        AND available = 1
    """, (
        owner_id,
    ))


    pending_count = query_one("""
        SELECT COUNT(*) AS total
        FROM rental_requests r

        INNER JOIN properties p
            ON r.property_id = p.id

        WHERE p.owner_id = %s
        AND r.status = 'pending'
    """, (
        owner_id,
    ))


    return render_template(
        "owner/dashboard.html",

        property_count=(
            property_count["total"]
            if property_count
            else 0
        ),

        available_count=(
            available_count["total"]
            if available_count
            else 0
        ),

        pending_count=(
            pending_count["total"]
            if pending_count
            else 0
        )
    )


# =========================================================
# OWNER PROPERTIES
# =========================================================

@owner_bp.route("/properties")
def properties():

    if not owner_required():

        return redirect(
            url_for("auth.login")
        )


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

        WHERE p.owner_id = %s

        ORDER BY p.created_at DESC
    """, (
        session["user_id"],
    ))


    return render_template(
        "owner/properties.html",
        properties=properties
    )


# =========================================================
# ADD PROPERTY
# =========================================================

@owner_bp.route(
    "/add-property",
    methods=["GET", "POST"]
)
def add_property():

    if not owner_required():

        return redirect(
            url_for("auth.login")
        )


    if request.method == "GET":

        return render_template(
            "owner/add_property.html"
        )


    title = request.form.get(
        "title",
        ""
    ).strip()


    description = request.form.get(
        "description",
        ""
    ).strip()


    location = request.form.get(
        "location",
        ""
    ).strip()


    address = request.form.get(
        "address",
        ""
    ).strip()


    rent = request.form.get(
        "rent",
        ""
    ).strip()


    room_type = request.form.get(
        "room_type",
        "Single"
    ).strip()


    furnished = request.form.get(
        "furnished",
        "No"
    ).strip()


    food_available = request.form.get(
        "food_available",
        "No"
    ).strip()


    gender_preference = request.form.get(
        "gender_preference",
        "Any"
    ).strip()


    if not title:

        flash(
            "Property title is required.",
            "danger"
        )

        return redirect(
            url_for("owner.add_property")
        )


    if not location:

        flash(
            "Property location is required.",
            "danger"
        )

        return redirect(
            url_for("owner.add_property")
        )


    try:

        rent_value = float(rent)

    except (
        TypeError,
        ValueError
    ):

        flash(
            "Please enter a valid rent amount.",
            "danger"
        )

        return redirect(
            url_for("owner.add_property")
        )


    if rent_value <= 0:

        flash(
            "Rent must be greater than 0.",
            "danger"
        )

        return redirect(
            url_for("owner.add_property")
        )


    property_id = execute_query("""
        INSERT INTO properties
        (
            owner_id,
            title,
            description,
            location,
            address,
            rent,
            room_type,
            furnished,
            food_available,
            gender_preference,
            available
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            1
        )
    """, (
        session["user_id"],
        title,
        description,
        location,
        address,
        rent_value,
        room_type,
        furnished,
        food_available,
        gender_preference
    ))


    if not property_id:

        flash(
            "Property could not be created.",
            "danger"
        )

        return redirect(
            url_for("owner.add_property")
        )


    upload_folder = current_app.config[
        "UPLOAD_FOLDER"
    ]


    os.makedirs(
        upload_folder,
        exist_ok=True
    )


    files = request.files.getlist(
        "images"
    )


    uploaded_count = 0


    for file in files:

        if not file:
            continue


        original_filename = (
            file.filename or ""
        ).strip()


        if not original_filename:
            continue


        if not allowed_file(
            original_filename
        ):

            flash(
                f"Invalid image format: "
                f"{original_filename}",
                "warning"
            )

            continue


        safe_filename = secure_filename(
            original_filename
        )


        if not safe_filename:
            continue


        extension = safe_filename.rsplit(
            ".",
            1
        )[1].lower()


        unique_filename = (
            f"property_{property_id}_"
            f"{uuid.uuid4().hex}."
            f"{extension}"
        )


        file_path = os.path.join(
            upload_folder,
            unique_filename
        )


        try:

            file.save(
                file_path
            )


            if not os.path.exists(
                file_path
            ):

                continue


            execute_query("""
                INSERT INTO property_images
                (
                    property_id,
                    image
                )
                VALUES
                (
                    %s,
                    %s
                )
            """, (
                property_id,
                unique_filename
            ))


            uploaded_count += 1


        except OSError:

            flash(
                f"Could not save image: "
                f"{original_filename}",
                "danger"
            )


    if uploaded_count > 0:

        flash(
            f"Property added successfully "
            f"with {uploaded_count} image(s).",
            "success"
        )

    else:

        flash(
            "Property added successfully, "
            "but no valid image was uploaded.",
            "warning"
        )


    return redirect(
        url_for("owner.properties")
    )


# =========================================================
# EDIT PROPERTY
# =========================================================

@owner_bp.route(
    "/edit-property/<int:property_id>",
    methods=["GET", "POST"]
)
def edit_property(property_id):

    if not owner_required():

        return redirect(
            url_for("auth.login")
        )


    # =====================================================
    # GET PROPERTY
    # =====================================================

    property_data = query_one("""
        SELECT *
        FROM properties
        WHERE id = %s
        AND owner_id = %s
    """, (
        property_id,
        session["user_id"]
    ))


    if not property_data:

        flash(
            "Property not found.",
            "danger"
        )

        return redirect(
            url_for("owner.properties")
        )


    # =====================================================
    # GET CURRENT IMAGES
    # =====================================================

    images = query_all("""
        SELECT
            id,
            image
        FROM property_images
        WHERE property_id = %s
        ORDER BY id ASC
    """, (
        property_id,
    ))


    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":


        # -------------------------------------------------
        # GET FORM VALUES
        # -------------------------------------------------

        title = request.form.get(
            "title",
            property_data["title"]
        ).strip()


        description = request.form.get(
            "description",
            property_data["description"] or ""
        ).strip()


        location = request.form.get(
            "location",
            property_data["location"]
        ).strip()


        address = request.form.get(
            "address",
            property_data["address"] or ""
        ).strip()


        rent = request.form.get(
            "rent",
            property_data["rent"]
        )


        room_type = request.form.get(
            "room_type",
            property_data["room_type"]
        ).strip()


        furnished = request.form.get(
            "furnished",
            property_data["furnished"]
        ).strip()


        food_available = request.form.get(
            "food_available",
            property_data["food_available"]
        ).strip()


        gender_preference = request.form.get(
            "gender_preference",
            property_data["gender_preference"]
        ).strip()


        available = request.form.get(
            "available",
            property_data["available"]
        )


        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not title:

            flash(
                "Property title cannot be empty.",
                "danger"
            )

            return render_template(
                "owner/edit_property.html",
                property=property_data,
                images=images
            )


        if not location:

            flash(
                "Location cannot be empty.",
                "danger"
            )

            return render_template(
                "owner/edit_property.html",
                property=property_data,
                images=images
            )


        try:

            rent_value = float(
                rent
            )

        except (
            TypeError,
            ValueError
        ):

            flash(
                "Please enter a valid rent amount.",
                "danger"
            )

            return render_template(
                "owner/edit_property.html",
                property=property_data,
                images=images
            )


        if rent_value <= 0:

            flash(
                "Rent must be greater than 0.",
                "danger"
            )

            return render_template(
                "owner/edit_property.html",
                property=property_data,
                images=images
            )


        # -------------------------------------------------
        # AVAILABILITY
        # -------------------------------------------------

        available_value = (
            1
            if str(available).lower()
            in (
                "1",
                "yes",
                "true",
                "on"
            )
            else 0
        )


        # =================================================
        # UPDATE PROPERTY DATA
        # =================================================

        execute_query("""
            UPDATE properties

            SET
                title = %s,
                description = %s,
                location = %s,
                address = %s,
                rent = %s,
                room_type = %s,
                furnished = %s,
                food_available = %s,
                gender_preference = %s,
                available = %s

            WHERE id = %s
            AND owner_id = %s
        """, (
            title,
            description,
            location,
            address,
            rent_value,
            room_type,
            furnished,
            food_available,
            gender_preference,
            available_value,
            property_id,
            session["user_id"]
        ))


        # =================================================
        # DELETE SELECTED OLD IMAGES
        # =================================================

        delete_image_ids = request.form.getlist(
            "delete_images"
        )


        upload_folder = current_app.config[
            "UPLOAD_FOLDER"
        ]


        if delete_image_ids:

            for image_id in delete_image_ids:

                image_data = query_one("""
                    SELECT
                        id,
                        image
                    FROM property_images

                    WHERE id = %s
                    AND property_id = %s
                """, (
                    image_id,
                    property_id
                ))


                if not image_data:

                    continue


                file_path = os.path.join(
                    upload_folder,
                    image_data["image"]
                )


                # -----------------------------------------
                # DELETE PHYSICAL FILE
                # -----------------------------------------

                if os.path.isfile(
                    file_path
                ):

                    try:

                        os.remove(
                            file_path
                        )

                    except OSError:

                        pass


                # -----------------------------------------
                # DELETE DB RECORD
                # -----------------------------------------

                execute_query("""
                    DELETE FROM property_images

                    WHERE id = %s
                    AND property_id = %s
                """, (
                    image_id,
                    property_id
                ))


        # =================================================
        # ADD NEW IMAGES
        # =================================================

        new_files = request.files.getlist(
            "new_images"
        )


        os.makedirs(
            upload_folder,
            exist_ok=True
        )


        new_uploaded_count = 0


        for file in new_files:

            if not file:
                continue


            original_filename = (
                file.filename or ""
            ).strip()


            if not original_filename:
                continue


            if not allowed_file(
                original_filename
            ):

                flash(
                    f"Invalid image format: "
                    f"{original_filename}",
                    "warning"
                )

                continue


            safe_filename = secure_filename(
                original_filename
            )


            if not safe_filename:
                continue


            extension = safe_filename.rsplit(
                ".",
                1
            )[1].lower()


            unique_filename = (
                f"property_{property_id}_"
                f"{uuid.uuid4().hex}."
                f"{extension}"
            )


            file_path = os.path.join(
                upload_folder,
                unique_filename
            )


            try:

                file.save(
                    file_path
                )


                if not os.path.isfile(
                    file_path
                ):

                    continue


                execute_query("""
                    INSERT INTO property_images
                    (
                        property_id,
                        image
                    )
                    VALUES
                    (
                        %s,
                        %s
                    )
                """, (
                    property_id,
                    unique_filename
                ))


                new_uploaded_count += 1


            except OSError:

                flash(
                    f"Could not save image: "
                    f"{original_filename}",
                    "danger"
                )


        # =================================================
        # SUCCESS MESSAGE
        # =================================================

        if new_uploaded_count > 0:

            flash(
                f"Property updated successfully. "
                f"{new_uploaded_count} new image(s) added.",
                "success"
            )

        else:

            flash(
                "Property updated successfully.",
                "success"
            )


        return redirect(
            url_for(
                "owner.properties"
            )
        )


    # =====================================================
    # GET → EDIT PAGE
    # =====================================================

    return render_template(
        "owner/edit_property.html",
        property=property_data,
        images=images
    )


# =========================================================
# DELETE PROPERTY
# =========================================================

@owner_bp.route(
    "/delete-property/<int:property_id>",
    methods=["POST"]
)
def delete_property(property_id):

    if not owner_required():

        return redirect(
            url_for("auth.login")
        )


    property_data = query_one("""
        SELECT id
        FROM properties
        WHERE id = %s
        AND owner_id = %s
    """, (
        property_id,
        session["user_id"]
    ))


    if not property_data:

        flash(
            "Property not found.",
            "danger"
        )

        return redirect(
            url_for("owner.properties")
        )


    images = query_all("""
        SELECT image
        FROM property_images
        WHERE property_id = %s
    """, (
        property_id,
    ))


    upload_folder = current_app.config[
        "UPLOAD_FOLDER"
    ]


    for image in images:

        file_path = os.path.join(
            upload_folder,
            image["image"]
        )


        if os.path.isfile(
            file_path
        ):

            try:

                os.remove(
                    file_path
                )

            except OSError:

                pass


    execute_query("""
        DELETE FROM properties

        WHERE id = %s
        AND owner_id = %s
    """, (
        property_id,
        session["user_id"]
    ))


    flash(
        "Property deleted successfully.",
        "success"
    )


    return redirect(
        url_for("owner.properties")
    )


# =========================================================
# OWNER REQUESTS
# =========================================================

@owner_bp.route("/requests")
def requests():

    if not owner_required():

        return redirect(
            url_for("auth.login")
        )


    requests_data = query_all("""
        SELECT
            r.*,

            p.title,
            p.location,
            p.rent,

            u.name AS tenant_name,
            u.email AS tenant_email,
            u.phone AS tenant_phone

        FROM rental_requests r

        INNER JOIN properties p
            ON r.property_id = p.id

        INNER JOIN users u
            ON r.tenant_id = u.id

        WHERE p.owner_id = %s

        ORDER BY r.created_at DESC
    """, (
        session["user_id"],
    ))


    return render_template(
        "owner/requests.html",
        requests=requests_data
    )


# =========================================================
# ACCEPT / REJECT REQUEST
# =========================================================

@owner_bp.route(
    "/request/<int:request_id>/<status>",
    methods=["POST"]
)
def update_request(
    request_id,
    status
):

    if not owner_required():

        return redirect(
            url_for("auth.login")
        )


    if status not in [
        "accepted",
        "rejected"
    ]:

        flash(
            "Invalid request status.",
            "danger"
        )

        return redirect(
            url_for("owner.requests")
        )


    request_data = query_one("""
        SELECT
            r.id,
            r.property_id,
            r.status

        FROM rental_requests r

        INNER JOIN properties p
            ON r.property_id = p.id

        WHERE r.id = %s
        AND p.owner_id = %s
    """, (
        request_id,
        session["user_id"]
    ))


    if not request_data:

        flash(
            "Request not found.",
            "danger"
        )

        return redirect(
            url_for("owner.requests")
        )


    execute_query("""
        UPDATE rental_requests
        SET status = %s
        WHERE id = %s
    """, (
        status,
        request_id
    ))


    if status == "accepted":

        execute_query("""
            UPDATE properties
            SET available = 0
            WHERE id = %s
        """, (
            request_data["property_id"],
        ))


    flash(
        f"Request {status}.",
        "success"
    )


    return redirect(
        url_for("owner.requests")
    )


# =========================================================
# OWNER PROFILE
# =========================================================

@owner_bp.route("/profile")
def profile():

    if not owner_required():

        return redirect(
            url_for("auth.login")
        )


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
            "Owner account not found. Please login again.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )


    return render_template(
        "owner/profile.html",
        user=user
    )