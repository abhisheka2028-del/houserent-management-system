import sqlite3
import os
from pathlib import Path

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    role TEXT NOT NULL DEFAULT 'renter',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS houses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    location TEXT NOT NULL,
    rent REAL NOT NULL,
    security_deposit REAL NOT NULL DEFAULT 0,
    property_type TEXT NOT NULL DEFAULT 'Apartment',
    furnishing TEXT NOT NULL DEFAULT 'Semi-Furnished',
    amenities TEXT DEFAULT '',
    bedrooms INTEGER NOT NULL,
    bathrooms INTEGER NOT NULL,
    description TEXT NOT NULL,
    is_available INTEGER NOT NULL DEFAULT 1,
    image_url TEXT,
    image_filename TEXT DEFAULT '',
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rental_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    house_id INTEGER NOT NULL,
    tenant_id INTEGER NOT NULL,
    move_in_date TEXT NOT NULL,
    duration_months INTEGER NOT NULL DEFAULT 12,
    message TEXT,
    status TEXT NOT NULL DEFAULT 'Pending',
    owner_notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (house_id) REFERENCES houses (id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS saved_properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    house_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (house_id) REFERENCES houses (id) ON DELETE CASCADE,
    UNIQUE(user_id, house_id)
);

CREATE INDEX IF NOT EXISTS idx_houses_location ON houses(location);
CREATE INDEX IF NOT EXISTS idx_houses_availability ON houses(is_available);
CREATE INDEX IF NOT EXISTS idx_houses_owner ON houses(created_by);
CREATE INDEX IF NOT EXISTS idx_requests_tenant ON rental_requests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_requests_house ON rental_requests(house_id);
CREATE INDEX IF NOT EXISTS idx_saved_user ON saved_properties(user_id);
"""

def get_db_connection(db_path=None):
    """Create and return a database connection with Row factory enabled."""
    if db_path is None:
        db_path = os.environ.get(
            "DATABASE_PATH",
            str(Path(__file__).resolve().parent / "houserent.db")
        )
    
    # Ensure parent directory exists unless using in-memory db
    if db_path != ":memory:":
        parent_dir = Path(db_path).parent
        parent_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def run_migrations(conn):
    """Safely apply schema migrations to preserve existing data while adding new fields."""
    cursor = conn.cursor()

    # Check columns in houses
    cursor.execute("PRAGMA table_info(houses)")
    house_cols = {row["name"] for row in cursor.fetchall()}

    if house_cols:
        if "security_deposit" not in house_cols:
            cursor.execute("ALTER TABLE houses ADD COLUMN security_deposit REAL NOT NULL DEFAULT 0")
            # Populate default security deposit only for legacy rows that lacked the column
            cursor.execute("UPDATE houses SET security_deposit = rent * 2 WHERE security_deposit = 0 OR security_deposit IS NULL")
        if "property_type" not in house_cols:
            cursor.execute("ALTER TABLE houses ADD COLUMN property_type TEXT NOT NULL DEFAULT 'Apartment'")
        if "furnishing" not in house_cols:
            cursor.execute("ALTER TABLE houses ADD COLUMN furnishing TEXT NOT NULL DEFAULT 'Semi-Furnished'")
        if "amenities" not in house_cols:
            cursor.execute("ALTER TABLE houses ADD COLUMN amenities TEXT DEFAULT ''")
        if "image_filename" not in house_cols:
            cursor.execute("ALTER TABLE houses ADD COLUMN image_filename TEXT DEFAULT ''")

    # Check columns in rental_requests
    cursor.execute("PRAGMA table_info(rental_requests)")
    req_cols = {row["name"] for row in cursor.fetchall()}

    if req_cols and "owner_notes" not in req_cols:
        cursor.execute("ALTER TABLE rental_requests ADD COLUMN owner_notes TEXT DEFAULT ''")

    # Ensure saved_properties table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            house_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (house_id) REFERENCES houses (id) ON DELETE CASCADE,
            UNIQUE(user_id, house_id)
        )
    """)

    conn.commit()

def init_db(db_path=None):
    """Initialize database tables with the schema and run migrations."""
    conn = get_db_connection(db_path)
    with conn:
        conn.executescript(SCHEMA_SQL)
        run_migrations(conn)
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database schema and migrations completed successfully.")
