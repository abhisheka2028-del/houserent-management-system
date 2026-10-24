import json
import pytest
import sys
from pathlib import Path

# Add serverless directory to sys.path so we can import lambda_function
SERVERLESS_DIR = Path(__file__).resolve().parent.parent / "serverless"
sys.path.insert(0, str(SERVERLESS_DIR))

from lambda_function import lambda_handler

def test_lambda_availability_get():
    """Verify that Lambda handles GET /houses/availability properly."""
    event = {
        "httpMethod": "GET",
        "path": "/houses/availability",
        "queryStringParameters": None,
        "headers": {}
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "success"
    assert body["count"] >= 1

def test_lambda_rental_request_valid():
    """Verify that Lambda accepts and validates a correct rental application."""
    payload = {
        "tenant_name": "Test Tenant",
        "email": "test@tenant.com",
        "house_id": 1,
        "move_in_date": "2026-11-01",
        "duration_months": 12
    }
    event = {
        "httpMethod": "POST",
        "path": "/rental-request",
        "body": json.dumps(payload),
        "headers": {"Content-Type": "application/json"}
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert "inquiry_id" in body

def test_lambda_rental_request_invalid():
    """Verify that Lambda rejects an invalid rental request."""
    payload = {
        "tenant_name": "",
        "email": "not-an-email",
        "house_id": -1,
        "move_in_date": "",
        "duration_months": 0
    }
    event = {
        "httpMethod": "POST",
        "path": "/rental-request",
        "body": json.dumps(payload),
        "headers": {"Content-Type": "application/json"}
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["status"] == "validation_error"
    assert len(body["errors"]) > 0

def test_lambda_s3_event_trigger():
    """Verify that Lambda processes S3 ObjectCreated events."""
    event = {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "eventName": "ObjectCreated:Put",
                "eventTime": "2026-10-09T06:00:00.000Z",
                "s3": {
                    "bucket": {"name": "houserent-documents"},
                    "object": {"key": "agreements/sample.pdf", "size": 1024}
                }
            }
        ]
    }
    response = lambda_handler(event, None)
    assert response["status"] == "completed"
    assert response["processed_count"] == 1
