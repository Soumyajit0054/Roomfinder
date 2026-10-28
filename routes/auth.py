import os
import re
import uuid
from io import BytesIO

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
from werkzeug.security import generate_password_hash, check_password_hash

from database import query_one, execute_query


auth_bp = Blueprint("auth", __name__)

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from pdf2image import convert_from_bytes
    import pytesseract
except ImportError:
    convert_from_bytes = None
    pytesseract = None


COMMON_PASSPORT_PATTERN = r"\b[A-Z][0-9]{7,8}\b|\b[0-9]{8,9}\b"


COUNTRY_ID_RULES = {
    "Argentina": {
        "keywords": (
            "dni",
            "documento nacional",
            "pasaporte",
            "licencia",
            "passport"
        ),
        "patterns": (
            r"\b[0-9]{7,8}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Australia": {
        "keywords": (
            "passport",
            "driver licence",
            "driver license",
            "medicare",
            "photo card"
        ),
        "patterns": (
            COMMON_PASSPORT_PATTERN,
            r"\b[0-9]{8,10}\b"
        )
    },
    "Austria": {
        "keywords": (
            "personalausweis",
            "reisepass",
            "fuhrerschein",
            "fuhrerschein",
            "passport"
        ),
        "patterns": (
            r"\b[A-Z0-9]{8,10}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Bangladesh": {
        "keywords": (
            "national id",
            "nid",
            "passport",
            "driving licence"
        ),
        "patterns": (
            r"\b[0-9]{10}\b",
            r"\b[0-9]{13}\b",
            r"\b[0-9]{17}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Belgium": {
        "keywords": (
            "identity card",
            "carte d'identite",
            "identiteitskaart",
            "passport",
            "permis de conduire",
            "rijbewijs"
        ),
        "patterns": (
            r"\b[0-9]{11}\b",
            r"\b[A-Z0-9]{8,12}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Brazil": {
        "keywords": (
            "cpf",
            "rg",
            "passport",
            "carteira nacional"
        ),
        "patterns": (
            r"\b[0-9]{3}\.?[0-9]{3}\.?[0-9]{3}-?[0-9]{2}\b",
            r"\b[0-9]{2}\.?[0-9]{3}\.?[0-9]{3}-?[0-9X]\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Chile": {
        "keywords": (
            "run",
            "rut",
            "cedula",
            "pasaporte",
            "licencia",
            "passport"
        ),
        "patterns": (
            r"\b[0-9]{1,2}\.?[0-9]{3}\.?[0-9]{3}-?[0-9K]\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "China": {
        "keywords": (
            "resident identity card",
            "identity card",
            "passport",
            "driver license"
        ),
        "patterns": (
            r"\b[0-9]{17}[0-9X]\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Colombia": {
        "keywords": (
            "cedula",
            "passport",
            "pasaporte",
            "licencia"
        ),
        "patterns": (
            r"\b[0-9]{6,10}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Canada": {
        "keywords": (
            "passport",
            "driver's licence",
            "driver license",
            "permanent resident card",
            "provincial id"
        ),
        "patterns": (
            COMMON_PASSPORT_PATTERN,
            r"\b[A-Z0-9]{5}-?[A-Z0-9]{5}\b",
            r"\b[A-Z0-9]{6,15}\b"
        )
    },
    "Denmark": {
        "keywords": (
            "cpr",
            "pas",
            "passport",
            "korekort",
            "driver licence"
        ),
        "patterns": (
            r"\b[0-9]{6}-?[0-9]{4}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Egypt": {
        "keywords": (
            "national id",
            "identity card",
            "passport",
            "driver license"
        ),
        "patterns": (
            r"\b[0-9]{14}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "France": {
        "keywords": (
            "carte nationale",
            "passeport",
            "permis de conduire",
            "passport"
        ),
        "patterns": (
            r"\b[0-9]{12}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Ghana": {
        "keywords": (
            "ghana card",
            "national identification",
            "passport",
            "driver licence",
            "voter"
        ),
        "patterns": (
            r"\bGHA-?[0-9]{9}-?[0-9]\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Germany": {
        "keywords": (
            "personalausweis",
            "reisepass",
            "fuhrerschein",
            "führerschein",
            "passport"
        ),
        "patterns": (
            r"\b[A-Z0-9]{9}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Hong Kong": {
        "keywords": (
            "identity card",
            "hong kong identity",
            "passport",
            "driving licence"
        ),
        "patterns": (
            r"\b[A-Z]{1,2}[0-9]{6}\(?[0-9A]\)?\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "India": {
        "keywords": (
            "aadhaar",
            "aadhar",
            "passport",
            "pan",
            "voter",
            "election commission",
            "driving licence",
            "driving license"
        ),
        "patterns": (
            r"\b[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\b",
            r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
            r"\b[A-Z]{3}[0-9]{7}\b",
            r"\b[A-Z]{1}[0-9]{7}\b",
            r"\b[A-Z]{2}[0-9]{2}\s?[0-9]{11}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Ireland": {
        "keywords": (
            "passport",
            "public services card",
            "driving licence",
            "driver licence"
        ),
        "patterns": (
            r"\b[0-9]{7}[A-Z]{1,2}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Indonesia": {
        "keywords": (
            "nik",
            "ktp",
            "paspor",
            "passport",
            "sim"
        ),
        "patterns": (
            r"\b[0-9]{16}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Israel": {
        "keywords": (
            "identity card",
            "teudat zehut",
            "passport",
            "driving licence"
        ),
        "patterns": (
            r"\b[0-9]{9}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Italy": {
        "keywords": (
            "carta d'identita",
            "carta d'identità",
            "passaporto",
            "patente",
            "passport"
        ),
        "patterns": (
            r"\b[A-Z]{2}[0-9]{5}[A-Z]{2}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Japan": {
        "keywords": (
            "passport",
            "mynumber",
            "my number",
            "driver license",
            "residence card"
        ),
        "patterns": (
            r"\b[0-9]{12}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Kenya": {
        "keywords": (
            "national identity card",
            "identity card",
            "passport",
            "driving licence",
            "huduma"
        ),
        "patterns": (
            r"\b[0-9]{7,9}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Kuwait": {
        "keywords": (
            "civil id",
            "passport",
            "driving licence",
            "residence"
        ),
        "patterns": (
            r"\b[0-9]{12}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Malaysia": {
        "keywords": (
            "mykad",
            "kad pengenalan",
            "passport",
            "driving licence"
        ),
        "patterns": (
            r"\b[0-9]{6}-?[0-9]{2}-?[0-9]{4}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Morocco": {
        "keywords": (
            "cin",
            "carte nationale",
            "passport",
            "passeport",
            "permis de conduire"
        ),
        "patterns": (
            r"\b[A-Z]{1,2}[0-9]{5,7}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Mexico": {
        "keywords": (
            "curp",
            "ine",
            "pasaporte",
            "licencia",
            "passport"
        ),
        "patterns": (
            r"\b[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[A-Z0-9][0-9]\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "New Zealand": {
        "keywords": (
            "passport",
            "driver licence",
            "driver license",
            "kiwi access card"
        ),
        "patterns": (
            r"\b[A-Z]{2}[0-9]{6}\b",
            r"\b[0-9]{8,10}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Nepal": {
        "keywords": (
            "citizenship",
            "passport",
            "driving license",
            "national identity"
        ),
        "patterns": (
            r"\b[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{5}\b",
            r"\b[0-9]{8,12}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Netherlands": {
        "keywords": (
            "identiteitskaart",
            "paspoort",
            "rijbewijs",
            "passport"
        ),
        "patterns": (
            r"\b[A-Z0-9]{9}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Norway": {
        "keywords": (
            "national identity card",
            "passport",
            "pass",
            "forerkort",
            "driver licence"
        ),
        "patterns": (
            r"\b[0-9]{11}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Nigeria": {
        "keywords": (
            "nin",
            "national identification",
            "passport",
            "driver licence",
            "voter"
        ),
        "patterns": (
            r"\b[0-9]{11}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Oman": {
        "keywords": (
            "civil number",
            "resident card",
            "passport",
            "driving licence"
        ),
        "patterns": (
            r"\b[0-9]{8,10}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Pakistan": {
        "keywords": (
            "cnic",
            "national identity card",
            "nadra",
            "passport",
            "driving licence"
        ),
        "patterns": (
            r"\b[0-9]{5}-?[0-9]{7}-?[0-9]\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Poland": {
        "keywords": (
            "dowod osobisty",
            "paszport",
            "prawo jazdy",
            "passport"
        ),
        "patterns": (
            r"\b[A-Z]{3}[0-9]{6}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Portugal": {
        "keywords": (
            "cartao de cidadao",
            "passaporte",
            "carta de conducao",
            "passport"
        ),
        "patterns": (
            r"\b[0-9]{8}\b",
            r"\b[A-Z0-9]{8,12}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Qatar": {
        "keywords": (
            "qatar id",
            "qid",
            "residence permit",
            "passport",
            "driving licence"
        ),
        "patterns": (
            r"\b[0-9]{11}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Philippines": {
        "keywords": (
            "passport",
            "philippine identification",
            "philsys",
            "driver's license",
            "umid"
        ),
        "patterns": (
            r"\b[0-9]{4}-?[0-9]{4}-?[0-9]{4}-?[0-9]{4}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Saudi Arabia": {
        "keywords": (
            "national id",
            "iqama",
            "passport",
            "driving licence"
        ),
        "patterns": (
            r"\b[12][0-9]{9}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Singapore": {
        "keywords": (
            "nric",
            "fin",
            "passport",
            "driving licence",
            "identity card"
        ),
        "patterns": (
            r"\b[STFGM][0-9]{7}[A-Z]\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "South Korea": {
        "keywords": (
            "resident registration",
            "passport",
            "driver license",
            "alien registration"
        ),
        "patterns": (
            r"\b[0-9]{6}-?[1-4][0-9]{6}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "South Africa": {
        "keywords": (
            "identity document",
            "id number",
            "passport",
            "driving licence"
        ),
        "patterns": (
            r"\b[0-9]{13}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Sweden": {
        "keywords": (
            "personnummer",
            "passport",
            "pass",
            "korkort",
            "identity card"
        ),
        "patterns": (
            r"\b[0-9]{6,8}-?[0-9]{4}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Switzerland": {
        "keywords": (
            "identity card",
            "identitatskarte",
            "passport",
            "passeport",
            "driving licence"
        ),
        "patterns": (
            r"\b[A-Z][0-9]{7}\b",
            r"\b[A-Z0-9]{8,12}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Spain": {
        "keywords": (
            "dni",
            "nie",
            "pasaporte",
            "permiso de conducir",
            "passport"
        ),
        "patterns": (
            r"\b[0-9]{8}[A-Z]\b",
            r"\b[XYZ][0-9]{7}[A-Z]\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Thailand": {
        "keywords": (
            "identity card",
            "passport",
            "driving licence",
            "national id"
        ),
        "patterns": (
            r"\b[0-9]{13}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Turkey": {
        "keywords": (
            "kimlik",
            "identity card",
            "passport",
            "pasaport",
            "driving licence"
        ),
        "patterns": (
            r"\b[1-9][0-9]{10}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "Sri Lanka": {
        "keywords": (
            "nic",
            "national identity card",
            "passport",
            "driving licence"
        ),
        "patterns": (
            r"\b[0-9]{9}[VX]\b",
            r"\b[0-9]{12}\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "United Arab Emirates": {
        "keywords": (
            "emirates id",
            "passport",
            "driving licence",
            "residence"
        ),
        "patterns": (
            r"\b784-?[0-9]{4}-?[0-9]{7}-?[0-9]\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "United Kingdom": {
        "keywords": (
            "passport",
            "driving licence",
            "biometric residence permit",
            "national insurance"
        ),
        "patterns": (
            r"\b[A-CEGHJ-PR-TW-Z]{2}[0-9]{6}[A-D]\b",
            COMMON_PASSPORT_PATTERN
        )
    },
    "United States": {
        "keywords": (
            "passport",
            "driver license",
            "driver's license",
            "state id",
            "identity card"
        ),
        "patterns": (
            r"\b[0-9]{9}\b",
            r"\b[A-Z][0-9]{7,8}\b",
            r"\b[A-Z0-9]{6,13}\b"
        )
    },
    "Vietnam": {
        "keywords": (
            "citizen identity",
            "identity card",
            "passport",
            "driver license",
            "can cuoc"
        ),
        "patterns": (
            r"\b[0-9]{9}\b",
            r"\b[0-9]{12}\b",
            COMMON_PASSPORT_PATTERN
        )
    }
}


PDF_HEADER = b"%PDF-"
MAX_GOVERNMENT_ID_SIZE = 5 * 1024 * 1024
MIN_EXTRACTED_TEXT_LENGTH = 30
MAX_OCR_PAGES = 2


def normalize_document_text(text):
    text = text.lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def read_pdf_upload(file_storage):
    file_storage.stream.seek(0)
    data = file_storage.stream.read(MAX_GOVERNMENT_ID_SIZE + 1)
    file_storage.stream.seek(0)

    if len(data) > MAX_GOVERNMENT_ID_SIZE:
        return None, "Government ID PDF must be 5 MB or smaller."

    if not data.startswith(PDF_HEADER):
        return None, "Government ID must be a valid PDF file."

    return data, None


def extract_pdf_text(data):
    if PdfReader is None:
        return "", "pypdf is not installed."

    try:
        reader = PdfReader(BytesIO(data))
    except Exception:
        return "", "The PDF could not be read."

    page_text = []

    for page in reader.pages[:MAX_OCR_PAGES]:
        try:
            page_text.append(
                page.extract_text() or ""
            )
        except Exception:
            continue

    return normalize_document_text(" ".join(page_text)), ""


def extract_pdf_text_with_ocr(data):
    if convert_from_bytes is None or pytesseract is None:
        return "", "OCR dependencies are not installed."

    try:
        images = convert_from_bytes(
            data,
            dpi=200,
            first_page=1,
            last_page=MAX_OCR_PAGES
        )
    except Exception:
        return "", "OCR could not render the PDF pages."

    ocr_text = []

    for image in images:
        try:
            ocr_text.append(
                pytesseract.image_to_string(image)
            )
        except Exception:
            continue

    return normalize_document_text(" ".join(ocr_text)), ""


def get_government_id_text(data):
    text, pdf_error = extract_pdf_text(data)

    if len(text) >= MIN_EXTRACTED_TEXT_LENGTH:
        return text, "pdf_text", ""

    ocr_text, ocr_error = extract_pdf_text_with_ocr(data)

    if len(ocr_text) >= MIN_EXTRACTED_TEXT_LENGTH:
        return ocr_text, "ocr", ""

    if PdfReader is None or convert_from_bytes is None or pytesseract is None:
        return (
            "",
            "",
            "Government ID validation requires pypdf, pdf2image, "
            "pytesseract, Poppler, and Tesseract OCR to be installed."
        )

    if pdf_error and ocr_error:
        return "", "", f"{pdf_error} {ocr_error}"

    return (
        "",
        "",
        "Could not read enough text from this PDF. Please upload a clearer "
        "government ID scan."
    )


def match_government_id(country, text):
    rules = COUNTRY_ID_RULES.get(country)

    if not rules:
        return False, "unsupported country", ""

    keyword = next(
        (
            value
            for value in rules["keywords"]
            if value in text
        ),
        ""
    )

    if not keyword:
        return False, "no supported ID type label found", ""

    uppercase_text = text.upper()
    pattern = next(
        (
            value
            for value in rules["patterns"]
            if re.search(value, uppercase_text)
        ),
        ""
    )

    if not pattern:
        return False, "no valid ID number format found", ""

    return True, keyword, pattern


def validate_government_id(file_storage, country):
    if not file_storage or not file_storage.filename:
        return {
            "valid": False,
            "error": "Please upload your government ID PDF.",
            "method": "",
            "notes": ""
        }

    safe_filename = secure_filename(file_storage.filename)

    if not safe_filename or "." not in safe_filename:
        return {
            "valid": False,
            "error": "Government ID must be a PDF file.",
            "method": "",
            "notes": ""
        }

    extension = safe_filename.rsplit(
        ".",
        1
    )[1].lower()

    if extension != "pdf":
        return {
            "valid": False,
            "error": "Government ID must be uploaded as a PDF.",
            "method": "",
            "notes": ""
        }

    if file_storage.mimetype not in (
        "application/pdf",
        "application/x-pdf",
        "application/octet-stream"
    ):
        return {
            "valid": False,
            "error": "Government ID must be a PDF file.",
            "method": "",
            "notes": ""
        }

    data, error = read_pdf_upload(file_storage)

    if error:
        return {
            "valid": False,
            "error": error,
            "method": "",
            "notes": ""
        }

    text, method, text_error = get_government_id_text(data)

    if text_error:
        return {
            "valid": False,
            "error": text_error,
            "method": method,
            "notes": ""
        }

    is_match, match_reason, matched_pattern = match_government_id(
        country,
        text
    )

    if not is_match:
        return {
            "valid": False,
            "error": (
                "Uploaded PDF does not look like a valid supported "
                f"government ID for {country}: {match_reason}."
            ),
            "method": method,
            "notes": match_reason
        }

    return {
        "valid": True,
        "error": "",
        "method": method,
        "notes": (
            f"Matched '{match_reason}' with pattern {matched_pattern}."
        )
    }


def save_government_id(file_storage):
    upload_folder = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        "government_ids"
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    unique_filename = (
        f"government_id_{uuid.uuid4().hex}.pdf"
    )

    file_path = os.path.join(
        upload_folder,
        unique_filename
    )

    file_storage.save(file_path)

    return os.path.join(
        "government_ids",
        unique_filename
    )


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "tenant")
        country = request.form.get("country", "").strip()
        government_id = request.files.get("government_id")

        if not name or not email or not password:
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("auth.register"))

        if country not in COUNTRY_ID_RULES:
            flash("Please select a supported country.", "danger")
            return redirect(url_for("auth.register"))

        id_validation = validate_government_id(
            government_id,
            country
        )

        if not id_validation["valid"]:
            flash(id_validation["error"], "danger")
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
        government_id_file = save_government_id(
            government_id
        )

        execute_query("""
            INSERT INTO users
            (
                name,
                email,
                phone,
                password,
                role,
                country,
                government_id_file,
                government_id_verified,
                government_id_status,
                government_id_validation_method,
                government_id_validation_notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s, %s, %s)
        """, (
            name,
            email,
            phone,
            hashed_password,
            role,
            country,
            government_id_file,
            "auto_verified",
            id_validation["method"],
            id_validation["notes"]
        ))

        flash("Registration successful. Please login.", "success")

        return redirect(url_for("auth.login"))

    return render_template(
        "register.html",
        countries=sorted(COUNTRY_ID_RULES.keys())
    )


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

    # Not logged in: send to the login page
    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )


    if request.method == "POST":

        role = request.form.get("role")


        # Only these two roles can be self-selected
        if role not in ["tenant", "owner"]:

            flash(
                "Please select Tenant or Owner.",
                "danger"
            )

            return redirect(
                url_for("auth.select_role")
            )


        # Remember the chosen role for this session
        session["role"] = role


        # Go to the matching dashboard
        if role == "tenant":

            return redirect(
                url_for("tenant.dashboard")
            )


        if role == "owner":

            return redirect(
                url_for("owner.dashboard")
            )


    return render_template("select_role.html")
