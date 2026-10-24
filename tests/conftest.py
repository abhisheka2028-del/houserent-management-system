import os
import sys
import tempfile
from pathlib import Path
import pytest

# Ensure root directory is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from database.init_db import init_db
from database.seed_data import seed_db

@pytest.fixture
def app_instance():
    """Create a temporary Flask application instance with an isolated database."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    # Set up isolated test configuration
    os.environ["DATABASE_PATH"] = db_path
    os.environ["FLASK_ENV"] = "testing"

    app = create_app("testing")
    app.config["DATABASE_PATH"] = db_path
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    # Seed the fresh temporary database
    seed_db(db_path)

    yield app

    # Cleanup temporary database file after test execution
    os.close(db_fd)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass

@pytest.fixture
def client(app_instance):
    """A test client for sending HTTP requests to the application."""
    return app_instance.test_client()

@pytest.fixture
def runner(app_instance):
    """A test CLI runner for invoking click commands."""
    return app_instance.test_cli_runner()
