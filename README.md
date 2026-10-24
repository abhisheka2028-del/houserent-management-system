# HouseRent – Professional House Rental Management System

A production-ready full-stack web application, rental property management platform, and practical multi-tier cloud infrastructure project demonstrating **Virtualization (Type-1/Type-2), Infrastructure Automation (KVM/Libvirt), Containerization (Docker & Gunicorn), Container Orchestration (Kubernetes/Minikube), and Serverless Microservices (AWS Lambda, API Gateway & Amazon S3)**.

---

## 1. Project Overview & Architecture

**HouseRent** is a modern, responsive web application engineered to solve the operational fragmentation of residential property leasing. It connects tenants directly with verified homeowners and property managers, eliminating hidden brokerage commissions, establishing transparent rental terms, and automating the rental inquiry workflow.

Beyond full-stack web engineering, HouseRent demonstrates how enterprise web software is architected, secured, packaged, orchestrated, and observed across five standard infrastructure paradigms:

```
+------------------------------------------------------------------------------------------------------+
|                                   HouseRent Application Architecture                                 |
+------------------------------------------------------------------------------------------------------+
|  Client Browser (Mobile / Desktop)                                                                  |
|         │                                                                                            |
|         ▼  (HTTP / Port 5000 / Reverse Proxy Port 80)                                                |
|  [ Gunicorn 22.0 WSGI Server (3 Worker Processes) ]                                                  |
|         │                                                                                            |
|         ▼                                                                                            |
|  [ Flask 3.0 Application Core ]                                                                      |
|     ├── Security Layer: CSRF Token Middleware, Rate Limiter, Password Hasher (Werkzeug PBKDF2)       |
|     ├── Authorization Engine: Role-Based Access Control (Admin, Landlord/Owner, Tenant/Renter)       |
|     ├── File Upload Engine: Magic-byte Content Inspection, UUID Filename Generator (5MB limit)       |
|     └── Health Probe Endpoint: /health (Liveness & Readiness for Docker and Kubernetes)              |
|         │                                                    │                                       |
|         ▼                                                    ▼                                       |
|  [ SQLite 3 Relational Database ]                   [ File Storage / Volume Mount ]                  |
|  - Users (Admin, Owner, Renter)                     - /app/data/uploads/ (Persistent Images)         |
|  - Houses (Rent, Deposit, Type, Amenities)          - Default Fallback Property Photos               |
|  - Rental Requests (Status, Lease Duration)                                                          |
|  - Saved Properties (Tenant Bookmarks)                                                               |
+------------------------------------------------------------------------------------------------------+
|                                    Deployment Infrastructure Tiers                                   |
+------------------------------------------------------------------------------------------------------+
| Tier 1: Local Development (Python Virtual Environment / PowerShell on Windows 10/11)                 |
| Tier 2: Hosted Virtualization (Oracle VM VirtualBox & Ubuntu Linux 22.04 LTS Guest)                  |
| Tier 3: Kernel Virtualization & Shell Automation (Linux KVM, QEMU, libvirtd & virsh scripts)         |
| Tier 4: Containerization (Docker Multi-Stage Image, Non-Root appuser, Healthcheck, Docker Compose)   |
| Tier 5: Orchestration (Kubernetes Namespace, ConfigMap, Secret, PVC, Replicas, NodePort/ClusterIP)  |
| Tier 6: Serverless Microservices (AWS Lambda FaaS, API Gateway Endpoints, S3 Event Triggers)         |
| Tier 7: Cloud Web Service (Render Free Web Service, Gunicorn WSGI, Health Probes & Blueprints)       |
+------------------------------------------------------------------------------------------------------+
```

---

## 2. User Roles & System Features

The platform provides dedicated, isolated workflows for three distinct user roles:

