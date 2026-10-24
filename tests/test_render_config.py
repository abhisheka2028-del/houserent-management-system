import os
import sqlite3
import tempfile
from pathlib import Path
import pytest
from app import create_app
from database.init_db import get_db_connection, init_db, run_migrations


def test_requirements_contains_gunicorn_and_production_deps():
    """Verify requirements.txt has all necessary production dependencies."""
    req_file = Path(__file__).resolve().parent.parent / "requirements.txt"
    assert req_file.exists(), "requirements.txt not found"
    content = req_file.read_text().lower()
    assert "gunicorn" in content, "gunicorn must be present in requirements.txt"
    assert "flask" in content, "flask must be present in requirements.txt"
    assert "python-dotenv" in content, "python-dotenv must be present in requirements.txt"


def test_app_exposed_correctly_for_gunicorn():
    """Verify app.py exposes 'app' WSGI callable suitable for 'gunicorn app:app'."""
    import app
    assert hasattr(app, "app"), "app.py must expose module-level 'app' instance"
    assert hasattr(app.app, "wsgi_app"), "app.app must be a WSGI application"


def test_production_config_disables_debug_mode(monkeypatch):
    """Ensure Flask debug mode is strictly False in production."""
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("FLASK_DEBUG", "0")
    monkeypatch.delenv("RENDER", raising=False)

    app = create_app("production")
    assert app.config["DEBUG"] is False, "DEBUG mode must be False in production"
    assert app.debug is False, "app.debug must be False in production"


def test_render_environment_auto_detection_disables_debug(monkeypatch):
    """Ensure Render environment auto-detection selects production and disables debug."""
    monkeypatch.delenv("FLASK_ENV", raising=False)
    monkeypatch.delenv("FLASK_CONFIG", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.setenv("RENDER", "true")

    app = create_app()
    assert app.config["DEBUG"] is False, "DEBUG mode must be False when RENDER=true"


def test_secret_key_read_from_environment(monkeypatch):
    """Ensure secret key is read directly from environment variables."""
    test_secret = "render-prod-custom-cryptographic-key-xyz987"
    monkeypatch.setenv("SECRET_KEY", test_secret)
    monkeypatch.setenv("FLASK_ENV", "production")

    app = create_app("production")
    assert app.config["SECRET_KEY"] == test_secret, "SECRET_KEY must be read from environment"


def test_health_check_endpoint_operational():
    """Verify that /health responds with 200 and healthy status."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    try:
        init_db(db_path)
        app = create_app("testing")
        app.config["DATABASE_PATH"] = db_path
        client = app.test_client()

        response = client.get("/health")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["status"] == "healthy"
        assert payload["database"] == "connected"
        assert payload["service"] == "HouseRent"
    finally:
        os.close(db_fd)
        if os.path.exists(db_path):
            os.remove(db_path)


def test_database_initialization_does_not_overwrite_existing_data():
    """Verify that deployment/startup does not overwrite existing records in the database."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    try:
        # Initialize schema and insert an explicit user and house
        init_db(db_path)
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, full_name, role) "
            "VALUES ('preserve_user', 'preserve@example.com', 'hash', 'Preserved User', 'owner')"
        )
        user_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO houses (title, location, rent, security_deposit, bedrooms, bathrooms, description, created_by) "
            "VALUES ('Preserved House', 'Bangalore', 25000, 0, 2, 2, 'Preserve test', ?)",
            (user_id,)
        )
        conn.commit()
        conn.close()

        # Simulate subsequent app startup with existing DB
        app = create_app("testing")
        app.config["DATABASE_PATH"] = db_path

        # Verify our record and exact custom 0 deposit are untouched
        conn2 = get_db_connection(db_path)
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT username FROM users WHERE username = 'preserve_user'")
        assert cursor2.fetchone() is not None, "Existing user must not be overwritten"

        cursor2.execute("SELECT security_deposit FROM houses WHERE title = 'Preserved House'")
        row = cursor2.fetchone()
        assert row is not None
        assert row["security_deposit"] == 0.0, "Existing custom security deposit must not be overwritten"
        conn2.close()
    finally:
        os.close(db_fd)
        if os.path.exists(db_path):
            os.remove(db_path)


def test_gunicorn_conf_binds_to_port(monkeypatch):
    """Verify that gunicorn.conf.py configures bind to 0.0.0.0 and respects PORT env var."""
    monkeypatch.setenv("PORT", "10000")
    import importlib.util
    conf_path = Path(__file__).resolve().parent.parent / "gunicorn.conf.py"
    assert conf_path.exists(), "gunicorn.conf.py must exist"

    spec = importlib.util.spec_from_file_location("gunicorn_conf", str(conf_path))
    conf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(conf)

    assert conf.bind == "0.0.0.0:10000", "gunicorn.conf.py must bind to 0.0.0.0:$PORT"
    assert conf.workers >= 1, "workers must be >= 1"
