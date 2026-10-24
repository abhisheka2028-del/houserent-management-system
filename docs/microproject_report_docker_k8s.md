# Microproject Report: Containerization and Orchestration of HouseRent System

---

## 1. Title of the Microproject
**"Containerization and Resilient Cloud Orchestration of HouseRent Management System using Docker and Kubernetes (Minikube)"**

---

## 2. Aim & Objectives

### Aim:
To package the **HouseRent** web application into an isolated, lightweight, multi-stage Docker container and orchestrate it within a local Kubernetes (Minikube) cluster with declarative manifests, persistent volume claims, health probes, and automated scaling.

### Objectives:
1. **Containerization (Docker):**
   - Package Python 3.10 runtime, Flask web application, and Gunicorn WSGI server into a multi-stage Docker image (`houserent:v1.0`).
   - Implement non-root user execution (`appuser:10001`) and automated health checks (`/health`).
   - Configure host-to-container volume mounting (`./data:/app/data`) for SQLite and image upload persistence.
2. **Container Orchestration (Kubernetes / Minikube):**
   - Isolate application workloads using a dedicated Kubernetes `Namespace` (`houserent`).
   - Externalize runtime configuration and credentials via `ConfigMap` and base64-encoded `Secret`.
   - Guarantee data retention across pod restarts and rollouts using a `PersistentVolumeClaim` (PVC).
   - Configure self-healing with **Liveness** and **Readiness** probes.
   - Expose the deployment using dual-tier networking: internal `ClusterIP` and external `NodePort` (port 30080).
   - Test zero-downtime rolling updates, scaling, and rollbacks.

---

## 3. System Architecture & Theory

### 3.1 Virtual Machines vs. Docker Containers
```
Virtual Machine Architecture:            Docker Container Architecture:
+-----------------------------------+     +-----------------------------------+
| App (HouseRent)                   |     | App (HouseRent)                   |
+-----------------------------------+     +-----------------------------------+
| Guest OS Libraries & Binaries     |     | Container Libs (Python/Gunicorn)  |
+-----------------------------------+     +-----------------------------------+
| Guest OS Kernel (e.g., Ubuntu)    |     | Docker Engine (cgroups/namespaces)|
+-----------------------------------+     +-----------------------------------+
| Hypervisor (VirtualBox / KVM)     |     | Host Operating System Kernel      |
+-----------------------------------+     +-----------------------------------+
| Physical Server Hardware          |     | Physical Server Hardware          |
+-----------------------------------+     +-----------------------------------+
```

### 3.2 Kubernetes Cluster Deployment Architecture
```
+-----------------------------------------------------------------------------------------+
|                                    Kubernetes Cluster                                   |
|                                                                                         |
|  Namespace: houserent                                                                   |
|                                                                                         |
|  +---------------------------+       +-----------------------------------------------+  |
|  | ConfigMap & Secret        |       | Services:                                     |  |
|  | (FLASK_ENV, SECRET_KEY)   |       |  - ClusterIP: Port 80 -> 5000 (Internal)      |  |
|  +---------------------------+       |  - NodePort: Port 30080 -> 5000 (External)    |  |
|               |                      +-----------------------------------------------+  |
|               v                                               |                         |
|  +--------------------------------------------+               | (Routes Traffic)        |
|  | Deployment: houserent-deployment           |<--------------+                         |
|  |   +-------------------------------------+  |                                         |
|  |   | Pod Replica: houserent-xxxx         |  |                                         |
|  |   |   - Container: houserent:v1.0       |  |                                         |
|  |   |   - WSGI: Gunicorn (3 workers)      |  |                                         |
|  |   |   - Probes: /health (Live/Ready)    |  |                                         |
|  |   |   - Volume: /app/data <------+      |  |                                         |
|  |   +------------------------------|------+  |                                         |
|  +----------------------------------|---------+                                         |
|                                     v                                                   |
|             +-------------------------------------------------+                         |
|             | PersistentVolumeClaim (houserent-pvc: 1Gi, RWO) |                         |
|             +-------------------------------------------------+                         |
+-----------------------------------------------------------------------------------------+
```