### 1. Renter / Tenant Portal
- **Property Discovery:** Search by locality/city, filter by property type (Apartment, Villa, Studio, Penthouse), bedroom count (1 BHK to 4+ BHK), furnishing status, and maximum monthly budget.
- **Rental Applications:** Submit structured applications with intended move-in date, lease period (6 to 24 months), and notes for the landlord.
- **Application Status Tracking:** Real-time visibility into application review status (`Pending`, `Approved`, `Rejected`). Upon approval, direct landlord contact details (Email, Phone) and owner notes become accessible.
- **Saved Properties (Favorites):** Bookmark homes with one click for easy side-by-side comparison.
- **Personalized Recommendations:** Automated property suggestions based on active database listings.
- **Profile Management:** Update personal contact details and securely change passwords.

### 2. Property Owner / Landlord Portal
- **Listing Management:** Add, edit, and delete properties with full specification control (rent, security deposit, property type, furnishing, amenities checklist, detailed description).
- **Secure Image Uploads:** Upload property exterior/interior photos (PNG, JPG, WebP up to 5MB) with automatic magic-byte content validation, safe UUID file naming, and live frontend preview.
- **Availability Management:** Instantly toggle listing availability between *Available for Lease* and *Currently Occupied*.
- **Inquiry Decision Engine:** Review incoming tenant applications, inspect tenant contact info and proposed move-in dates, and approve or reject applications with custom owner feedback notes.
- **Real-Time Operational Metrics:** Live statistics calculated from stored database records (Total Listed, Available, Occupied, Total Inquiries, Pending Review).

### 3. System Administrator Portal
- **User & Role Management:** Search and filter registered accounts across all roles; reassign privileges (Admin, Owner, Renter); delete inactive or malicious accounts with confirmation safeguards.
- **Catalog Moderation:** Global property catalog oversight with administrative edit, availability override, and deletion rights.
- **Global Inquiry Oversight:** Audit all tenant-landlord rental applications across all platform properties.
- **System Metrics & Monitoring:** Platform-wide counters calculated from real database records (Listings, Renters, Landlords, Pending Requests).
- **Container & Cluster Probe Support:** Operational monitoring via the `/health` endpoint.

---

## 3. Technology Stack

| Layer | Technology | Version | Purpose in Architecture |
| :--- | :--- | :--- | :--- |
| **Frontend** | HTML5, Vanilla CSS3, JavaScript, Bootstrap 5.3, Bootstrap Icons 1.11 | Modern Standard | Responsive real-estate UI, custom design system, accessibility |
| **Backend** | Python Flask, Jinja2, Werkzeug | Flask 3.0.3, Werkzeug 3.0 | Application factory, MVC controllers, security decorators |
| **Authentication** | Werkzeug Security (PBKDF2/SHA-256) | Python 3.10+ | Salted password hashing, secure session management |
| **Database** | SQLite 3 with Foreign Key Constraints | SQLite 3 | Embedded relational storage with parameterized SQL queries |
| **File Handling** | Werkzeug `secure_filename`, UUID4, Header Sniffing | Native | Safe property image uploads (PNG/JPG/WebP <= 5MB) |
| **WSGI Server** | Gunicorn | 22.0.0 | High-performance multi-worker WSGI server for container runtime |
| **Containerization** | Docker, Docker Compose | OCI Spec 1.0 | Multi-stage image build, non-root user execution, volume mounts |
| **Orchestration** | Kubernetes, Minikube, kubectl | K8s 1.28+ | Declarative manifests, ConfigMap, Secret, PVC, probes, rolling updates |
| **Testing** | Pytest | 8.2.2 | Automated unit, authorization, validation, and integration tests |
| **Serverless** | AWS Lambda, API Gateway, Amazon S3, AWS SAM | Python 3.10 Runtime | Serverless availability API and document processing event triggers |

---

## 4. Database Schema & Migration Strategy

The relational schema is managed by `database/init_db.py`, featuring an automated safe migration mechanism that updates existing database files without data loss:

