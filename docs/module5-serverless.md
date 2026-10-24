# Module 5: Serverless Architecture (AWS Lambda, API Gateway & S3)

## 1. Overview and Objectives

This lab module explores modern **Serverless Computing** and **Function as a Service (FaaS)** using **AWS Lambda**, **Amazon API Gateway**, and **Amazon S3**.

Rather than running an entire Flask monolithic server continuously on an EC2 virtual machine or a container pod, specific microservices are implemented as lightweight, stateless functions that run only when invoked by incoming HTTP requests or cloud storage events.

---

## 2. Theoretical Concepts

### 2.1 What is Function as a Service (FaaS)?
In traditional hosting, you pay for virtual servers (like EC2 or DigitalOcean droplets) 24 hours a day, 7 days a week, regardless of whether any user visits the site.

In **FaaS**:
1. You deploy individual blocks of code (functions) rather than complete operating systems.
2. The cloud provider automatically provisions execution runtimes (microVMs using Firecracker) in milliseconds upon incoming events.
3. Billing is strictly metered per execution millisecond and memory consumed. When traffic drops to zero, **cost is exactly zero**.
4. Elastic auto-scaling is handled transparently by the cloud platform.

### 2.2 Event-Driven Architecture
An **event-driven architecture** is a software design pattern where decoupled services communicate by producing and reacting to events:
- **Event Producer:** An actor that creates an event (e.g., API Gateway receiving an HTTP POST request, or a user uploading an image to an S3 bucket).
- **Event Router:** Dispatches the event to registered listeners.
- **Event Consumer (AWS Lambda):** Executes business logic based on the payload of the event.

```
+-----------------------------------------------------------------------------------------+
|                               AWS Serverless Cloud Flow                                 |
|                                                                                         |
|  [Client Browser]                                                                       |
|         |                                                                               |
|         v (HTTP GET /houses/availability)                                               |
|  [Amazon API Gateway] -------> [AWS Lambda Function B: Availability Query]              |
|         |                                                                               |
|         v (HTTP POST /rental-request)                                                   |
|  [Amazon API Gateway] -------> [AWS Lambda Function A: Rental Request Validation]       |
|                                                                                         |
|  [Property Documents / Photos Uploaded]                                                 |
|         |                                                                               |
|         v                                                                               |
|  [Amazon S3 Storage Bucket] ---> (Event: s3:ObjectCreated)                              |
|                                         |                                               |
|                                         v                                               |
|                                [AWS Lambda Function C: Document Metadata Processor]     |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Serverless Database Consideration (Viva Focus)

> [!IMPORTANT]
> **Why Lambda Does Not Use the Local SQLite Database:**
> AWS Lambda operates in temporary microVM containers that are created on-demand and destroyed after idle periods. Any local disk file (in `/tmp`) is ephemeral.
>
> In production serverless systems:
> - Applications connect to cloud-native managed databases: **Amazon DynamoDB** (NoSQL serverless database) or **Amazon Aurora Serverless v2** (PostgreSQL/MySQL).
> - For our educational microproject, the serverless functions operate as self-contained microservices with validated mock catalogs and data schema verification, isolating student demonstration from costly cloud databases.

---

## 4. Local Testing Without AWS Account (Recommended First Step)

You can verify the entire serverless implementation on your local machine without needing an AWS account or incurring any cloud charges:

```bash
# Run standalone script
python serverless/test_local.py

# Or via pytest automated test suite
pytest tests/test_serverless.py -v
```

*Expected Terminal Output:*
```text
Executing Local Serverless Function Test Suite
--- Test 1: GET /houses/availability (All Available Houses) ---
Status Code: 200 | Houses Count: 4 [PASS]

--- Test 2: GET /houses/availability with Filter (Koramangala) ---
Status Code: 200 | Filtered Results: ['Sunny 2BHK Apartment in Koramangala'] [PASS]

--- Test 3: POST /rental-request (Valid Payload) ---
Status Code: 201 | Inquiry ID: REQ-LAMBDA-1-1791507515 [PASS]

--- Test 4: POST /rental-request (Invalid Payload - Missing Email) ---
Status Code: 400 | Status: validation_error [PASS]

--- Test 5: S3 ObjectCreated Event Notification ---
Status Code: completed | Records: 1 [PASS]
```

> `[SCREENSHOT PLACEHOLDER 5.1: Terminal output of serverless/test_local.py showing all tests passing]`

---

## 5. Live AWS Deployment Demonstration (Using AWS SAM or AWS CLI)

### Step 1: Prerequisites & Security Best Practices
1. **AWS Free Tier Account:** AWS provides 1,000,000 free Lambda requests per month and 5 GB of free S3 storage indefinitely under the Free Tier.
2. **AWS CLI & SAM CLI Installed:**
   ```bash
   aws --version
   sam --version
   ```
3. **Configure AWS Credentials (NEVER HARDCODE CREDENTIALS):**
   ```bash
   aws configure
   ```
   Provide:
   - AWS Access Key ID: `[YOUR_ACCESS_KEY]`
   - AWS Secret Access Key: `[YOUR_SECRET_KEY]`
   - Default region name: `ap-south-1` (Mumbai) or `us-east-1` (N. Virginia)
   - Default output format: `json`

---

### Step 2: Minimum IAM Permissions (Least Privilege Principle)
The AWS Lambda execution role requires only:
1. `AWSLambdaBasicExecutionRole` (allows writing execution logs to Amazon CloudWatch Logs).
2. `AmazonS3ReadOnlyAccess` (allows reading metadata of uploaded documents in the designated bucket).
No administrative root permissions are granted to the Lambda execution role.

---

### Step 3: Build and Deploy Using AWS SAM
Navigate to the serverless directory:

```bash
cd serverless
sam build
sam deploy --guided
```

Provide the guided parameters:
- **Stack Name:** `houserent-serverless-stack`
- **AWS Region:** `ap-south-1` (or your preferred region)
- **Confirm changes before deploy:** `Y`
- **Allow SAM CLI to create IAM roles:** `Y`
- **Disable rollback:** `N`

Once deployed, SAM CLI outputs your public URLs:
```text
Outputs:
-------------------------------------------------------------------------------------------------
Key                 ApiEndpointUrl
Description         Public API Gateway Invocation URL for HouseRent microservices
Value               https://abc123xyz.execute-api.ap-south-1.amazonaws.com/prod/

