import json
import re
import os
import logging
from datetime import datetime, timezone

# Configure structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Sample static house availability data (decoupled from local SQLite for serverless cloud execution)
SAMPLE_HOUSES_CATALOG = [
    {
        "id": 1,
        "title": "Sunny 2BHK Apartment in Koramangala",
        "location": "Koramangala, Bengaluru",
        "rent": 28000,
        "bedrooms": 2,
        "is_available": True
    },
    {
        "id": 2,
        "title": "Luxury 3BHK Villa with Private Garden",
        "location": "Indiranagar, Bengaluru",
        "rent": 55000,
        "bedrooms": 3,
        "is_available": True
    },
    {
        "id": 3,
        "title": "Cozy 1BHK Studio for Working Professionals",
        "location": "HSR Layout, Bengaluru",
        "rent": 16500,
        "bedrooms": 1,
        "is_available": True
    },
    {
        "id": 4,
        "title": "Modern 3BHK High-Rise Gated Community",
        "location": "Whitefield, Bengaluru",
        "rent": 42000,
        "bedrooms": 3,
        "is_available": True
    },
    {
        "id": 5,
        "title": "Spacious 4BHK Duplex Penthouse",
        "location": "Jayanagar, Bengaluru",
        "rent": 72000,
        "bedrooms": 4,
        "is_available": False
    }
]

def build_response(status_code, body_dict):
    """Generate an API Gateway compatible HTTP response dictionary."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
        },
        "body": json.dumps(body_dict)
    }

# ----------------------------------------------------------------------
# Function A: Rental Request API Handler
# ----------------------------------------------------------------------
def handle_rental_request(body_data):
    """
    Validate a rental inquiry received through API Gateway POST request.
    Expected fields: tenant_name, email, house_id, move_in_date, duration_months
    """
    if not isinstance(body_data, dict):
        return build_response(400, {
            "error": "Bad Request",
            "message": "Request body must be a valid JSON object."
        })

    tenant_name = body_data.get("tenant_name", "").strip()
    email = body_data.get("email", "").strip()
    house_id = body_data.get("house_id")
    move_in_date = body_data.get("move_in_date", "").strip()
    duration_months = body_data.get("duration_months")

    # Validation
    errors = []
    if not tenant_name or len(tenant_name) < 2:
        errors.append("Field 'tenant_name' is required and must be at least 2 characters.")

    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not email or not re.match(email_regex, email):
        errors.append("A valid 'email' address is required.")

    if house_id is None or not isinstance(house_id, int) or house_id <= 0:
        errors.append("Field 'house_id' must be a positive integer.")

    if not move_in_date:
        errors.append("Field 'move_in_date' (YYYY-MM-DD) is required.")

    if duration_months is None or not isinstance(duration_months, int) or duration_months <= 0:
        errors.append("Field 'duration_months' must be a positive integer.")

    if errors:
        return build_response(400, {
            "status": "validation_error",
            "errors": errors
        })

    # Generate reference inquiry ID
    inquiry_id = f"REQ-LAMBDA-{house_id}-{int(datetime.now(timezone.utc).timestamp())}"
    logger.info(f"Successfully processed rental request inquiry: {inquiry_id} for tenant {email}")

    return build_response(201, {
        "status": "success",
        "message": "Rental inquiry received and validated by HouseRent Serverless API.",
        "inquiry_id": inquiry_id,
        "details": {
            "tenant_name": tenant_name,
            "email": email,
            "house_id": house_id,
            "move_in_date": move_in_date,
            "duration_months": duration_months,
            "received_at": datetime.now(timezone.utc).isoformat()
        }
    })

# ----------------------------------------------------------------------
# Function B: House Availability API Handler
# ----------------------------------------------------------------------
def handle_house_availability(query_params):
    """
    Return available houses with optional query parameter filtering.
    Supported filters: location, max_rent, bedrooms
    """
    params = query_params or {}
    location_filter = params.get("location", "").lower().strip()
    max_rent_str = params.get("max_rent")
    bedrooms_str = params.get("bedrooms")

    results = []
    for house in SAMPLE_HOUSES_CATALOG:
        # Check availability filter
        if not house["is_available"]:
            continue

        if location_filter and location_filter not in house["location"].lower():
            continue

        if max_rent_str:
            try:
                if house["rent"] > float(max_rent_str):
                    continue
            except ValueError:
                pass

        if bedrooms_str:
            try:
                if house["bedrooms"] != int(bedrooms_str):
                    continue
            except ValueError:
                pass

        results.append(house)

    logger.info(f"House availability queried. Found {len(results)} matching properties.")
    return build_response(200, {
        "status": "success",
        "count": len(results),
        "houses": results
    })

# ----------------------------------------------------------------------
# Event-driven: S3 Object Created Event Trigger Handler
# ----------------------------------------------------------------------
def handle_s3_event(event):
    """
    Process an AWS S3 object creation event notification.
    Extracts bucket name, object key, file size, and logs summary.
    """
    records = event.get("Records", [])
    if not records:
        return {"status": "no_records", "processed_count": 0}

    processed = []
    for record in records:
        s3_data = record.get("s3", {})
        bucket_name = s3_data.get("bucket", {}).get("name", "unknown-bucket")
        object_key = s3_data.get("object", {}).get("key", "unknown-key")
        object_size = s3_data.get("object", {}).get("size", 0)

        summary = {
            "bucket": bucket_name,
            "object_key": object_key,
            "size_bytes": object_size,
            "event_time": record.get("eventTime", datetime.now(timezone.utc).isoformat()),
            "status": "metadata_logged_safely"
        }
        logger.info(f"S3 Event Trigger: File '{object_key}' ({object_size} bytes) in bucket '{bucket_name}' processed.")
        processed.append(summary)

    return {
        "status": "completed",
        "processed_count": len(processed),
        "records": processed
    }

# ----------------------------------------------------------------------
# Main Unified Entrypoint Handler
# ----------------------------------------------------------------------
def lambda_handler(event, context):
    """
    Main AWS Lambda entry point router.
    Routes between API Gateway HTTP events and S3 bucket events.
    """
    # 1. Check if the invocation is from an S3 ObjectCreated event
    if "Records" in event and event["Records"] and "s3" in event["Records"][0]:
        return handle_s3_event(event)

    # 2. Check if the invocation is from API Gateway
    http_method = event.get("httpMethod", "GET")
    raw_path = event.get("path") or event.get("rawPath", "/")
    query_params = event.get("queryStringParameters") or {}

    # Handle CORS preflight OPTIONS request
    if http_method == "OPTIONS":
        return build_response(200, {"message": "CORS preflight OK"})

    # Route: POST /rental-request
    if (raw_path.endswith("/rental-request") or raw_path.endswith("/inquiry")) and http_method == "POST":
        raw_body = event.get("body", "{}")
        try:
            body_dict = json.loads(raw_body) if isinstance(raw_body, str) else (raw_body or {})
        except json.JSONDecodeError:
            return build_response(400, {"error": "Invalid JSON format in body."})
        return handle_rental_request(body_dict)

    # Route: GET /houses/availability
    if (raw_path.endswith("/houses/availability") or raw_path.endswith("/availability")) and http_method == "GET":
        return handle_house_availability(query_params)

    # Default Fallback Route
    return build_response(200, {
        "service": "HouseRent Serverless Microservice API",
        "endpoints": [
            {"method": "GET", "path": "/houses/availability", "description": "Query available houses"},
            {"method": "POST", "path": "/rental-request", "description": "Submit a validated rental inquiry"}
        ],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