```
+-------------------------------------------------------------+
|                            users                            |
+-------------------------------------------------------------+
| id            INTEGER PRIMARY KEY AUTOINCREMENT             |
| username      TEXT UNIQUE NOT NULL                          |
| email         TEXT UNIQUE NOT NULL                          |
| password_hash TEXT NOT NULL (PBKDF2 / SHA-256)              |
| full_name     TEXT NOT NULL                                 |
| phone         TEXT                                          |
| role          TEXT NOT NULL DEFAULT 'renter'                |  -- 'admin' | 'owner' | 'renter'
| created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP           |
+-------------------------------------------------------------+
                               | 1
                               |
                               | N (created_by)
                               v
+-------------------------------------------------------------+
|                           houses                            |
+-------------------------------------------------------------+
| id               INTEGER PRIMARY KEY AUTOINCREMENT          |
| title            TEXT NOT NULL                              |
| location         TEXT NOT NULL                              |
| rent             REAL NOT NULL                              |
| security_deposit REAL NOT NULL DEFAULT 0                    |
| property_type    TEXT NOT NULL DEFAULT 'Apartment'          |  -- Apartment, Villa, Studio, etc.
| furnishing       TEXT NOT NULL DEFAULT 'Semi-Furnished'     |  -- Furnished, Semi-Furnished, Unfurnished
| amenities        TEXT DEFAULT ''                            |  -- Comma-separated amenities list
| bedrooms         INTEGER NOT NULL                           |
| bathrooms        INTEGER NOT NULL                           |
| description      TEXT NOT NULL                              |
| is_available     INTEGER NOT NULL DEFAULT 1                 |  -- 1 = Available, 0 = Occupied
| image_url        TEXT                                       |  -- Web image URL (optional)
| image_filename   TEXT DEFAULT ''                            |  -- Uploaded image filename (UUID)
| created_by       INTEGER NOT NULL, FOREIGN KEY -> users(id) |
| created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP        |
+-------------------------------------------------------------+
         | 1                                           | 1
         |                                             |
         | N (house_id)                                | N (tenant_id)
         +----------------------+  +-------------------+
                                |  |
                                v  v
+-------------------------------------------------------------+
|                       rental_requests                       |
+-------------------------------------------------------------+
| id              INTEGER PRIMARY KEY AUTOINCREMENT           |
| house_id        INTEGER NOT NULL, FOREIGN KEY -> houses(id) |
| tenant_id       INTEGER NOT NULL, FOREIGN KEY -> users(id)  |
| move_in_date    TEXT NOT NULL                               |
| duration_months INTEGER NOT NULL DEFAULT 12                 |
| message         TEXT                                        |
| status          TEXT NOT NULL DEFAULT 'Pending'             |  -- Pending, Approved, Rejected
| owner_notes     TEXT DEFAULT ''                             |
| created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP         |
| updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP         |
+-------------------------------------------------------------+

+-------------------------------------------------------------+
|                      saved_properties                       |
+-------------------------------------------------------------+
| id              INTEGER PRIMARY KEY AUTOINCREMENT           |
| user_id         INTEGER NOT NULL, FOREIGN KEY -> users(id)  |
| house_id        INTEGER NOT NULL, FOREIGN KEY -> houses(id) |
| created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP         |
| UNIQUE(user_id, house_id)                                   |
+-------------------------------------------------------------+
```

---

## 5. Security & Protection Measures

1. **Password Security:** All passwords are salted and hashed using PBKDF2 with SHA-256 via Werkzeug (`generate_password_hash` and `check_password_hash`). Plaintext passwords are never stored or logged.
2. **CSRF Protection:** State-changing HTTP methods (`POST`, `PUT`, `DELETE`) require a cryptographically random CSRF token tied to the user session.
3. **Session Security:** Session cookies are configured with `HttpOnly=True` to mitigate XSS-based cookie theft, `SameSite="Lax"` to prevent CSRF, and optional `Secure=True` for HTTPS environments. Login regenerates session identifiers to prevent session fixation attacks.
4. **Login Rate Limiting:** An IP-based rate limiter restricts consecutive failed login attempts (maximum 5 attempts per 5-minute window) returning HTTP 429 to mitigate brute-force credential stuffing.
5. **Secure File Uploads:** Uploaded property images are validated against allowed extensions (`.png`, `.jpg`, `.jpeg`, `.webp`), checked via file header magic bytes to reject disguised executables, limited to 5MB, renamed to random UUIDs (`prop_<uuid>.ext`), and stored outside the executable web root.
6. **SQL Injection Defense:** All database interactions use parameterized SQL statements (`?` placeholders) with SQLite row factory binding.
7. **Role-Based Authorization:** Custom Python decorators (`@login_required`, `@admin_required`, `@owner_or_admin_required`, `@renter_required`) protect backend routes. Unauthorized URL manipulation redirects to safety with informative alerts.
8. **No Hardcoded Secrets:** Configuration keys are externalized into environment variables read through `.env`.

