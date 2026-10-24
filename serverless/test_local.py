"""
Local test runner for HouseRent AWS Lambda functions.
Demonstrates serverless execution locally without needing an active AWS account.
"""

import json
from lambda_function import lambda_handler

def test_local_availability_get():
    print("\n--- Test 1: GET /houses/availability (All Available Houses) ---")
    mock_event = {
        "httpMethod": "GET",
        "path": "/houses/availability",
        "queryStringParameters": None,
        "headers": {}
    }
    response = lambda_handler(mock_event, None)
    print(f"Status Code: {response['statusCode']}")
    body = json.loads(response["body"])
    print(f"Houses Count: {body['count']}")
    assert response["statusCode"] == 200
    assert body["count"] > 0
    print("[PASS] GET /houses/availability returned expected data.")

def test_local_availability_filter():
    print("\n--- Test 2: GET /houses/availability with Filter (Koramangala) ---")
    mock_event = {
        "httpMethod": "GET",
        "path": "/houses/availability",
        "queryStringParameters": {"location": "Koramangala"},
        "headers": {}
    }
    response = lambda_handler(mock_event, None)
    print(f"Status Code: {response['statusCode']}")
    body = json.loads(response["body"])
    print(f"Filtered Results: {[h['title'] for h in body['houses']]}")
    assert response["statusCode"] == 200
    assert any("Koramangala" in h["location"] for h in body["houses"])
    print("[PASS] Filtering by query parameters succeeded.")

def test_local_rental_request_post():
    print("\n--- Test 3: POST /rental-request (Valid Payload) ---")
    payload = {
        "tenant_name": "Deepak Verma",
        "email": "deepak@example.com",
        "house_id": 1,
        "move_in_date": "2026-12-01",
        "duration_months": 11
    }
    mock_event = {
        "httpMethod": "POST",
        "path": "/rental-request",
        "body": json.dumps(payload),
        "headers": {"Content-Type": "application/json"}
    }
    response = lambda_handler(mock_event, None)
    print(f"Status Code: {response['statusCode']}")
    body = json.loads(response["body"])
    print(f"Response Body: {body}")
    assert response["statusCode"] == 201
    assert "inquiry_id" in body
    print("[PASS] Valid rental inquiry received reference ID.")

def test_local_rental_request_invalid():
    print("\n--- Test 4: POST /rental-request (Invalid Payload - Missing Email) ---")
    payload = {
        "tenant_name": "Deepak Verma",
        "email": "not-an-email",
        "house_id": 1,
        "move_in_date": "2026-12-01",
        "duration_months": -5
    }
    mock_event = {
        "httpMethod": "POST",
        "path": "/rental-request",
        "body": json.dumps(payload),
        "headers": {"Content-Type": "application/json"}
    }
    response = lambda_handler(mock_event, None)
    print(f"Status Code: {response['statusCode']}")
    body = json.loads(response["body"])
    print(f"Validation Errors: {body.get('errors')}")
    assert response["statusCode"] == 400
    assert body["status"] == "validation_error"
    print("[PASS] Invalid payload rejected with 400 Bad Request.")

def test_local_s3_event_trigger():
    print("\n--- Test 5: S3 ObjectCreated Event Notification ---")
    mock_s3_event = {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "eventName": "ObjectCreated:Put",
                "eventTime": "2026-10-09T06:00:00.000Z",
                "s3": {
                    "bucket": {
                        "name": "houserent-documents-bucket"
                    },
                    "object": {
                        "key": "agreements/tenant_rahul_lease_agreement.pdf",
                        "size": 245820
                    }
                }
            }
        ]
    }
    response = lambda_handler(mock_s3_event, None)
    print(f"S3 Processing Response: {response}")
    assert response["status"] == "completed"
    assert response["processed_count"] == 1
    print("[PASS] S3 Event safely parsed object metadata.")

if __name__ == "__main__":
    print("==================================================")
    print("Executing Local Serverless Function Test Suite")
    print("==================================================")
    test_local_availability_get()
    test_local_availability_filter()
    test_local_rental_request_post()
    test_local_rental_request_invalid()
    test_local_s3_event_trigger()
    print("\nAll 5 serverless tests executed successfully!")
