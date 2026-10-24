# HouseRent Serverless Architecture (AWS Lambda & API Gateway)

This directory contains the serverless components for **Module 5: Serverless Architecture** of the syllabus.

## Architecture Overview

Instead of deploying a monolithic web server for every function, serverless microservices allow specific features to execute on-demand in a Function as a Service (FaaS) environment:

- **Function A: Rental Request API** (`POST /rental-request`)
  - Validates rental applications.
  - Generates tracking reference IDs.
  - Returns structured HTTP responses (201 Created or 400 Bad Request).
- **Function B: House Availability API** (`GET /houses/availability`)
  - Provides instant JSON queries for available properties.
  - Supports query parameters (`location`, `max_rent`, `bedrooms`).
- **Event-Driven Processor: S3 ObjectCreated Trigger**
  - Triggered automatically when agreements (PDFs) or property photos are uploaded to an S3 bucket.
  - Safely extracts metadata without server management.

## File Breakdown

- `lambda_function.py`: Production-ready Python 3.10 handler covering API Gateway and S3 event sources.
- `template.yaml`: AWS Serverless Application Model (AWS SAM) infrastructure-as-code template.
- `test_local.py`: Local offline testing script that executes mock events against the Lambda handler.
- `requirements.txt`: Python package requirements for the serverless functions.

## Running Tests Locally (No AWS Account Required)

You can verify the Lambda functions locally without cloud costs or an AWS account:

```bash
python serverless/test_local.py
```

Or via pytest:

```bash
pytest tests/test_serverless.py
```

For live deployment instructions, IAM policies, and cost analysis, see [`docs/module5-serverless.md`](../docs/module5-serverless.md).
