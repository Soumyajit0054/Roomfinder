from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import generate_password_hash, check_password_hash

from database import query_one, execute_query


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "tenant")

        if not name or not email or not password:
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("auth.register"))

        if role not in ["tenant", "owner"]:
            role = "tenant"

        existing_user = query_one(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )

        if existing_user:
            flash("Email already registered.", "danger")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)

        execute_query("""
            INSERT INTO users
            (name, email, phone, password, role)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            name,
            email,
            phone,
            hashed_password,
            role
        ))

        flash("Registration successful. Please login.", "success")

        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = query_one(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        if not user:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        if not check_password_hash(user["password"], password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        session.clear()

        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["role"] = user["role"]

        if user["role"] == "tenant":
            return redirect(url_for("tenant.dashboard"))

        if user["role"] == "owner":
            return redirect(url_for("owner.dashboard"))

        if user["role"] == "admin":
            return redirect(url_for("admin.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("main.home"))

@auth_bp.route("/select-role", methods=["GET", "POST"])
def select_role():

    # Login na korle login page
    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )


    if request.method == "POST":

        role = request.form.get("role")


        # Sudhu ei duita role allowed
        if role not in ["tenant", "owner"]:

            flash(
                "Please select Tenant or Owner.",
                "danger"
            )

            return redirect(
                url_for("auth.select_role")
            )


        # User-er role session-e save
        session["role"] = role


        # Correct dashboard
        if role == "tenant":

            return redirect(
                url_for("tenant.dashboard")
            )


        if role == "owner":

            return redirect(
                url_for("owner.dashboard")
            )


    return render_template("select_role.html")