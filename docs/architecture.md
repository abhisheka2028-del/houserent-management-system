# HouseRent - System Architecture & Evolution Across Syllabus Modules

This document provides a comprehensive architectural breakdown of the **HouseRent – House Rental Management System**, tracing its progression across all five modules of the syllabus: **Virtualization, Virtualization Automation, Docker Containerization, Kubernetes Orchestration, and AWS Serverless Architecture**.

---

## 1. Overall Architectural Workflow

The application serves as a consistent microproject implemented across five progressive paradigms of modern computing infrastructure:

```mermaid
flowchart TD
    subgraph S0["Source Code & Development"]
        SC["HouseRent Python Flask Web Application"]
        GIT["Git Version Control & GitHub Repository"]
        SC --> GIT
    end

    subgraph S1["Module 1 & 2: Virtualization"]
        GIT --> VB["Type-2 Hypervisor: Oracle VirtualBox (Windows Host)"]
        GIT --> KVM["Type-1/Kernel Hypervisor: KVM + Virt-Manager (Ubuntu)"]
        VB --> UBU1["Ubuntu 22.04 LTS Guest VM\n(2 vCPUs, 4GB RAM, 25GB Disk)"]
        KVM --> UBU2["KVM Managed Guest VM\nAutomated via virsh Shell Scripts"]
    end

    subgraph S2["Module 3: Containerization"]
        GIT --> DOC["Docker Engine & Multi-stage Dockerfile"]
        DOC --> GUNI["Production Container: Gunicorn WSGI (3 Workers)"]
        DOC --> VOL["Docker Volume: ./data (SQLite Persistence)"]
        DOC --> HUB["Docker Hub Registry (houserent:v1.0)"]
    end

    subgraph S3["Module 4: Container Orchestration"]
        HUB --> K8S["Kubernetes Cluster (Minikube / MicroK8s)"]
        K8S --> CM["ConfigMap & Secrets (Environment & Keys)"]
        K8S --> PODS["Deployment: Multi-Replica Pods (2 Replicas)\nLiveness & Readiness Probes"]
        K8S --> SVC1["ClusterIP Service (Port 80 -> 5000)"]
        K8S --> SVC2["NodePort Service (NodePort: 30080)"]
    end

    subgraph S4["Module 5: Serverless Microservices"]
        GIT --> SAM["AWS SAM / CloudFormation Template"]
        SAM --> APIGW["Amazon API Gateway (REST HTTP Endpoints)"]
        APIGW --> LAM1["Lambda Function A:\nRental Request Validation API"]
        APIGW --> LAM2["Lambda Function B:\nHouse Availability Query API"]
        S3B["Amazon S3 Storage Bucket\n(Agreements & Photos)"] -->|s3:ObjectCreated| LAM3["Lambda Function C:\nEvent-Driven Metadata Processor"]
    end
```

---

## 2. Infrastructure Comparison Matrix

| Dimension | Native Host (Windows) | Module 1: VirtualBox | Module 2: KVM/QEMU | Module 3: Docker | Module 4: Kubernetes | Module 5: AWS Serverless |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Isolation Level** | None (Process level) | Full hardware emulation (Type-2) | Hardware-assisted kernel (Type-1/Hybrid) | OS-level kernel namespaces & cgroups | Container grouping & network namespace | Ephemeral execution sandbox (MicroVM / Firecracker) |
| **Startup Time** | Instant (<1s) | Slow (30–60s) | Moderate (15–30s) | Fast (1–3s) | Fast per Pod (2–5s) | Sub-second cold start (100–300ms) |
| **Resource Overhead** | Minimal | High (Guest OS duplicates kernel & RAM) | Moderate | Very Low (Shared host Linux kernel) | Low per container, moderate cluster plane | Zero idle resource consumption (Pay-per-request) |
| **Portability** | OS-dependent | VM image (.ova / .vdi, 5-20 GB) | Disk image (.qcow2, 5-20 GB) | Standard OCI image (~150 MB) | Declarative YAML manifests | CloudFormation / SAM YAML |
| **Scaling** | Manual | Heavyweight VM cloning | Automated `virt-clone` script | Multi-container compose | Automated replica scaling (`kubectl scale`) | Auto-scales from 0 to 1,000s of requests |

---

## 3. Application Component Design

```mermaid
graph LR
    subgraph Client["Client Tier"]
        B["Web Browser / Mobile Client"]
    end

    subgraph AppTier["Application Tier (Flask + Gunicorn)"]
        MW["CSRF Security & Session Middleware"]
        AUTH["Auth Controller (Hash, RBAC)"]
        HOUSE["Listing Controller (CRUD, Filter)"]
        REQ["Rental Request Controller (State Engine)"]
        HEALTH["Health Probe Controller (/health)"]
    end

    subgraph DataTier["Data Tier"]
        DB[(SQLite Relational Database)]
        T1["users table"]
        T2["houses table"]
        T3["rental_requests table"]
    end

    B <-->|HTTP / HTTPS| MW
    MW --> AUTH
    MW --> HOUSE
    MW --> REQ
    MW --> HEALTH

    AUTH <-->|Parameterized SQL| T1
    HOUSE <-->|Parameterized SQL| T2
    REQ <-->|Parameterized SQL| T3
    T1 -.-> DB
    T2 -.-> DB
    T3 -.-> DB
```

---

## 4. State Management & Database Persistence Across Modules

A foundational concept for computer science students is **Statefulness vs. Statelessness**:

1. **Local Development (Windows):**
   - SQLite file stored at `database/houserent.db`.
   - Single application process connects directly via file locks.

2. **Docker Single Container:**
   - Container filesystems are ephemeral (erased on container removal).
   - Solution: Host volume mapping (`./data:/app/data`) mounts the host folder into the container, preserving database records between restarts.

3. **Kubernetes Multi-Replica Challenge (Critical Viva Topic):**
   - If a Kubernetes Deployment scales to 2 or 4 replicas, each pod has its own container filesystem.
   - If each pod uses an independent local SQLite file, Pod A cannot see records written by Pod B.
   - **Production Remedy:** In production, cloud applications decouple compute from state by using a centralized relational database service (e.g., PostgreSQL, Amazon RDS, Google Cloud SQL) or a distributed storage volume (`ReadWriteMany` PVC backed by NFS or Ceph).
   - In our educational lab, we demonstrate scaling with health probes while highlighting this exact architectural boundary.

4. **Serverless (AWS Lambda):**
   - Lambda functions are completely stateless; their execution context is ephemeral and disposed of after idle periods.
   - Therefore, our serverless demonstration operates either via API validation and mock catalogs or connects to cloud-native databases (such as Amazon DynamoDB or Amazon RDS Aurora Serverless).
