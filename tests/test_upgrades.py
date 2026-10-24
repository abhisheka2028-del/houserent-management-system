import io
import pytest

def test_owner_registration_and_login(client):
    """Test that a new property owner can register and sign in."""
    response = client.post("/register", data={
        "username": "newowner",
        "email": "newowner@example.com",
        "password": "OwnerPassword123!",
        "confirm_password": "OwnerPassword123!",
        "full_name": "New Property Owner",
        "phone": "+91 98888 77777",
        "role": "owner"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Registration successful" in response.data

    # Login as new owner
    login_resp = client.post("/login", data={
        "username": "newowner",
        "password": "OwnerPassword123!"
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert b"Owner Portal" in login_resp.data

def test_owner_dashboard_access(client):
    """Test that owner can view their dashboard and listings."""
    # Login as existing seeded owner Suresh
    client.post("/login", data={
        "username": "suresh",
        "password": "OwnerPassword123!"
    })

    response = client.get("/owner/dashboard")
    assert response.status_code == 200
    assert b"Property Owner Portal" in response.data
    assert b"My Property Listings" in response.data

def test_renter_blocked_from_owner_dashboard(client):
    """Test that a renter cannot access the owner dashboard."""
    client.post("/login", data={
        "username": "rahul",
        "password": "TenantPassword123!"
    })

    response = client.get("/owner/dashboard", follow_redirects=True)
    assert response.status_code == 200
    assert b"Access denied. Property owner or administrator privileges required." in response.data

def test_owner_can_add_property_with_valid_image(client):
    """Test that an owner can add a property with an uploaded PNG image."""
    client.post("/login", data={
        "username": "suresh",
        "password": "OwnerPassword123!"
    })

    # Create dummy PNG image bytes (valid PNG header)
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    image_file = (io.BytesIO(png_bytes), "living_room.png")

    response = client.post("/owner/houses/add", data={
        "title": "Owner Managed Penthouse in Indiranagar",
        "location": "100ft Road, Indiranagar, Bengaluru",
        "rent": "65000",
        "security_deposit": "130000",
        "property_type": "Penthouse",
        "furnishing": "Furnished",
        "amenities": "Parking, Lift, Power Backup, Terrace",
        "bedrooms": "3",
        "bathrooms": "3",
        "description": "Stunning penthouse with direct owner lease.",
        "image_file": image_file,
        "is_available": "1"
    }, content_type="multipart/form-data", follow_redirects=True)

    assert response.status_code == 200
    assert b"House listing created successfully" in response.data
    assert b"Owner Managed Penthouse in Indiranagar" in response.data

def test_invalid_image_extension_rejected(client):
    """Test that non-image extensions (.exe, .sh) are rejected."""
    client.post("/login", data={
        "username": "suresh",
        "password": "OwnerPassword123!"
    })

    fake_file = (io.BytesIO(b"echo 'malicious script'"), "exploit.sh")

    response = client.post("/owner/houses/add", data={
        "title": "Fake Image Listing",
        "location": "Test Area",
        "rent": "30000",
        "bedrooms": "2",
        "bathrooms": "2",
        "description": "Test description",
        "image_file": fake_file,
        "is_available": "1"
    }, content_type="multipart/form-data")

    assert response.status_code == 200
    assert b"Invalid image file format" in response.data

def test_fake_executable_content_rejected(client):
    """Test that a file with .jpg extension but executable binary header is rejected."""
    client.post("/login", data={
        "username": "suresh",
        "password": "OwnerPassword123!"
    })

    # DOS MZ executable header masquerading as a JPEG
    fake_exe = (io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff"), "virus.jpg")

    response = client.post("/owner/houses/add", data={
        "title": "Fake Header Listing",
        "location": "Test Area",
        "rent": "30000",
        "bedrooms": "2",
        "bathrooms": "2",
        "description": "Test description",
        "image_file": fake_exe,
        "is_available": "1"
    }, content_type="multipart/form-data")

    assert response.status_code == 200
    assert b"does not match a valid image format" in response.data

def test_saved_property_toggle(client):
    """Test that a renter can save and remove a property from saved listings."""
    client.post("/login", data={
        "username": "rahul",
        "password": "TenantPassword123!"
    })

    # Save house #2
    save_resp = client.post("/houses/2/save", follow_redirects=True)
    assert save_resp.status_code == 200
    assert b"Property added to your saved listings" in save_resp.data

    # Un-save house #2
    unsave_resp = client.post("/houses/2/save", follow_redirects=True)
    assert unsave_resp.status_code == 200
    assert b"Property removed from saved listings" in unsave_resp.data

def test_admin_user_management(client):
    """Test that administrator can view users and change roles."""
    client.post("/login", data={
        "username": "admin",
        "password": "AdminPassword123!"
    })

    # View user portal
    response = client.get("/admin/users")
    assert response.status_code == 200
    assert b"User &amp; Role Management" in response.data or b"User & Role Management" in response.data
    assert b"@rahul" in response.data

    # Change role of user Rahul (id: 3 in test db or id: 2)
    role_resp = client.post("/admin/users/2/role", data={
        "role": "owner"
    }, follow_redirects=True)
    assert role_resp.status_code == 200
    assert b"role updated" in role_resp.data

def test_renter_blocked_from_admin_users(client):
    """Test that ordinary users cannot access the user management route."""
    client.post("/login", data={
        "username": "rahul",
        "password": "TenantPassword123!"
    })

    response = client.get("/admin/users", follow_redirects=True)
    assert response.status_code == 200
    assert b"Access denied. Administrator privileges are required." in response.data

def test_profile_update(client):
    """Test that a logged-in user can update their profile information."""
    client.post("/login", data={
        "username": "rahul",
        "password": "TenantPassword123!"
    })

    response = client.post("/profile", data={
        "action": "update_info",
        "full_name": "Rahul S. Sharma",
        "email": "rahul_updated@example.com",
        "phone": "+91 98111 99999"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Profile details updated successfully" in response.data
    assert b"Rahul S. Sharma" in response.data

def test_about_and_contact_pages(client):
    """Test that static public pages load successfully."""
    about_resp = client.get("/about")
    assert about_resp.status_code == 200
    assert b"Our Mission" in about_resp.data

    contact_resp = client.get("/contact")
    assert contact_resp.status_code == 200
    assert b"Contact HouseRent Support" in contact_resp.data