---

## 6. How to Run Locally on Windows

### Step 1: Open PowerShell and Verify Virtual Environment
Open PowerShell in the project directory:

```powershell
cd "c:\Users\NEW\OneDrive\Documents\House Rental Microproject"
.\venv\Scripts\python --version
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

### Step 3: Optional Development Database Seeding
The application initializes an empty database schema automatically on startup. If you would like realistic sample listings across all three roles for evaluation, run the standalone seeding script:

```powershell
.\venv\Scripts\python scripts/seed_dev_data.py
```

To reset the database back to clean sample data at any time:
```powershell
.\venv\Scripts\python scripts/seed_dev_data.py --reset
```

> **Evaluation Accounts (Development Only):**
> - **Administrator:** `admin@houserent.com` / `AdminPassword123!`
> - **Property Owner (Landlord):** `suresh@example.com` / `OwnerPassword123!`
> - **Renter (Tenant):** `rahul@example.com` / `TenantPassword123!`
> - **Renter (Tenant):** `priya@example.com` / `TenantPassword123!`

### Step 4: Run the Application
```powershell
.\venv\Scripts\python app.py
```

Navigate to: **`http://localhost:5000`**

---

## 7. Automated Testing Suite

The project features **47 automated tests** covering authentication, role-based authorization, property CRUD operations, search filters, inquiry workflows, image upload validation, rate limiting, Render production deployment, and serverless logic. All tests run against an isolated temporary database fixture:

```powershell
.\venv\Scripts\python -m pytest -v
```

### Test Suite Breakdown:
- **`tests/test_auth.py` (9 tests):** Homepage rendering, tenant registration, duplicate email/username rejection, password mismatch, valid login, invalid password rejection, unauthorized route redirection, role dashboard protection, session logout.
- **`tests/test_houses.py` (9 tests):** House catalog listing, locality search query, bedroom filter, admin property creation, negative rent validation, property editing, listing deletion, role checks, and `/health` probe verification.
- **`tests/test_rental_requests.py` (6 tests):** Tenant rental request submission, missing date rejection, admin approval workflow, admin rejection workflow, tenant application timeline view, admin inquiry portal protection.
- **`tests/test_upgrades.py` (11 tests):** Owner registration, owner dashboard access, renter isolation from owner portal, owner property creation with PNG image upload, invalid image extension rejection, executable binary header rejection, saved properties bookmark toggle, admin user management, user role updates, profile editing, and static pages.
- **`tests/test_serverless.py` (4 tests):** AWS Lambda house availability endpoint, rental request payload validation, malformed inquiry rejection, and Amazon S3 `ObjectCreated` event processing.
- **`tests/test_render_config.py` (8 tests):** `requirements.txt` production dependencies (`gunicorn`), `app:app` WSGI exposure, production debug mode disabled (`DEBUG=False`), Render auto-detection, environment secret key extraction, `/health` operational readiness, database data preservation across boots, and `gunicorn.conf.py` 0.0.0.0 dynamic port binding.

**Test Execution Result:** `47 passed (100% pass rate)`.

---

## 8. Docker Containerization (Module 3)

### Build the Docker Image:
```powershell
docker build -t houserent:v1.0 .
```

### Run Container with Volume Persistence:
Using the PowerShell automation script:
```powershell
.\scripts\run_docker.ps1 run
```

Or using standard Docker CLI:
```powershell
docker run -d `
    --name houserent-app `
    -p 5000:5000 `
    -v "${PWD}\data:/app/data" `
    -e FLASK_ENV=production `
    -e SECRET_KEY="your-secure-production-key" `
    houserent:v1.0
```

