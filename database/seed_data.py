import sqlite3
import os
import sys
from pathlib import Path

# Add project root to sys.path if run directly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from werkzeug.security import generate_password_hash
from database.init_db import get_db_connection, init_db

SAMPLE_USERS = [
    (
        "admin",
        "admin@houserent.com",
        generate_password_hash("AdminPassword123!"),
        "System Administrator",
        "+91 98765 43210",
        "admin"
    ),
    (
        "suresh",
        "suresh@example.com",
        generate_password_hash("OwnerPassword123!"),
        "Suresh Kumar",
        "+91 98450 12345",
        "owner"
    ),
    (
        "rahul",
        "rahul@example.com",
        generate_password_hash("TenantPassword123!"),
        "Rahul Sharma",
        "+91 98111 22334",
        "renter"
    ),
    (
        "priya",
        "priya@example.com",
        generate_password_hash("TenantPassword123!"),
        "Priya Patel",
        "+91 98222 33445",
        "renter"
    )
]

SAMPLE_HOUSES = [
    (
        "Sunny 2BHK Apartment in Koramangala",
        "Koramangala, Bengaluru",
        28000.0,
        56000.0,
        "Apartment",
        "Semi-Furnished",
        "Parking, Power Backup, 24/7 Security, Balcony, Lift",
        2,
        2,
        "Modern 2BHK apartment with modular kitchen, spacious balcony, dedicated parking, and 24/7 security. Located close to tech parks, cafes, and metro connectivity.",
        1,
        "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&w=800&q=80",
        "",
        "owner"  # Owned by Suresh
    ),
    (
        "Luxury 3BHK Villa with Private Garden",
        "Indiranagar, Bengaluru",
        55000.0,
        110000.0,
        "Villa",
        "Furnished",
        "Private Garden, Covered Car Park, Home Office, Inverter Backup, Water Purifier",
        3,
        3,
        "Spacious independent villa featuring hardwood flooring, private landscaped garden, home office room, and power backup. Located in a prime, quiet residential lane.",
        1,
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=800&q=80",
        "",
        "owner"  # Owned by Suresh
    ),
    (
        "Cozy 1BHK Studio for Working Professionals",
        "HSR Layout, Bengaluru",
        16500.0,
        33000.0,
        "Studio",
        "Furnished",
        "High-speed WiFi, Smart TV, Washing Machine, Refrigerator, RO Water",
        1,
        1,
        "Fully furnished studio apartment equipped with high-speed internet, smart TV, washing machine, and refrigerator. Walkable distance to bus stops and grocery supermarkets.",
        1,
        "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=800&q=80",
        "",
        "admin"  # Managed by Admin
    ),
    (
        "Modern 3BHK High-Rise Gated Community",
        "Whitefield, Bengaluru",
        42000.0,
        84000.0,
        "Apartment",
        "Semi-Furnished",
        "Swimming Pool, Gym, Clubhouse, Children Play Area, Gated Security, 2 Covered Car Parks",
        3,
        2,
        "Premium apartment in a gated society with swimming pool, gym, clubhouse, and children's park. 5 minutes from International Tech Park Bengaluru (ITPB).",
        1,
        "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=800&q=80",
        "",
        "owner"  # Owned by Suresh
    ),
    (
        "Spacious 4BHK Duplex Penthouse",
        "Jayanagar, Bengaluru",
        72000.0,
        150000.0,
        "Penthouse",
        "Furnished",
        "Private Terrace, Servants Quarters, Automation, 2 Covered Parking, 24/7 Power",
        4,
        4,
        "Ultra-luxury duplex penthouse with 360-degree terrace views, servant quarters, automated lighting, and 2 covered car parking slots in central Bengaluru.",
        0,  # Currently rented out
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80",
        "",
        "admin"  # Managed by Admin
    ),
    (
        "Affordable 2BHK Near Tech Zone",
        "Electronic City, Bengaluru",
        22000.0,
        44000.0,
        "Apartment",
        "Unfurnished",
        "Lift, Water Treatment Plant, CCTV Surveillance, 2 Wheeler & 4 Wheeler Parking",
        2,
        2,
        "Clean, well-ventilated 2BHK flat with lift, water treatment plant, and CCTV surveillance. Quick access to Infosys, Wipro, and Tech Mahindra campuses.",
        1,
        "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=800&q=80",
        "",
        "owner"  # Owned by Suresh
    )
]

def seed_db(db_path=None):
    """Seed the database with initial users, houses, and rental requests if empty."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Check if users already seeded
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO users (username, email, password_hash, full_name, phone, role) VALUES (?, ?, ?, ?, ?, ?)",
            SAMPLE_USERS
        )
        print("Sample users seeded successfully.")

    # Dynamic user resolution to guarantee foreign keys
    cursor.execute("SELECT id, username FROM users")
    user_map = {row["username"]: row["id"] for row in cursor.fetchall()}
    admin_id = user_map.get("admin", 1)
    owner_id = user_map.get("suresh", admin_id)
    rahul_id = user_map.get("rahul", 2)
    priya_id = user_map.get("priya", 3)

    # Check if houses already seeded
    cursor.execute("SELECT COUNT(*) FROM houses")
    if cursor.fetchone()[0] == 0:
        houses_to_insert = [
            (
                h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7], h[8], h[9], h[10], h[11], h[12],
                owner_id if h[13] == "owner" else admin_id
            )
            for h in SAMPLE_HOUSES
        ]
        cursor.executemany(
            """
            INSERT INTO houses (
                title, location, rent, security_deposit, property_type, furnishing,
                amenities, bedrooms, bathrooms, description, is_available, image_url,
                image_filename, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            houses_to_insert
        )
        print("Sample houses seeded successfully.")

    # Dynamic house resolution to guarantee foreign keys
    cursor.execute("SELECT id FROM houses ORDER BY id ASC")
    house_ids = [row["id"] for row in cursor.fetchall()]

    # Check if requests already seeded
    cursor.execute("SELECT COUNT(*) FROM rental_requests")
    if cursor.fetchone()[0] == 0 and len(house_ids) >= 4:
        requests_to_insert = [
            (house_ids[0], rahul_id, "2026-11-01", 11, "Hi, I am Rahul working at an IT consultancy nearby. Looking to move in by November 1st. Please let me know the agreement details.", "Pending", ""),
            (house_ids[1], priya_id, "2026-11-15", 12, "Interested in the Indiranagar villa for my family. Ready for immediate verification and lease deposit payment.", "Approved", "Tenant profile verified; lease agreement shared."),
            (house_ids[3], rahul_id, "2026-12-01", 6, "Inquiring about short-term lease for 6 months during project duration.", "Rejected", "Minimum lease period required is 11 months.")
        ]
        cursor.executemany(
            """
            INSERT INTO rental_requests (
                house_id, tenant_id, move_in_date, duration_months, message, status, owner_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            requests_to_insert
        )
        print("Sample rental requests seeded successfully.")

    conn.commit()
    conn.close()
    print("Database seeding completed.")

if __name__ == "__main__":
    seed_db()
