import pytest

def test_tenant_submit_rental_request(client):
    """Test that a logged-in tenant can submit a rental application."""
    # Log in as tenant Priya (id: 3) who has not requested house 3
    client.post("/login", data={
        "username": "priya",
        "password": "TenantPassword123!"
    })

    response = client.post("/houses/3/request", data={
        "move_in_date": "2026-11-20",
        "duration_months": "12",
        "message": "Excited to rent this studio flat for 12 months."
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Rental request submitted successfully" in response.data

def test_tenant_missing_date_rejected(client):
    """Test that submitting a rental request with a blank move-in date fails."""
    client.post("/login", data={
        "username": "priya",
        "password": "TenantPassword123!"
    })

    response = client.post("/houses/3/request", data={
        "move_in_date": "",
        "duration_months": "12",
        "message": "No date provided"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Please specify an intended move-in date" in response.data

def test_admin_approve_rental_request(client):
    """Test that an administrator can approve a pending rental request."""
    client.post("/login", data={
        "username": "admin",
        "password": "AdminPassword123!"
    })

    # Request #1 is 'Pending' in seed data
    response = client.post("/admin/requests/1/status", data={
        "status": "Approved"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Rental request #1 has been approved" in response.data

def test_admin_reject_rental_request(client):
    """Test that an administrator can reject a rental request."""
    client.post("/login", data={
        "username": "admin",
        "password": "AdminPassword123!"
    })

    response = client.post("/admin/requests/1/status", data={
        "status": "Rejected"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Rental request #1 has been rejected" in response.data

def test_tenant_view_own_requests(client):
    """Test that a tenant sees their own applications in my_requests."""
    client.post("/login", data={
        "username": "rahul",
        "password": "TenantPassword123!"
    })

    response = client.get("/my-requests")
    assert response.status_code == 200
    assert b"Sunny 2BHK Apartment in Koramangala" in response.data

def test_tenant_blocked_from_admin_requests_portal(client):
    """Test that a tenant cannot access the admin requests management page."""
    client.post("/login", data={
        "username": "rahul",
        "password": "TenantPassword123!"
    })

    response = client.get("/admin/requests", follow_redirects=True)
    assert response.status_code == 200
    assert b"Access denied. Administrator privileges are required." in response.data