---

## 4. Implementation Steps & Real Terminal Execution Outputs

### Step 1: Docker Image Build
**Command Executed:**
```powershell
docker build -t houserent:v1.0 .
```
**Observed Terminal Output:**
```text
#1 [internal] load build definition from Dockerfile
#1 DONE 0.1s
#2 [1/10] FROM docker.io/library/python:3.10-slim
#3 [2/10] WORKDIR /app
#4 [3/10] RUN apt-get update && apt-get install -y --no-install-recommends curl
#5 [4/10] COPY requirements.txt .
#6 [5/10] RUN pip install --no-cache-dir -r requirements.txt
#7 [6/10] COPY app.py config.py ./
#8 [7/10] COPY database/ ./database/
#9 [8/10] COPY templates/ ./templates/
#10 [9/10] COPY static/ ./static/
#11 [10/10] RUN mkdir -p /app/data /app/data/uploads && useradd -u 10001 appuser
#12 naming to docker.io/library/houserent:v1.0 done
```

---

### Step 2: Docker Container Execution & Volume Persistence
**Command Executed:**
```powershell
docker run -d `
    --name houserent-app `
    -p 5000:5000 `
    -v "${PWD}\data:/app/data" `
    -e FLASK_ENV=production `
    -e SECRET_KEY="houserent-docker-production-key-928374" `
    houserent:v1.0
```
**Container Verification Output (`docker ps`):**
```text
CONTAINER ID   IMAGE            COMMAND                  STATUS                    PORTS                    NAMES
16670ed230fe   houserent:v1.0   "gunicorn --workers …"   Up 2 minutes (healthy)    0.0.0.0:5000->5000/tcp   houserent-app
```

**Health Check Response:**
```json
{
  "database": "connected",
  "service": "HouseRent",
  "status": "healthy",
  "version": "2.0.0"
}
```

---

### Step 3: Kubernetes Stack Deployment
**Manifests Applied:**
```powershell
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secret.yaml
kubectl apply -f kubernetes/pvc.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

**Observed Rollout Output:**
```text
namespace/houserent created
configmap/houserent-config created
secret/houserent-secret created
persistentvolumeclaim/houserent-pvc created
deployment.apps/houserent-deployment created
service/houserent-service created
service/houserent-nodeport-service created

Waiting for deployment "houserent-deployment" rollout to finish: 0 of 1 updated replicas are available...
deployment "houserent-deployment" successfully rolled out
```

---

### Step 4: Verification of Cluster Resources
**Command Executed:**
```powershell
kubectl get all,pvc -n houserent
```

**Observed Output:**
```text
NAME                                           READY   STATUS    RESTARTS   AGE
pod/houserent-deployment-c67797f55-hsfh6       1/1     Running   0          3m

NAME                                 TYPE        CLUSTER-IP     PORT(S)          AGE
service/houserent-nodeport-service   NodePort    10.96.120.25   5000:30080/TCP   3m
service/houserent-service            ClusterIP   10.96.183.83   80/TCP           3m

NAME                                   READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/houserent-deployment   1/1     1            1           3m

NAME                                             DESIRED   CURRENT   READY   AGE
replicaset.apps/houserent-deployment-c67797f55   1         1         1       3m

NAME                                  STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/houserent-pvc   Bound    pvc-89d42407-7ae0-4497-ba7e-e179267c7e9c   1Gi        RWO            hostpath
```

---

### Step 5: Service Access Verification
**Port Forwarding Command:**
```powershell
kubectl port-forward svc/houserent-service 8080:80 -n houserent
```

**Access Points:**
- Web Portal: `http://localhost:8080` (HTTP Status: 200 OK)
- Health API: `http://localhost:8080/health` (`{"status": "healthy", "database": "connected"}`)

