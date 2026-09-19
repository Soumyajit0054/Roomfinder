from flask import Flask, session, redirect, url_for, request

from config import SECRET_KEY, UPLOAD_FOLDER

from routes.main import main_bp
from routes.auth import auth_bp
from routes.tenant import tenant_bp
from routes.owner import owner_bp
from routes.admin import admin_bp


app = Flask(__name__)

app.secret_key = SECRET_KEY
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================================================
# REQUEST RECEIVED → LOGIN CHECK → ROLE CHECK
# =========================================================

@app.before_request
def check_login():

    path = request.path

    # Login/Register/Role Selection public thakbe
    public_routes = [
        "/login",
        "/register",
        "/select-role"
    ]

    # Static files always allow
    if path.startswith("/static"):
        return

    # Public page hole allow
    if path in public_routes:
        return

    # -----------------------------
    # STEP 1 → Login Check
    # -----------------------------
    if "user_id" not in session:

        return redirect(
            url_for(
                "auth.login",
                next=path
            )
        )

    # -----------------------------
    # STEP 2 → Role Selection Check
    # -----------------------------
    if not session.get("role"):

        return redirect(
            url_for("auth.select_role")
        )


# =========================================================
# BLUEPRINTS
# =========================================================

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(tenant_bp)
app.register_blueprint(owner_bp)
app.register_blueprint(admin_bp)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)