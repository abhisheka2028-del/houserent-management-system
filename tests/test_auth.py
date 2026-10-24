import pytest

def test_homepage_loads(client):
    """Test that the homepage loads with status code 200 and expected branding."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"HouseRent" in response.data
    assert b"Find Your Ideal Rental Home" in response.data

def test_registration_success(client):
    """Test that a new tenant can successfully register."""
    response = client.post("/register", data={
        "username": "newtenant",
        "email": "newtenant@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "full_name": "New Tenant",
        "phone": "+91 99999 88888"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Registration successful" in response.data

def test_registration_duplicate_rejected(client):
    """Test that duplicate usernames or emails are rejected."""
    # Existing user 'rahul' is in seed data
    response = client.post("/register", data={
        "username": "rahul",
        "email": "another@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "full_name": "Duplicate Rahul",
        "phone": "+91 99999 00000"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"already exists" in response.data

def test_registration_password_mismatch(client):
    """Test that mismatched passwords trigger a validation error."""
    response = client.post("/register", data={
        "username": "mismatchuser",
        "email": "mismatch@example.com",
        "password": "Password123!",
        "confirm_password": "DifferentPassword456!",
        "full_name": "Mismatch User",
        "phone": "+91 99999 11111"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Passwords do not match" in response.data

def test_login_success_tenant(client):
    """Test valid tenant login."""
    response = client.post("/login", data={
        "username": "rahul",
        "password": "TenantPassword123!"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome back, Rahul Sharma" in response.data

def test_login_incorrect_password(client):
    """Test that invalid password credentials are rejected."""
    response = client.post("/login", data={
        "username": "rahul",
        "password": "WrongPassword!"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data

def test_unauthorized_access_to_dashboard(client):
    """Test that an unauthenticated user cannot access the admin dashboard."""
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

def test_tenant_cannot_access_admin_dashboard(client):
    """Test that a tenant is blocked from accessing the admin dashboard."""
    # Log in as tenant
    client.post("/login", data={
        "username": "rahul",
        "password": "TenantPassword123!"
    })
    response = client.get("/dashboard", follow_redirects=True)
    assert response.status_code == 200
    assert b"Access denied. Administrator privileges are required." in response.data

def test_logout(client):
    """Test user logout clears the session."""
    client.post("/login", data={
        "username": "rahul",
        "password": "TenantPassword123!"
    })
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"successfully logged out" in response.data
