"""
Development Seeding Script for HouseRent Application.
Use this script during local development or evaluation to populate the database
with realistic sample listings, users across all three roles (Admin, Landlord, Renter),
and realistic inquiries.

Usage:
    python scripts/seed_dev_data.py
    python scripts/seed_dev_data.py --reset
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.init_db import get_db_connection, init_db
from database.seed_data import seed_db

def main():
    parser = argparse.ArgumentParser(description="Seed HouseRent database for local development.")
    parser.add_argument("--reset", action="store_true", help="Clear existing data before seeding.")
    parser.add_argument("--db-path", type=str, default=None, help="Optional custom SQLite database path.")
    args = parser.parse_args()

    db_path = args.db_path

    if args.reset:
        print("[!] Resetting database data...")
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM saved_properties")
        cursor.execute("DELETE FROM rental_requests")
        cursor.execute("DELETE FROM houses")
        cursor.execute("DELETE FROM users")
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('users', 'houses', 'rental_requests', 'saved_properties')")
        except Exception:
            pass
        conn.commit()
        conn.close()
        print("[OK] Existing data cleared.")

    print("[*] Initializing and seeding database...")
    seed_db(db_path)
    print("[OK] Development seed completed successfully!")
    print("\nAvailable Accounts for Evaluation:")
    print("  - Administrator:   admin@houserent.com  /  AdminPassword123!")
    print("  - Property Owner:  suresh@example.com   /  OwnerPassword123!")
    print("  - Renter (Tenant): rahul@example.com    /  TenantPassword123!")
    print("  - Renter (Tenant): priya@example.com    /  TenantPassword123!")

if __name__ == "__main__":
    main()
