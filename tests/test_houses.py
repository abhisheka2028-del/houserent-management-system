import pytest

def test_browse_houses_page(client):
    """Test that the browse houses page loads and renders listings."""
    response = client.get("/houses")
    assert response.status_code == 200
    assert b"Koramangala" in response.data
    assert b"Indiranagar" in response.data

def test_filter_houses_by_location(client):
    """Test filtering listings by location query."""
    response = client.get("/houses?location=Koramangala")
    assert response.status_code == 200
    assert b"Sunny 2BHK Apartment in Koramangala" in response.data
    assert b"Luxury 3BHK Villa with Private Garden" not in response.data

def test_filter_houses_by_bedrooms(client):
    """Test filtering listings by bedroom count."""
    response = client.get("/houses?bedrooms=1")
    assert response.status_code == 200
    assert b"Cozy 1BHK Studio" in response.data
    assert b"Luxury 3BHK Villa" not in response.data

def test_admin_can_add_house(client):
    """Test that an administrator can successfully add a new house listing."""
    # Login as admin
    client.post("/login", data={
        "username": "admin",
        "password": "AdminPassword123!"
    })

    response = client.post("/admin/houses/add", data={
        "title": "Brand New 2BHK in Bellandur",
        "location": "Bellandur, Bengaluru",
        "rent": "30000",
        "bedrooms": "2",
        "bathrooms": "2",
        "description": "Newly constructed flat close to RMZ Ecospace.",
        "image_url": "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800",
        "is_available": "1"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"House listing created successfully" in response.data
    assert b"Brand New 2BHK in Bellandur" in response.data

def test_tenant_cannot_add_house(client):
    """Test that tenants cannot access the house creation endpoint."""
    client.post("/login", data={
        "username": "rahul",
        "password": "TenantPassword123!"
    })

    response = client.get("/admin/houses/add", follow_redirects=True)
    assert response.status_code == 200
    assert b"Access denied. Administrator privileges are required." in response.data

def test_add_house_invalid_rent_rejected(client):
    """Test that negative or invalid rent values are rejected with an error."""
    client.post("/login", data={
        "username": "admin",
        "password": "AdminPassword123!"
    })

    response = client.post("/admin/houses/add", data={
        "title": "Invalid Rent House",
        "location": "Test Area",
        "rent": "-5000",
        "bedrooms": "2",
        "bathrooms": "1",
        "description": "Invalid rent test",
        "is_available": "1"
    })
    assert response.status_code == 200
    assert b"Rent, bedrooms, and bathrooms must be positive numbers" in response.data

def test_admin_can_edit_house(client):
    """Test that admin can update an existing house listing."""
    client.post("/login", data={
        "username": "admin",
        "password": "AdminPassword123!"
    })

    response = client.post("/admin/houses/1/edit", data={
        "title": "Updated Sunny 2BHK in Koramangala",
        "location": "Koramangala 4th Block, Bengaluru",
        "rent": "29500",
        "bedrooms": "2",
        "bathrooms": "2",
        "description": "Updated amenities description.",
        "image_url": "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800",
        "is_available": "1"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"House listing updated successfully" in response.data
    assert b"Updated Sunny 2BHK in Koramangala" in response.data

def test_admin_can_delete_house(client):
    """Test that admin can delete a house listing."""
    client.post("/login", data={
        "username": "admin",
        "password": "AdminPassword123!"
    })

    response = client.post("/admin/houses/6/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"House listing deleted successfully" in response.data

def test_health_check_endpoint(client):
    """Test the /health endpoint used for Kubernetes readiness & liveness probes."""
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "healthy"
    assert json_data["database"] == "connected"
    assert json_data["service"] == "HouseRent"