Key                 AvailabilityUrl
Description         Direct GET URL for house availability endpoint
Value               https://abc123xyz.execute-api.ap-south-1.amazonaws.com/prod/houses/availability

Key                 RentalRequestUrl
Description         Direct POST URL for rental inquiry endpoint
Value               https://abc123xyz.execute-api.ap-south-1.amazonaws.com/prod/rental-request
-------------------------------------------------------------------------------------------------
```

> `[SCREENSHOT PLACEHOLDER 5.2: SAM deploy outputs showing API Gateway URLs]`

---

### Step 4: Testing the Live Endpoints

#### 1. Test Function B: House Availability (GET Request)
Using `curl` or Postman:

```bash
curl -X GET "https://<your-api-id>.execute-api.ap-south-1.amazonaws.com/prod/houses/availability"
```
*Expected JSON Response (HTTP 200):*
```json
{
  "status": "success",
  "count": 4,
  "houses": [
    {
      "id": 1,
      "title": "Sunny 2BHK Apartment in Koramangala",
      "location": "Koramangala, Bengaluru",
      "rent": 28000,
      "bedrooms": 2,
      "is_available": true
    }
  ]
}
```

Test query filter for budget:
```bash
curl -X GET "https://<your-api-id>.execute-api.ap-south-1.amazonaws.com/prod/houses/availability?max_rent=30000"
```

---

#### 2. Test Function A: Rental Request Validation (POST Request)
Send a valid rental inquiry:

```bash
curl -X POST "https://<your-api-id>.execute-api.ap-south-1.amazonaws.com/prod/rental-request" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "Siddharth Verma",
    "email": "siddharth@example.com",
    "house_id": 1,
    "move_in_date": "2026-11-01",
    "duration_months": 11
  }'
```
*Expected JSON Response (HTTP 201 Created):*
```json
{
  "status": "success",
  "message": "Rental inquiry received and validated by HouseRent Serverless API.",
  "inquiry_id": "REQ-LAMBDA-1-1791507515",
  "details": {
    "tenant_name": "Siddharth Verma",
    "email": "siddharth@example.com",
    "house_id": 1,
    "move_in_date": "2026-11-01",
    "duration_months": 11,
    "received_at": "2026-10-09T06:40:00.000Z"
  }
}
```

Send an invalid payload to verify error handling:
```bash
curl -X POST "https://<your-api-id>.execute-api.ap-south-1.amazonaws.com/prod/rental-request" \
  -H "Content-Type: application/json" \
  -d '{"tenant_name": ""}'
```
*Expected Response (HTTP 400 Bad Request):*
```json
{
  "status": "validation_error",
  "errors": [
    "Field 'tenant_name' is required and must be at least 2 characters.",
    "A valid 'email' address is required.",
    "Field 'house_id' must be a positive integer.",
    "Field 'move_in_date' (YYYY-MM-DD) is required.",
    "Field 'duration_months' must be a positive integer."
  ]
}
```

> `[SCREENSHOT PLACEHOLDER 5.3: Postman or curl executing GET and POST requests against API Gateway]`

---

#### 3. Test Event-Driven S3 ObjectCreated Trigger
Upload a sample lease agreement PDF or image to the created S3 bucket:

```bash
# Upload a sample document
aws s3 cp sample_agreement.pdf s3://<your-bucket-name>/agreements/sample_agreement.pdf
```

Inspect CloudWatch Logs for the `S3DocumentProcessorFunction`:
```bash
sam logs -n S3DocumentProcessorFunction --tail
```
*Expected Log Entry:*
```text
2026-10-09T06:42:10.123Z INFO S3 Event Trigger: File 'agreements/sample_agreement.pdf' (245820 bytes) in bucket 'houserent-storage-...' processed.
```

> `[SCREENSHOT PLACEHOLDER 5.4: CloudWatch logs displaying S3 Event Trigger execution]`

---

## 6. AWS Cost Considerations & Free-Tier Limits

| Service | AWS Free Tier Monthly Allowance | Expected Lab Cost |
| :--- | :--- | :--- |
| **AWS Lambda** | 1,000,000 requests & 3.2M seconds compute time | $0.00 (Free) |
| **Amazon API Gateway** | 1,000,000 HTTP API calls for 12 months | $0.00 (Free) |
| **Amazon S3** | 5 GB Standard Storage & 20,000 GET requests | $0.00 (Free) |
| **CloudWatch Logs** | 5 GB ingestion & 5 GB archive storage | $0.00 (Free) |

> **Cost Optimization Tip:** Always delete the stack immediately after your presentation to prevent unexpected charges if you forget the resources running.

---

## 7. Cleanup Instructions to Avoid Charges

When your project demonstration or evaluation is complete, tear down all provisioned cloud resources:

```bash
cd serverless
sam delete --stack-name houserent-serverless-stack
```

Verify that the stack is completely removed:
```bash
aws cloudformation describe-stacks --stack-name houserent-serverless-stack
```
*(Should return `Stack does not exist`)*