### Run with Docker Compose:
```powershell
docker compose up -d --build
docker compose ps
```

Verify container health status:
```powershell
docker inspect --format='{{json .State.Health}}' houserent-app
```

---

## 9. Kubernetes Orchestration on Windows (Module 4)

### Prerequisites:
- Minikube or Docker Desktop with Kubernetes enabled on Windows.
- `kubectl` CLI installed and configured.

### Step 1: Start Minikube & Load Image
```powershell
minikube start --driver=docker
minikube image load houserent:v1.0
```

### Step 2: Deploy Declarative Manifests
Deploy the complete stack using the automated PowerShell script:
```powershell
.\scripts\deploy_k8s.ps1 deploy
```

The script applies in sequence:
1. `kubernetes/namespace.yaml` (creates isolated `houserent` namespace)
2. `kubernetes/configmap.yaml` (runtime configuration: `PORT`, `DATABASE_PATH`, `UPLOAD_FOLDER`)
3. `kubernetes/secret.yaml` (base64-encoded secret key)
4. `kubernetes/pvc.yaml` (PersistentVolumeClaim for database and uploaded images)
5. `kubernetes/deployment.yaml` (single-replica Deployment with liveness/readiness probes)
6. `kubernetes/service.yaml` (ClusterIP & NodePort high-port 30080 services)

### Step 3: Access the Application
Using port-forwarding:
```powershell
.\scripts\deploy_k8s.ps1 port-forward 8080
```
Open **`http://localhost:8080`** in your browser.

Or fetch the Minikube NodePort service URL:
```powershell
.\scripts\deploy_k8s.ps1 nodeport-url
```

### Step 4: Inspect Cluster Resources
```powershell
.\scripts\deploy_k8s.ps1 status
```

### Step 5: Rolling Updates & Rollback Demonstration
Simulate a rolling update:
```powershell
kubectl set image deployment/houserent-deployment houserent=houserent:v1.0 -n houserent
kubectl rollout status deployment/houserent-deployment -n houserent
```

Perform an immediate rollback:
```powershell
.\scripts\deploy_k8s.ps1 rollback
```

### Important Architectural Rule regarding SQLite in Kubernetes:
> **SQLite Data Consistency Notice:** In this local Kubernetes deployment, data persistence is maintained via a `ReadWriteOnce` PersistentVolumeClaim (`houserent-pvc`) attached to a single Pod replica. SQLite utilizes local file locks that are not automatically synchronized between concurrent container filesystems. For production multi-pod horizontal autoscaling, an external relational database (such as PostgreSQL or Amazon RDS) and cloud object storage (such as Amazon S3) must be used.

---

## 10. Serverless Microservices (Module 5)

The `serverless/` directory contains an AWS Lambda serverless microservice decoupled from the local database:

1. **GET `/houses/availability`**: Lightweight catalog availability search.
2. **POST `/rental-request`**: Schema-validated rental inquiry submission returning a unique tracking ID (`REQ-LAMBDA-...`).
3. **S3 Event Trigger**: Automated processing of lease agreements uploaded to Amazon S3 (`s3:ObjectCreated`).

To test the serverless logic locally without an active AWS account:
```powershell
.\venv\Scripts\python serverless/test_local.py
```

---

## 11. Render Web Service Deployment Guide

The House Rental Management System is fully pre-configured for automated or manual deployment onto **Render's Free Web Service tier**.

### A. Deployment Methods

