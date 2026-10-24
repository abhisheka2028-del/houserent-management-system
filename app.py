import os
import time
import uuid
import secrets
from functools import wraps
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g, jsonify, abort, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import config_by_name
from database.init_db import get_db_connection, init_db, run_migrations

# --------------------------------------------------------------------------
# In-memory Rate Limiter for Login Protection
# --------------------------------------------------------------------------
LOGIN_ATTEMPTS = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 300  # 5 minutes

def is_login_rate_limited(ip_address):
    """Check if the IP address has exceeded maximum login attempts."""
    now = time.time()
    attempts = LOGIN_ATTEMPTS.get(ip_address, [])
    # Filter attempts within lockout window
    recent_attempts = [t for t in attempts if now - t < LOCKOUT_DURATION_SECONDS]
    LOGIN_ATTEMPTS[ip_address] = recent_attempts
    return len(recent_attempts) >= MAX_LOGIN_ATTEMPTS

def record_failed_login(ip_address):
    """Record a failed login attempt timestamp for the IP address."""
    now = time.time()
    attempts = LOGIN_ATTEMPTS.get(ip_address, [])
    attempts.append(now)
    LOGIN_ATTEMPTS[ip_address] = attempts

def clear_login_attempts(ip_address):
    """Clear failed login attempts upon successful authentication."""
    LOGIN_ATTEMPTS.pop(ip_address, None)


# --------------------------------------------------------------------------
# Image Validation and Storage Helpers
# --------------------------------------------------------------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    """Validate file extension against allowed image types."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image_header(stream):
    """Inspect file header magic bytes to prevent fake extensions or executable uploads."""
    header = stream.read(16)
    stream.seek(0)
    if not header:
        return False
    # PNG: \x89PNG\r\n\x1a\n
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    # JPEG: \xff\xd8\xff
    if header.startswith(b"\xff\xd8\xff"):
        return True
    # WebP: RIFF....WEBP
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return True
    return False

def save_uploaded_property_image(file_storage, upload_folder):
    """Validate and securely save an uploaded property image with a UUID filename."""
    if not file_storage or file_storage.filename == "":
        return None

    if not allowed_file(file_storage.filename):
        raise ValueError("Invalid image file format. Only PNG, JPG, JPEG, and WebP are allowed.")

    if not validate_image_header(file_storage.stream):
        raise ValueError("The uploaded file content does not match a valid image format.")

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    safe_name = f"prop_{uuid.uuid4().hex}.{ext}"
    dest_path = Path(upload_folder) / safe_name
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    file_storage.save(str(dest_path))
    return safe_name


