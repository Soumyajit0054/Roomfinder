import os

from flask import Flask, session, redirect, url_for, request

from config import SECRET_KEY, UPLOAD_FOLDER

from routes.main import main_bp
from routes.auth import auth_bp
from routes.tenant import tenant_bp
from routes.owner import owner_bp
from routes.admin import admin_bp
from routes.api import api_bp
from routes.api_manage import api_owner_bp, api_admin_bp


app = Flask(__name__)

app.secret_key = SECRET_KEY
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB per request


# =========================================================
# REQUEST RECEIVED → LOGIN CHECK → ROLE CHECK
# =========================================================

@app.before_request
def check_login():

    path = request.path

    # Pages reachable without logging in
    public_routes = [
        "/login",
        "/register",
        "/select-role"
    ]

    # Static files, PWA files and the token-authenticated API
    # (the API does its own auth and returns JSON, not redirects)
    if path.startswith(("/static", "/api/")) or path in ("/sw.js", "/offline"):
        return

    # Public pages are always allowed
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
app.register_blueprint(api_bp)
app.register_blueprint(api_owner_bp)
app.register_blueprint(api_admin_bp)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")