#### Option 1: Render Blueprint (Infrastructure-as-Code — Recommended)
1. Push your repository to GitHub or GitLab.
2. In the [Render Dashboard](https://dashboard.render.com), click **New +** > **Blueprint**.
3. Connect your repository. Render will automatically read [`render.yaml`](file:///e:/House%20Rental%20Microproject/render.yaml) and configure:
   - **Service Name:** `houserent-system`
   - **Environment:** `Python 3`
   - **Plan:** `Free`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app` (automatically binds to `0.0.0.0:$PORT` via `gunicorn.conf.py`)
   - **Health Check Path:** `/health`
   - **Environment Variables:** Auto-generates a secure `SECRET_KEY`, sets `FLASK_ENV=production`, `FLASK_DEBUG=0`, `SESSION_COOKIE_SECURE=true`, and enables `AUTO_SEED_DATA=true`.
4. Click **Apply** to deploy.

#### Option 2: Manual Web Service Creation
1. Go to the [Render Dashboard](https://dashboard.render.com) > **New +** > **Web Service**.
2. Connect your Git repository.
3. Configure the following service settings:
   - **Name:** `houserent-web`
   - **Region:** Select the region nearest to your target users (e.g., Singapore, Frankfurt, Oregon, Ohio)
   - **Branch:** `main` (or your active release branch)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free`
4. Expand **Advanced** and set **Health Check Path** to `/health`.
5. Under **Environment Variables**, configure:
   | Key | Value | Description |
   | :--- | :--- | :--- |
   | `FLASK_ENV` | `production` | Enables production configuration mode |
   | `FLASK_DEBUG` | `0` | Strictly disables Flask interactive debugger |
   | `SECRET_KEY` | *(Click "Generate" or paste random 32-byte hex)* | Used for cookie signing & CSRF protection |
   | `DATABASE_PATH` | `database/houserent.db` | SQLite database file location |
   | `UPLOAD_FOLDER` | `static/uploads` | Directory for uploaded property images |
   | `SESSION_COOKIE_SECURE` | `true` | Enforces HTTPS-only cookies (Render terminates TLS by default) |
   | `AUTO_SEED_DATA` | `true` | Safely populates initial sample listings & users on empty database |
   | `WEB_CONCURRENCY` | `2` | 2 Gunicorn workers tuned for 512MB RAM |
6. Click **Create Web Service**.

---

### B. SQLite & Uploaded-Image Persistence Limitations on Render Free Tier

> [!WARNING]
> **CRITICAL PERSISTENCE ADVISORY:** Render Free Web Services use an **ephemeral filesystem** and do NOT permanently store local files.

When deploying on Render's Free plan, the following platform limitations apply:

1. **Ephemeral Local Filesystem:**
   - Every container restart, redeployment, or service update replaces the container disk with a fresh image built from the Git repository.
   - Any modifications made to the local SQLite database (`database/houserent.db`) or property images saved to `static/uploads/` during runtime will be **wiped** upon restart or redeployment.
   - Local files are **NOT permanently stored** on Render's free tier.

2. **Inactivity Sleep / Spin-Down (15 Minutes):**
   - Free Web Services automatically spin down after 15 minutes of inactivity.
   - Incoming traffic triggers a cold start (which may take 50+ seconds). While the application boots safely via `create_app()` and passes `/health` probes, runtime database additions made in previous sessions are reset if the container is recycled.

3. **Lack of Render Persistent Disks on Free Tier:**
   - Render Persistent Disks require a paid Starter plan ($7/mo+). Free web services cannot attach persistent storage volumes.

#### Recommended Production Architecture for Cloud Persistence:
To achieve long-term persistence in cloud production:
- **Relational Database:** Connect an external managed database such as **Render Managed PostgreSQL** (free tier available), Supabase, Neon, or cloud SQLite via **Turso** (`libSQL`).
- **Media & File Storage:** Store uploaded property photos in Cloud Object Storage such as **AWS S3**, **Cloudinary**, or **Supabase Storage**, storing only the permanent public image URLs in the database.

---

## 12. Known Limitations & Production Recommendations

1. **Live Payment Gateway:** Payment processing (such as Razorpay or Stripe) is intentionally excluded; security deposits and rents are recorded as agreed terms rather than live monetary transactions.
2. **Multi-Pod SQLite Write Contention:** As noted in Section 9, running multiple Kubernetes Pods against a shared SQLite file is not recommended due to database file locking semantics. Migrate to PostgreSQL for enterprise cloud deployments.
3. **Email Notification Service:** Rental request approvals currently notify tenants through in-app status indicators and landlord contact details; an asynchronous Celery/Redis worker with SendGrid/SMTP should be integrated for automated transactional email delivery.
4. **Cloud Storage for Uploads:** As detailed in Section 11, ephemeral cloud tiers require object storage (AWS S3/Cloudinary) for persistent tenant and owner photo uploads.

---

## 13. Project Structure

```
House Rental Microproject/
├── app.py                      # Application factory, routes, and decorators
├── config.py                   # Environment-driven configuration classes
├── gunicorn.conf.py            # Gunicorn WSGI runtime config for Render & containers
├── render.yaml                 # Render Blueprint specification for zero-config deploy
├── requirements.txt            # Python dependencies (Flask, Gunicorn, Pytest, Dotenv)
├── Dockerfile                  # Production multi-stage Docker container specification
├── docker-compose.yml          # Container service definition with volume mounts
├── pytest.ini                  # Pytest configuration settings
├── .env.example                # Sample environment configuration template
├── .gitignore                  # Excluded runtime databases, caches, and secrets
├── database/
│   ├── init_db.py              # Schema definition, migrations, and DB connection
│   ├── seed_data.py            # Development sample dataset generator
│   └── houserent.db            # Local SQLite database file
├── data/
│   ├── uploads/                # Persistent directory for uploaded property photos
│   └── houserent.db            # Container volume mounted database
├── static/
│   ├── css/style.css           # Custom real-estate platform design system
│   ├── js/main.js              # Password toggles, image previews, alert dismissers
│   ├── images/
│   │   └── default_property.jpg # High-resolution default fallback property image
│   └── uploads/                # Local development uploads folder
├── templates/
│   ├── base.html               # Main layout with role-aware navbar & footer
│   ├── index.html              # Landing page with hero, search, and real metrics
│   ├── login.html              # Professional login form with show/hide password
│   ├── register.html           # Registration with Renter vs Owner role selector
│   ├── houses.html             # Property catalog with multi-criteria filters
│   ├── house_detail.html       # Property showcase, amenities, and inquiry form
│   ├── renter_dashboard.html   # Renter portal (Applications, Saved, Recommended)
│   ├── owner_dashboard.html    # Landlord portal (My listings, inquiries, metrics)
│   ├── dashboard.html          # Admin dashboard (System stats, recent requests)
│   ├── admin_users.html        # Admin user and role management portal
│   ├── add_house.html          # Property creation with image file upload
│   ├── edit_house.html         # Property editing with photo replacement
│   ├── rental_requests.html    # Admin inquiries moderation portal
│   ├── profile.html            # Profile info and password update
│   ├── about.html              # Platform mission and background
│   └── contact.html            # Support contact form and office details
├── tests/
│   ├── conftest.py             # Pytest fixtures and isolated test database
│   ├── test_auth.py            # Authentication and session tests
│   ├── test_houses.py          # Property browsing, CRUD, and probe tests
│   ├── test_rental_requests.py # Inquiry workflow and permissions tests
│   ├── test_upgrades.py        # Roles, image validation, saved homes, profile tests
│   ├── test_serverless.py      # AWS Lambda and S3 event trigger tests
│   └── test_render_config.py   # Render production deployment & config tests
├── kubernetes/
│   ├── namespace.yaml          # K8s namespace declaration
│   ├── configmap.yaml          # K8s environment configuration
│   ├── secret.yaml.example     # K8s base64 secret example
│   ├── pvc.yaml                # PersistentVolumeClaim for SQLite & uploads
│   ├── deployment.yaml         # Single-replica Deployment with health probes
│   └── service.yaml            # ClusterIP and NodePort service definitions
├── scripts/
│   ├── seed_dev_data.py        # Standalone development database seed CLI
│   ├── run_docker.ps1          # Docker automation script (PowerShell)
│   ├── run_docker.sh           # Docker automation script (Bash)
│   ├── deploy_k8s.ps1          # Kubernetes automation script (PowerShell)
│   └── deploy_k8s.sh           # Kubernetes automation script (Bash)
└── serverless/
    ├── lambda_function.py      # AWS Lambda handler for availability & inquiries
    ├── template.yaml           # AWS SAM cloud infrastructure template
    └── test_local.py           # Local mock runner for serverless validation
```