---

## 5. Report Screenshot Evidence Checklist

Include the following screenshots in your report (matching `screenshots/` directory):

| Figure # | Suggested Filename | Caption / Evidence Description |
| :--- | :--- | :--- |
| **Fig 1** | `17_docker_build_output.png` | Terminal showing successful build of `houserent:v1.0` Docker image |
| **Fig 2** | `18_docker_ps_healthy.png` | `docker ps` showing running container on port 5000 with healthy probe |
| **Fig 3** | `19_docker_volume_persistence.png` | Host directory `.\data` containing `houserent.db` and uploaded photos |
| **Fig 4** | `21_minikube_status_nodes.png` | Output of `kubectl get nodes` showing active control-plane node |
| **Fig 5** | `22_kubectl_get_all.png` | Output of `kubectl get all -n houserent` showing Pods, Services & PVC |
| **Fig 6** | `23_kubectl_scaling.png` | Scale demonstration (`kubectl scale deployment --replicas=2`) |
| **Fig 7** | `24_kubectl_rolling_update.png` | Rollout status output showing zero-downtime rolling update |
| **Fig 8** | `01_home_page.png` | HouseRent web UI loaded in browser at `http://localhost:8080` |

---

## 6. Architectural Analysis & Key Learnings

1. **Defense-in-Depth Security:**
   The Docker container runs as non-root user `appuser` (UID `10001`), preventing privilege escalation attacks on the host kernel if container breakout occurs.
2. **Probes & Self-Healing:**
   - **Readiness Probe:** Ensures that user traffic is only routed to the container once Gunicorn is fully loaded and SQLite is accessible.
   - **Liveness Probe:** Periodically checks container responsiveness; if a deadlock occurs, Kubernetes automatically terminates and respawns the Pod.
3. **Decoupled Configuration:**
   Environment parameters (`PORT`, `DATABASE_PATH`) are externalized in `ConfigMap`, while credentials (`SECRET_KEY`) are secured in `Secret`, strictly following Twelve-Factor App methodology.
4. **Stateful Storage in Orchestration:**
   In local single-pod deployments, data is preserved using a `PersistentVolumeClaim`. For enterprise cloud scaling with multiple concurrent write replicas, SQLite should be substituted with an external managed database (e.g., PostgreSQL or Amazon RDS) due to file-locking constraints.

---

## 7. Viva / Evaluation Questions & Model Answers

### Q1: What is the purpose of Gunicorn in the Docker container instead of Flask's built-in server?
> **Answer:** Flask's built-in development server is single-threaded and unsuitable for production. Gunicorn is a production-ready WSGI HTTP server that implements a pre-fork master-worker model (3 workers), handling concurrent connections, automatic worker lifecycle management, and improved throughput.

### Q2: What is the difference between ClusterIP and NodePort services?
> **Answer:** 
> - **ClusterIP:** Default service type. Exposes the service on an internal IP address reachable only from within the Kubernetes cluster.
> - **NodePort:** Exposes the service on a static high port (30000–32767, here 30080) across all cluster nodes, allowing external clients or browser access.

### Q3: Why is a PersistentVolumeClaim (PVC) required for the container?
> **Answer:** Containers have an ephemeral writable layer. Without a PVC, all database records (`houserent.db`) and uploaded property images would be permanently destroyed when a Pod restarts, crashes, or updates. The PVC binds to durable host storage.

### Q4: How do Readiness and Liveness Probes differ?
> **Answer:**
> - **Readiness Probe:** Determines if the container is ready to accept incoming network traffic. If it fails, endpoints remove the Pod from Service load balancers.
> - **Liveness Probe:** Determines if the container process is alive and healthy. If it fails, Kubernetes terminates and restarts the container.

---

## 8. Conclusion
The HouseRent platform was successfully containerized and deployed into a Kubernetes cluster. The system exhibits high resilience through automated health probes, complete data persistence through volume mounting, and zero-downtime rolling update capability.