def create_app(config_name=None):
    """Application factory for HouseRent."""
    if config_name is None:
        # Determine environment: check FLASK_CONFIG, FLASK_ENV, ENVIRONMENT, or Render detection
        env_choice = (
            os.environ.get("FLASK_CONFIG")
            or os.environ.get("FLASK_ENV")
            or os.environ.get("ENVIRONMENT")
        )
        if env_choice:
            config_name = env_choice.lower()
        elif os.environ.get("RENDER"):
            config_name = "production"
        else:
            config_name = "development"

        if config_name not in config_by_name:
            config_name = "default"

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Dynamic environment variable overrides: sensitive configuration read from environment
    if os.environ.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
    if os.environ.get("DATABASE_PATH"):
        app.config["DATABASE_PATH"] = os.environ["DATABASE_PATH"]
    if os.environ.get("UPLOAD_FOLDER"):
        app.config["UPLOAD_FOLDER"] = os.environ["UPLOAD_FOLDER"]
    if os.environ.get("SESSION_COOKIE_SECURE") is not None:
        app.config["SESSION_COOKIE_SECURE"] = os.environ["SESSION_COOKIE_SECURE"].lower() in ("true", "1", "yes")

    # Ensure Flask debug mode is strictly disabled in production
    flask_debug = os.environ.get("FLASK_DEBUG", "").lower()
    if config_name == "production" or os.environ.get("RENDER") or flask_debug in ("0", "false", "no"):
        app.config["DEBUG"] = False

    # Ensure database parent directory and uploads directory exist
    db_path = app.config.get("DATABASE_PATH")
    if db_path and db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        # Initialize schema and run migrations if database does not exist
        if not Path(db_path).exists():
            init_db(db_path)
            # Safe initial seed for newly created database on first boot if AUTO_SEED_DATA is set
            if os.environ.get("AUTO_SEED_DATA", "false").lower() in ("true", "1"):
                try:
                    from database.seed_data import seed_db
                    seed_db(db_path)
                except Exception as e:
                    app.logger.warning(f"Could not seed initial demo data: {e}")
        else:
            # Run schema migrations on existing database to preserve data
            conn = get_db_connection(db_path)
            run_migrations(conn)
            conn.close()

    upload_folder = app.config.get("UPLOAD_FOLDER")
    if upload_folder:
        Path(upload_folder).mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # Database Connection Lifecycle
    # -------------------------------------------------------------
    def get_db():
        if "db" not in g:
            g.db = get_db_connection(app.config["DATABASE_PATH"])
        return g.db

    @app.teardown_appcontext
    def close_db(exception=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    # -------------------------------------------------------------
    # CSRF & Security Handlers
    # -------------------------------------------------------------
    @app.before_request
    def handle_security_and_csrf():
        # Ensure a secure CSRF token exists in the user session
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)

        # CSRF check for state-changing HTTP methods
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if not app.config.get("TESTING", False):
                token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
                if not token or token != session.get("csrf_token"):
                    abort(400, description="Invalid or missing CSRF token. Please refresh the page and try again.")

    @app.context_processor
    def inject_template_globals():
        role = session.get("role", "")
        return {
            "csrf_token": session.get("csrf_token", ""),
            "current_user": {
                "is_authenticated": "user_id" in session,
                "id": session.get("user_id"),
                "username": session.get("username"),
                "full_name": session.get("full_name"),
                "role": role,
                "is_admin": role == "admin",
                "is_owner": role == "owner",
                "is_renter": role in ("renter", "tenant")
            }
        }

    # -------------------------------------------------------------
    # Template Filter for Property Images (Uploaded or Fallback)
    # -------------------------------------------------------------
    @app.template_filter("property_image")
    def property_image_filter(house):
        if not house:
            return url_for("static", filename="images/default_property.jpg")

        # Check uploaded filename first
        img_fn = house["image_filename"] if "image_filename" in house.keys() else ""
        if img_fn:
            upload_dir = app.config.get("UPLOAD_FOLDER", "")
            if upload_dir and (Path(upload_dir) / img_fn).exists():
                return url_for("uploaded_file", filename=img_fn)

        # Check external image URL
        img_url = house["image_url"] if "image_url" in house.keys() else ""
        if img_url and img_url.strip():
            return img_url.strip()

        return url_for("static", filename="images/default_property.jpg")

    # -------------------------------------------------------------
    # Authentication & Authorization Decorators
    # -------------------------------------------------------------
    def login_required(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("login", next=request.path))
            return view_func(*args, **kwargs)
        return wrapper

    def admin_required(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in as an administrator to access this page.", "warning")
                return redirect(url_for("login", next=request.path))
            if session.get("role") != "admin":
                flash("Access denied. Administrator privileges are required.", "danger")
                return redirect(url_for("index"))
            return view_func(*args, **kwargs)
        return wrapper

    def owner_or_admin_required(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to manage property listings.", "warning")
                return redirect(url_for("login", next=request.path))
            if request.path.startswith("/admin/") and session.get("role") != "admin":
                flash("Access denied. Administrator privileges are required.", "danger")
                return redirect(url_for("index"))
            if session.get("role") not in ("owner", "admin"):
                flash("Access denied. Property owner or administrator privileges required.", "danger")
                return redirect(url_for("index"))
            return view_func(*args, **kwargs)
        return wrapper

    def renter_required(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in as a renter to proceed.", "warning")
                return redirect(url_for("login", next=request.path))
            if session.get("role") not in ("renter", "tenant"):
                flash("Only registered tenants/renters can perform this action.", "info")
                return redirect(url_for("index"))
            return view_func(*args, **kwargs)
        return wrapper

    # -------------------------------------------------------------
    # Static & Upload Routes
    # -------------------------------------------------------------
    @app.route("/uploads/<filename>")
    def uploaded_file(filename):
        """Serve user-uploaded property images securely."""
        safe_name = secure_filename(filename)
        upload_dir = app.config.get("UPLOAD_FOLDER")
        if not upload_dir or not (Path(upload_dir) / safe_name).exists():
            return redirect(url_for("static", filename="images/default_property.jpg"))
        return send_from_directory(upload_dir, safe_name)

    # -------------------------------------------------------------
    # Public & Informational Routes
    # -------------------------------------------------------------
    @app.route("/")
    def index():
        """Home page with hero section, live statistics, and featured available properties."""
        db = get_db()
        cursor = db.cursor()

        # Fetch up to 6 featured available houses
        cursor.execute(
            """
            SELECT h.*, u.full_name as owner_name 
            FROM houses h 
            JOIN users u ON h.created_by = u.id 
            WHERE h.is_available = 1 
            ORDER BY h.id DESC 
            LIMIT 6
            """
        )
        featured_houses = cursor.fetchall()

        # Real statistics calculated from stored database records
        cursor.execute("SELECT COUNT(*) FROM houses WHERE is_available = 1")
        available_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM houses")
        total_houses_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role IN ('tenant', 'renter')")
        tenants_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'owner'")
        owners_count = cursor.fetchone()[0]

        return render_template(
            "index.html",
            houses=featured_houses,
            stats={
                "available": available_count,
                "total": total_houses_count,
                "tenants": tenants_count,
                "owners": owners_count
            }
        )

    @app.route("/houses")
    def houses():
        """Browse all properties with multi-criteria search and filtering."""
        location_query = request.args.get("location", "").strip()
        max_rent = request.args.get("max_rent", "").strip()
        bedrooms = request.args.get("bedrooms", "").strip()
        property_type = request.args.get("property_type", "").strip()
        furnishing = request.args.get("furnishing", "").strip()
        availability = request.args.get("availability", "all").strip()
        sort_by = request.args.get("sort", "newest").strip()

        query = """
            SELECT h.*, u.full_name as owner_name 
            FROM houses h 
            JOIN users u ON h.created_by = u.id 
            WHERE 1=1
        """
        params = []

        if location_query:
            query += " AND (h.location LIKE ? OR h.title LIKE ?)"
            params.append(f"%{location_query}%")
            params.append(f"%{location_query}%")

        if max_rent:
            try:
                max_rent_val = float(max_rent)
                query += " AND h.rent <= ?"
                params.append(max_rent_val)
            except ValueError:
                pass

        if bedrooms and bedrooms != "any":
            try:
                bedrooms_val = int(bedrooms)
                query += " AND h.bedrooms = ?"
                params.append(bedrooms_val)
            except ValueError:
                pass

        if property_type and property_type != "any":
            query += " AND h.property_type = ?"
            params.append(property_type)

        if furnishing and furnishing != "any":
            query += " AND h.furnishing = ?"
            params.append(furnishing)

        if availability == "available":
            query += " AND h.is_available = 1"
        elif availability == "rented":
            query += " AND h.is_available = 0"

        # Sorting
        if sort_by == "price_asc":
            query += " ORDER BY h.rent ASC"
        elif sort_by == "price_desc":
            query += " ORDER BY h.rent DESC"
        else:
            query += " ORDER BY h.id DESC"

        db = get_db()
        cursor = db.cursor()
        cursor.execute(query, params)
        all_houses = cursor.fetchall()

        # Check saved properties for logged in renter
        saved_house_ids = set()
        if "user_id" in session:
            cursor.execute("SELECT house_id FROM saved_properties WHERE user_id = ?", (session["user_id"],))
            saved_house_ids = {row[0] for row in cursor.fetchall()}

        return render_template(
            "houses.html",
            houses=all_houses,
            saved_house_ids=saved_house_ids,
            filters={
                "location": location_query,
                "max_rent": max_rent,
                "bedrooms": bedrooms,
                "property_type": property_type,
                "furnishing": furnishing,
                "availability": availability,
                "sort": sort_by
            }
        )

    @app.route("/houses/<int:house_id>")
    def house_detail(house_id):
        """Detail page for a specific property listing."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT h.*, u.full_name as owner_name, u.email as owner_email, u.phone as owner_phone
            FROM houses h 
            JOIN users u ON h.created_by = u.id 
            WHERE h.id = ?
            """,
            (house_id,)
        )
        house = cursor.fetchone()
        if not house:
            abort(404, description="House listing not found.")

        # Check if the logged-in tenant already requested this house
        existing_request = None
        is_saved = False
        if "user_id" in session:
            cursor.execute(
                "SELECT * FROM rental_requests WHERE house_id = ? AND tenant_id = ? ORDER BY id DESC LIMIT 1",
                (house_id, session["user_id"])
            )
            existing_request = cursor.fetchone()

            cursor.execute(
                "SELECT id FROM saved_properties WHERE user_id = ? AND house_id = ?",
                (session["user_id"], house_id)
            )
            is_saved = cursor.fetchone() is not None

        return render_template(
            "house_detail.html",
            house=house,
            existing_request=existing_request,
            is_saved=is_saved
        )

    @app.route("/houses/<int:house_id>/save", methods=["POST"])
    @login_required
    def toggle_save_property(house_id):
        """Bookmark or un-bookmark a property for quick reference."""
        user_id = session["user_id"]
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT id FROM saved_properties WHERE user_id = ? AND house_id = ?", (user_id, house_id))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("DELETE FROM saved_properties WHERE id = ?", (existing["id"],))
            db.commit()
            flash("Property removed from saved listings.", "info")
        else:
            cursor.execute("INSERT INTO saved_properties (user_id, house_id) VALUES (?, ?)", (user_id, house_id))
            db.commit()
            flash("Property added to your saved listings!", "success")

        next_page = request.referrer or url_for("house_detail", house_id=house_id)
        return redirect(next_page)

    @app.route("/houses/<int:house_id>/request", methods=["POST"])
    @login_required
    def submit_rental_request(house_id):
        """Submit a rental inquiry/application for a property."""
        if session.get("role") not in ("tenant", "renter"):
            flash("Only registered tenants or renters can submit rental inquiries.", "danger")
            return redirect(url_for("house_detail", house_id=house_id))

        move_in_date = request.form.get("move_in_date", "").strip()
        duration_months = request.form.get("duration_months", "").strip()
        message = request.form.get("message", "").strip()

        if not move_in_date:
            flash("Please specify an intended move-in date.", "danger")
            return redirect(url_for("house_detail", house_id=house_id))

        try:
            duration_val = int(duration_months)
            if duration_val <= 0:
                raise ValueError
        except ValueError:
            flash("Rental duration must be a positive number of months.", "danger")
            return redirect(url_for("house_detail", house_id=house_id))

        db = get_db()
        cursor = db.cursor()

        # Check if house exists and is available
        cursor.execute("SELECT is_available, created_by FROM houses WHERE id = ?", (house_id,))
        house = cursor.fetchone()
        if not house:
            abort(404, description="House listing not found.")

        if house["is_available"] != 1:
            flash("This house is currently not available for rental applications.", "warning")
            return redirect(url_for("house_detail", house_id=house_id))

        # Check for duplicate pending request
        cursor.execute(
            "SELECT id FROM rental_requests WHERE house_id = ? AND tenant_id = ? AND status = 'Pending'",
            (house_id, session["user_id"])
        )
        if cursor.fetchone():
            flash("You already have an active pending inquiry for this property.", "info")
            return redirect(url_for("my_requests"))

        cursor.execute(
            """
            INSERT INTO rental_requests (house_id, tenant_id, move_in_date, duration_months, message, status)
            VALUES (?, ?, ?, ?, ?, 'Pending')
            """,
            (house_id, session["user_id"], move_in_date, duration_val, message)
        )
        db.commit()

        flash("Rental request submitted successfully! The property manager will review your request.", "success")
        return redirect(url_for("my_requests"))

    @app.route("/about")
    def about():
        """About the HouseRent platform page."""
        return render_template("about.html")

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        """Contact and inquiries page."""
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            subject = request.form.get("subject", "").strip()
            message = request.form.get("message", "").strip()

            if not name or not email or not message:
                flash("Please fill in all required fields.", "danger")
                return render_template("contact.html")

            flash("Thank you for reaching out! Our support team will get back to you shortly.", "success")
            return redirect(url_for("contact"))

        return render_template("contact.html")

    # -------------------------------------------------------------
    # Authentication & User Management Routes
    # -------------------------------------------------------------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        """User registration with role selection (Renter or Property Owner)."""
        if "user_id" in session:
            return redirect(url_for("index"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            full_name = request.form.get("full_name", "").strip()
            phone = request.form.get("phone", "").strip()
            selected_role = request.form.get("role", "renter").strip().lower()

            if selected_role not in ("renter", "owner", "tenant"):
                selected_role = "renter"

            # Validation
            if not username or not email or not password or not full_name:
                flash("Please fill in all mandatory fields.", "danger")
                return render_template("register.html")

            if len(username) < 3:
                flash("Username must be at least 3 characters long.", "danger")
                return render_template("register.html")

            if "@" not in email or "." not in email:
                flash("Please enter a valid email address.", "danger")
                return render_template("register.html")

            if len(password) < 6:
                flash("Password must be at least 6 characters long.", "danger")
                return render_template("register.html")

            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return render_template("register.html")

            db = get_db()
            cursor = db.cursor()

            # Check for existing username or email
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            if cursor.fetchone():
                flash("A user account with this username or email already exists.", "danger")
                return render_template("register.html")

            pwd_hash = generate_password_hash(password)
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, full_name, phone, role)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (username, email, pwd_hash, full_name, phone, selected_role)
            )
            db.commit()

            flash("Registration successful! You can now log in with your credentials.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """User login with rate limiting and secure session management."""
        if "user_id" in session:
            return redirect(url_for("index"))

        client_ip = request.remote_addr or "127.0.0.1"

        if request.method == "POST":
            # Check rate limiting
            if is_login_rate_limited(client_ip):
                flash("Too many failed login attempts. Please wait 5 minutes before trying again.", "danger")
                return render_template("login.html"), 429

            username_or_email = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if not username_or_email or not password:
                flash("Please provide both username/email and password.", "danger")
                return render_template("login.html")

            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ? OR email = ?",
                (username_or_email, username_or_email.lower())
            )
            user = cursor.fetchone()

            if user and check_password_hash(user["password_hash"], password):
                # Successful login: clear failed attempts and regenerate session
                clear_login_attempts(client_ip)
                csrf_token = session.get("csrf_token")
                session.clear()
                session["csrf_token"] = csrf_token or secrets.token_hex(32)

                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["full_name"] = user["full_name"]
                session["role"] = user["role"]

                flash(f"Welcome back, {user['full_name']}!", "success")
                next_page = request.args.get("next")
                if next_page and next_page.startswith("/"):
                    return redirect(next_page)

                if user["role"] == "admin":
                    return redirect(url_for("dashboard"))
                elif user["role"] == "owner":
                    return redirect(url_for("owner_dashboard"))
                else:
                    return redirect(url_for("my_requests"))
            else:
                record_failed_login(client_ip)
                flash("Invalid username or password. Please try again.", "danger")

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        """Clear user session and log out."""
        session.clear()
        flash("You have been successfully logged out.", "info")
        return redirect(url_for("index"))

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        """User profile management and password update."""
        user_id = session["user_id"]
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            abort(404, description="User record not found.")

        if request.method == "POST":
            action = request.form.get("action")

            if action == "update_info":
                full_name = request.form.get("full_name", "").strip()
                phone = request.form.get("phone", "").strip()
                email = request.form.get("email", "").strip().lower()

                if not full_name or not email:
                    flash("Full name and email are required.", "danger")
                    return render_template("profile.html", user=user)

                # Check if email is already used by another user
                cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id))
                if cursor.fetchone():
                    flash("This email address is already in use by another account.", "danger")
                    return render_template("profile.html", user=user)

                cursor.execute(
                    "UPDATE users SET full_name = ?, phone = ?, email = ? WHERE id = ?",
                    (full_name, phone, email, user_id)
                )
                db.commit()
                session["full_name"] = full_name
                flash("Profile details updated successfully!", "success")
                return redirect(url_for("profile"))

            elif action == "change_password":
                current_pwd = request.form.get("current_password", "")
                new_pwd = request.form.get("new_password", "")
                confirm_pwd = request.form.get("confirm_password", "")

                if not check_password_hash(user["password_hash"], current_pwd):
                    flash("Current password is incorrect.", "danger")
                    return render_template("profile.html", user=user)

                if len(new_pwd) < 6:
                    flash("New password must be at least 6 characters long.", "danger")
                    return render_template("profile.html", user=user)

                if new_pwd != confirm_pwd:
                    flash("New passwords do not match.", "danger")
                    return render_template("profile.html", user=user)

                new_hash = generate_password_hash(new_pwd)
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
                db.commit()
                flash("Password updated successfully!", "success")
                return redirect(url_for("profile"))

        return render_template("profile.html", user=user)

    # -------------------------------------------------------------
    # Renter Dashboard & Inquiries
    # -------------------------------------------------------------
    @app.route("/my-requests")
    @app.route("/renter/dashboard")
    @login_required
    def my_requests():
        """Renter portal: view submitted inquiries, statuses, and saved properties."""
        user_id = session["user_id"]
        db = get_db()
        cursor = db.cursor()

        # Inquiries submitted by this renter
        cursor.execute(
            """
            SELECT r.*, h.title as house_title, h.location as house_location, h.rent as house_rent,
                   h.image_url as house_image, h.image_filename, u.full_name as owner_name,
                   u.email as owner_email, u.phone as owner_phone
            FROM rental_requests r
            JOIN houses h ON r.house_id = h.id
            JOIN users u ON h.created_by = u.id
            WHERE r.tenant_id = ?
            ORDER BY r.id DESC
            """,
            (user_id,)
        )
        requests_list = cursor.fetchall()

        # Saved properties
        cursor.execute(
            """
            SELECT h.*, s.created_at as saved_at, u.full_name as owner_name
            FROM saved_properties s
            JOIN houses h ON s.house_id = h.id
            JOIN users u ON h.created_by = u.id
            WHERE s.user_id = ?
            ORDER BY s.id DESC
            """,
            (user_id,)
        )
        saved_list = cursor.fetchall()

        # Recommended properties: available houses that the renter hasn't requested yet
        cursor.execute(
            """
            SELECT h.*, u.full_name as owner_name
            FROM houses h
            JOIN users u ON h.created_by = u.id
            WHERE h.is_available = 1
              AND h.id NOT IN (SELECT house_id FROM rental_requests WHERE tenant_id = ?)
            ORDER BY h.id DESC
            LIMIT 3
            """,
            (user_id,)
        )
        recommended_houses = cursor.fetchall()

        stats = {
            "total_requests": len(requests_list),
            "pending": sum(1 for r in requests_list if r["status"] == "Pending"),
            "approved": sum(1 for r in requests_list if r["status"] == "Approved"),
            "saved_count": len(saved_list)
        }

        return render_template(
            "renter_dashboard.html",
            requests=requests_list,
            saved_houses=saved_list,
            recommended_houses=recommended_houses,
            stats=stats
        )

    # -------------------------------------------------------------
    # Owner Dashboard & Property Operations
    # -------------------------------------------------------------
    @app.route("/owner/dashboard")
    @owner_or_admin_required
    def owner_dashboard():
        """Landlord/Owner dashboard for property and inquiry management."""
        user_id = session["user_id"]
        is_admin = session.get("role") == "admin"
        db = get_db()
        cursor = db.cursor()

        # Owner's properties (or all properties if admin accessing)
        if is_admin:
            cursor.execute("SELECT * FROM houses ORDER BY id DESC")
        else:
            cursor.execute("SELECT * FROM houses WHERE created_by = ? ORDER BY id DESC", (user_id,))
        properties = cursor.fetchall()

        # Inquiries for owner's properties
        if is_admin:
            cursor.execute(
                """
                SELECT r.*, h.title as house_title, h.rent as house_rent,
                       u.full_name as tenant_name, u.email as tenant_email, u.phone as tenant_phone
                FROM rental_requests r
                JOIN houses h ON r.house_id = h.id
                JOIN users u ON r.tenant_id = u.id
                ORDER BY r.id DESC
                """
            )
        else:
            cursor.execute(
                """
                SELECT r.*, h.title as house_title, h.rent as house_rent,
                       u.full_name as tenant_name, u.email as tenant_email, u.phone as tenant_phone
                FROM rental_requests r
                JOIN houses h ON r.house_id = h.id
                JOIN users u ON r.tenant_id = u.id
                WHERE h.created_by = ?
                ORDER BY r.id DESC
                """,
                (user_id,)
            )
        inquiries = cursor.fetchall()

        stats = {
            "total_properties": len(properties),
            "available": sum(1 for p in properties if p["is_available"] == 1),
            "rented": sum(1 for p in properties if p["is_available"] == 0),
            "total_inquiries": len(inquiries),
            "pending_inquiries": sum(1 for i in inquiries if i["status"] == "Pending")
        }

        return render_template(
            "owner_dashboard.html",
            properties=properties,
            inquiries=inquiries,
            stats=stats
        )

    @app.route("/owner/houses/add", methods=["GET", "POST"])
    @app.route("/admin/houses/add", methods=["GET", "POST"])
    @owner_or_admin_required
    def add_house():
        """Create a new property listing with optional image upload."""
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            location = request.form.get("location", "").strip()
            rent = request.form.get("rent", "").strip()
            security_deposit = request.form.get("security_deposit", "").strip()
            property_type = request.form.get("property_type", "Apartment").strip()
            furnishing = request.form.get("furnishing", "Semi-Furnished").strip()
            amenities = request.form.get("amenities", "").strip()
            bedrooms = request.form.get("bedrooms", "").strip()
            bathrooms = request.form.get("bathrooms", "").strip()
            description = request.form.get("description", "").strip()
            image_url = request.form.get("image_url", "").strip()
            is_available = 1 if request.form.get("is_available") == "1" else 0

            # Mandatory validation
            if not title or not location or not rent or not bedrooms or not bathrooms or not description:
                flash("Please fill in all mandatory fields.", "danger")
                return render_template("add_house.html")

            try:
                rent_val = float(rent)
                bedrooms_val = int(bedrooms)
                bathrooms_val = int(bathrooms)
                deposit_val = float(security_deposit) if security_deposit else rent_val * 2
                if rent_val <= 0 or bedrooms_val <= 0 or bathrooms_val <= 0 or deposit_val < 0:
                    raise ValueError
            except ValueError:
                flash("Rent, bedrooms, and bathrooms must be positive numbers.", "danger")
                return render_template("add_house.html")

            # Handle image file upload
            image_filename = ""
            if "image_file" in request.files:
                file = request.files["image_file"]
                if file and file.filename != "":
                    try:
                        image_filename = save_uploaded_property_image(file, app.config["UPLOAD_FOLDER"])
                    except ValueError as err:
                        flash(str(err), "danger")
                        return render_template("add_house.html")

            if not image_filename and not image_url:
                image_url = "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&w=800&q=80"

            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                """
                INSERT INTO houses (
                    title, location, rent, security_deposit, property_type, furnishing,
                    amenities, bedrooms, bathrooms, description, is_available, image_url,
                    image_filename, created_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title, location, rent_val, deposit_val, property_type, furnishing,
                    amenities, bedrooms_val, bathrooms_val, description, is_available,
                    image_url, image_filename, session["user_id"]
                )
            )
            db.commit()

            flash("House listing created successfully!", "success")
            if session.get("role") == "owner":
                return redirect(url_for("owner_dashboard"))
            return redirect(url_for("houses"))

        return render_template("add_house.html")

    @app.route("/owner/houses/<int:house_id>/edit", methods=["GET", "POST"])
    @app.route("/admin/houses/<int:house_id>/edit", methods=["GET", "POST"])
    @owner_or_admin_required
    def edit_house(house_id):
        """Edit an existing property listing."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM houses WHERE id = ?", (house_id,))
        house = cursor.fetchone()
        if not house:
            abort(404, description="House listing not found.")

        # Ensure owners can only edit their own listings (admins can edit any)
        if session.get("role") != "admin" and house["created_by"] != session["user_id"]:
            flash("You do not have permission to edit this property listing.", "danger")
            return redirect(url_for("owner_dashboard"))

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            location = request.form.get("location", "").strip()
            rent = request.form.get("rent", "").strip()
            security_deposit = request.form.get("security_deposit", "").strip()
            property_type = request.form.get("property_type", "Apartment").strip()
            furnishing = request.form.get("furnishing", "Semi-Furnished").strip()
            amenities = request.form.get("amenities", "").strip()
            bedrooms = request.form.get("bedrooms", "").strip()
            bathrooms = request.form.get("bathrooms", "").strip()
            description = request.form.get("description", "").strip()
            image_url = request.form.get("image_url", "").strip()
            is_available = 1 if request.form.get("is_available") == "1" else 0

            if not title or not location or not rent or not bedrooms or not bathrooms or not description:
                flash("Please fill in all mandatory fields.", "danger")
                return render_template("edit_house.html", house=house)

            try:
                rent_val = float(rent)
                bedrooms_val = int(bedrooms)
                bathrooms_val = int(bathrooms)
                deposit_val = float(security_deposit) if security_deposit else rent_val * 2
                if rent_val <= 0 or bedrooms_val <= 0 or bathrooms_val <= 0 or deposit_val < 0:
                    raise ValueError
            except ValueError:
                flash("Rent, bedrooms, and bathrooms must be positive numbers.", "danger")
                return render_template("edit_house.html", house=house)

            # Check if a new image was uploaded
            image_filename = house["image_filename"]
            if "image_file" in request.files:
                file = request.files["image_file"]
                if file and file.filename != "":
                    try:
                        image_filename = save_uploaded_property_image(file, app.config["UPLOAD_FOLDER"])
                    except ValueError as err:
                        flash(str(err), "danger")
                        return render_template("edit_house.html", house=house)

            cursor.execute(
                """
                UPDATE houses
                SET title = ?, location = ?, rent = ?, security_deposit = ?, property_type = ?,
                    furnishing = ?, amenities = ?, bedrooms = ?, bathrooms = ?, description = ?,
                    is_available = ?, image_url = ?, image_filename = ?
                WHERE id = ?
                """,
                (
                    title, location, rent_val, deposit_val, property_type, furnishing,
                    amenities, bedrooms_val, bathrooms_val, description, is_available,
                    image_url, image_filename, house_id
                )
            )
            db.commit()

            flash("House listing updated successfully!", "success")
            return redirect(url_for("house_detail", house_id=house_id))

        return render_template("edit_house.html", house=house)

    @app.route("/owner/houses/<int:house_id>/delete", methods=["POST"])
    @app.route("/admin/houses/<int:house_id>/delete", methods=["POST"])
    @owner_or_admin_required
    def delete_house(house_id):
        """Delete a property listing."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM houses WHERE id = ?", (house_id,))
        house = cursor.fetchone()
        if not house:
            abort(404, description="House listing not found.")

        # Ensure owners can only delete their own listings
        if session.get("role") != "admin" and house["created_by"] != session["user_id"]:
            flash("You do not have permission to delete this property listing.", "danger")
            return redirect(url_for("owner_dashboard"))

        cursor.execute("DELETE FROM houses WHERE id = ?", (house_id,))
        db.commit()

        flash("House listing deleted successfully.", "success")
        if session.get("role") == "owner":
            return redirect(url_for("owner_dashboard"))
        return redirect(url_for("houses"))

    @app.route("/owner/houses/<int:house_id>/toggle-availability", methods=["POST"])
    @owner_or_admin_required
    def toggle_house_availability(house_id):
        """Toggle property availability between available and occupied."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT is_available, created_by FROM houses WHERE id = ?", (house_id,))
        house = cursor.fetchone()
        if not house:
            abort(404, description="House not found.")

        if session.get("role") != "admin" and house["created_by"] != session["user_id"]:
            abort(403)

        new_status = 0 if house["is_available"] == 1 else 1
        cursor.execute("UPDATE houses SET is_available = ? WHERE id = ?", (new_status, house_id))
        db.commit()

        status_text = "available" if new_status == 1 else "marked as occupied"
        flash(f"Property availability updated to: {status_text}.", "success")
        return redirect(request.referrer or url_for("owner_dashboard"))

    # -------------------------------------------------------------
    # Rental Request Status Updates (Owner & Admin)
    # -------------------------------------------------------------
    @app.route("/requests/<int:request_id>/status", methods=["POST"])
    @app.route("/admin/requests/<int:request_id>/status", methods=["POST"])
    @login_required
    def update_request_status(request_id):
        """Approve or reject a rental request (Owner of the property or Admin)."""
        new_status = request.form.get("status", "").strip().capitalize()
        owner_notes = request.form.get("owner_notes", "").strip()

        if new_status not in ("Approved", "Rejected"):
            flash("Invalid request status.", "danger")
            return redirect(request.referrer or url_for("dashboard"))

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT r.*, h.created_by as owner_id 
            FROM rental_requests r
            JOIN houses h ON r.house_id = h.id
            WHERE r.id = ?
            """,
            (request_id,)
        )
        req = cursor.fetchone()
        if not req:
            abort(404, description="Rental request not found.")

        # Permission check: must be admin or the owner who created this house
        if session.get("role") != "admin" and req["owner_id"] != session["user_id"]:
            flash("You do not have permission to manage this inquiry.", "danger")
            return redirect(url_for("index"))

        cursor.execute(
            """
            UPDATE rental_requests 
            SET status = ?, owner_notes = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
            """,
            (new_status, owner_notes, request_id)
        )

        # If approved, mark the house as unavailable
        if new_status == "Approved":
            cursor.execute("UPDATE houses SET is_available = 0 WHERE id = ?", (req["house_id"],))

        db.commit()

        flash(f"Rental request #{request_id} has been {new_status.lower()}.", "success")
        if session.get("role") == "owner":
            return redirect(url_for("owner_dashboard"))
        return redirect(url_for("admin_requests"))

    # -------------------------------------------------------------
    # Admin Dashboard & Moderation Routes
    # -------------------------------------------------------------
    @app.route("/dashboard")
    @app.route("/admin/dashboard")
    @admin_required
    def dashboard():
        """Admin dashboard with summary statistics and recent requests."""
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT COUNT(*) FROM houses")
        total_houses = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM houses WHERE is_available = 1")
        available_houses = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role IN ('tenant', 'renter')")
        total_tenants = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'owner'")
        total_owners = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM rental_requests WHERE status = 'Pending'")
        pending_requests = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT r.*, h.title as house_title, u.full_name as tenant_name, u.email as tenant_email
            FROM rental_requests r
            JOIN houses h ON r.house_id = h.id
            JOIN users u ON r.tenant_id = u.id
            ORDER BY r.id DESC
            LIMIT 5
            """
        )
        recent_requests = cursor.fetchall()

        return render_template(
            "dashboard.html",
            stats={
                "total_houses": total_houses,
                "available_houses": available_houses,
                "total_tenants": total_tenants,
                "total_owners": total_owners,
                "pending_requests": pending_requests
            },
            recent_requests=recent_requests
        )

    @app.route("/admin/houses")
    @admin_required
    def admin_houses():
        """Admin property moderation list."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT h.*, u.full_name as owner_name, u.email as owner_email
            FROM houses h
            JOIN users u ON h.created_by = u.id
            ORDER BY h.id DESC
            """
        )
        houses_list = cursor.fetchall()
        return render_template("houses.html", houses=houses_list, is_admin_view=True)

    @app.route("/admin/users")
    @admin_required
    def admin_users():
        """Admin user and role management portal."""
        role_filter = request.args.get("role", "all").strip().lower()
        search_query = request.args.get("q", "").strip()

        query = "SELECT id, username, email, full_name, phone, role, created_at FROM users WHERE 1=1"
        params = []

        if role_filter in ("admin", "owner", "renter", "tenant"):
            query += " AND role = ?"
            params.append(role_filter)

        if search_query:
            query += " AND (username LIKE ? OR email LIKE ? OR full_name LIKE ?)"
            params.append(f"%{search_query}%")
            params.append(f"%{search_query}%")
            params.append(f"%{search_query}%")

        query += " ORDER BY id DESC"

        db = get_db()
        cursor = db.cursor()
        cursor.execute(query, params)
        users_list = cursor.fetchall()

        return render_template("admin_users.html", users=users_list, current_role=role_filter, search_query=search_query)

    @app.route("/admin/users/<int:target_user_id>/role", methods=["POST"])
    @admin_required
    def update_user_role(target_user_id):
        """Admin change user role."""
        new_role = request.form.get("role", "").strip().lower()
        if new_role not in ("admin", "owner", "renter"):
            flash("Invalid role specified.", "danger")
            return redirect(url_for("admin_users"))

        if target_user_id == session["user_id"]:
            flash("You cannot alter your own administrator role.", "warning")
            return redirect(url_for("admin_users"))

        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, target_user_id))
        db.commit()

        flash(f"User #{target_user_id} role updated to {new_role}.", "success")
        return redirect(url_for("admin_users"))

    @app.route("/admin/users/<int:target_user_id>/delete", methods=["POST"])
    @admin_required
    def delete_user(target_user_id):
        """Admin delete user account with confirmation."""
        if target_user_id == session["user_id"]:
            flash("You cannot delete your own active administrator account.", "danger")
            return redirect(url_for("admin_users"))

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (target_user_id,))
        user = cursor.fetchone()
        if not user:
            abort(404, description="User not found.")

        cursor.execute("DELETE FROM users WHERE id = ?", (target_user_id,))
        db.commit()

        flash(f"User account '{user['username']}' deleted successfully.", "success")
        return redirect(url_for("admin_users"))

    @app.route("/admin/requests")
    @admin_required
    def admin_requests():
        """Admin view and filter all rental inquiries across the platform."""
        status_filter = request.args.get("status", "all").capitalize()
        query = """
            SELECT r.*, h.title as house_title, h.location as house_location, h.rent as house_rent,
                   u.full_name as tenant_name, u.email as tenant_email, u.phone as tenant_phone,
                   o.full_name as owner_name
            FROM rental_requests r
            JOIN houses h ON r.house_id = h.id
            JOIN users u ON r.tenant_id = u.id
            JOIN users o ON h.created_by = o.id
        """
        params = []
        if status_filter in ("Pending", "Approved", "Rejected"):
            query += " WHERE r.status = ?"
            params.append(status_filter)

        query += " ORDER BY r.id DESC"

        db = get_db()
        cursor = db.cursor()
        cursor.execute(query, params)
        requests_list = cursor.fetchall()

        return render_template(
            "rental_requests.html",
            requests=requests_list,
            current_status=status_filter
        )

    # -------------------------------------------------------------
    # Health Check Endpoint (For Docker & Kubernetes Probes)
    # -------------------------------------------------------------
    @app.route("/health")
    def health_check():
        """Liveness & readiness probe endpoint for Kubernetes and Docker."""
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"

        is_healthy = db_status == "connected"
        return jsonify({
            "status": "healthy" if is_healthy else "degraded",
            "database": db_status,
            "service": "HouseRent",
            "version": "2.0.0"
        }), (200 if is_healthy else 503)

    # -------------------------------------------------------------
    # Error Handlers
    # -------------------------------------------------------------
    @app.errorhandler(400)
    def bad_request(error):
        return render_template("base.html", error_title="400 - Bad Request", error_msg=getattr(error, "description", "The request could not be processed due to invalid parameters.")), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("base.html", error_title="403 - Access Forbidden", error_msg="You do not have permission to access the requested resource."), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("base.html", error_title="404 - Page Not Found", error_msg="The property, page, or resource you requested could not be located."), 404

    @app.errorhandler(429)
    def too_many_requests(error):
        return render_template("base.html", error_title="429 - Rate Limit Exceeded", error_msg="Too many requests in a short time window. Please try again later."), 429

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("base.html", error_title="500 - Server Error", error_msg="An unexpected error occurred. Our technical team has been notified."), 500

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Production safeguards: never enable debug if running in production or on Render
    is_production = (
        os.environ.get("FLASK_ENV", "").lower() == "production"
        or os.environ.get("FLASK_CONFIG", "").lower() == "production"
        or os.environ.get("RENDER") is not None
    )
    debug_mode = False if is_production else (os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true"))
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
