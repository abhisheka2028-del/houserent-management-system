# Module 4: Container Orchestration Using Kubernetes

## 1. Overview and Objectives

This lab module demonstrates enterprise container orchestration using **Kubernetes (K8s)** and **Minikube**. Students will deploy the containerized HouseRent application across declarative manifests, configure auto-healing multi-replica Pods, manage internal ClusterIP and external NodePort networking services, inspect ReplicaSets, perform zero-downtime rolling updates, execute rollbacks, configure health probes, and examine stateful storage limitations.

---

## 2. Theoretical Background & Key Kubernetes Concepts

```
+-----------------------------------------------------------------------------------------+
|                                    Kubernetes Cluster                                   |
|                                                                                         |
|  Namespace: houserent                                                                   |
|                                                                                         |
|  +---------------------------+       +-----------------------------------------------+  |
|  | ConfigMap & Secret        |       | Services:                                     |  |
|  | (FLASK_ENV, SECRET_KEY)   |       |  - ClusterIP (Port 80 -> 5000)                |  |
|  +---------------------------+       |  - NodePort  (NodePort 30080 -> 5000)         |  |
|               |                      +-----------------------------------------------+  |
|               v                                               |                         |
|  +--------------------------------------------+               | (Load Balances Traffic) |
|  | Deployment: houserent-deployment           |               |                         |
|  |   +-------------------------------------+  |               |                         |
|  |   | ReplicaSet (e.g., replicas: 2)      |  |<--------------+                         |
|  |   |   +------------------------------+  |  |                                         |
|  |   |   | Pod 1: houserent-xxxx-1      |  |  |                                         |
|  |   |   | [Gunicorn: 0.0.0.0:5000]     |  |  |                                         |
|  |   |   | Probes: /health (Liveness)   |  |  |                                         |
|  |   |   +------------------------------+  |  |                                         |
|  |   |   +------------------------------+  |  |                                         |
|  |   |   | Pod 2: houserent-xxxx-2      |  |  |                                         |
|  |   |   | [Gunicorn: 0.0.0.0:5000]     |  |  |                                         |
|  |   |   | Probes: /health (Readiness)  |  |  |                                         |
|  |   |   +------------------------------+  |  |                                         |
|  |   +-------------------------------------+  |                                         |
|  +--------------------------------------------+                                         |
+-----------------------------------------------------------------------------------------+
```

### Core Architecture Components:
- **Pod:** The smallest deployable unit in Kubernetes, wrapping one or more tightly coupled containers.
- **ReplicaSet:** Ensures a specified number of identical Pod replicas are running at all times.
- **Deployment:** A declarative supervisor managing ReplicaSets, supporting zero-downtime rolling updates and rollbacks.
- **Service:** A stable network abstraction providing a persistent IP and DNS name that load-balances traffic across dynamic Pods.
- **ConfigMap & Secret:** Externalized configuration separating code from environment variables and sensitive keys.
- **Readiness & Liveness Probes:**
  - *Readiness Probe:* Informs Kubernetes when the Pod is ready to accept incoming user traffic.
  - *Liveness Probe:* Informs Kubernetes when the Pod is alive; if it fails (e.g., deadlock), Kubernetes terminates and recreates the container.

---

## 3. Important Architectural Notice: SQLite in Multi-Replica Deployments

> [!WARNING]
> **Stateful Storage Limitation in Kubernetes Multi-Pod Architectures:**
> In our educational demonstration, the Deployment runs **2 replicas**. Each container operates with an isolated, ephemeral local filesystem.
>
> **Why SQLite is NOT used for multi-replica production deployments:**
> 1. SQLite is a serverless, single-file database relying on OS file locks.
> 2. If Pod 1 and Pod 2 write to their own local filesystem files, their databases are independent and will diverge immediately.
> 3. Even with a shared network volume (NFS PVC), concurrent write locks over network filesystems frequently cause SQLite database corruption (`database is locked` error).
>
> **Production Solution:**
> For true multi-replica horizontal autoscaling, production architectures use a client-server RDBMS (such as **PostgreSQL** or **MySQL**) deployed outside the stateless pods (or managed via cloud services like Amazon RDS), or an operator like CloudNativePG.
>
> For our college microproject, we explicitly highlight this architectural distinction during evaluation.

---

## 4. Step-by-Step Practical Demonstration

### Step 1: Install Minikube and kubectl
1. **Install kubectl (Kubernetes CLI):**
   - On Windows (via winget or direct binary): `winget install Kubernetes.kubectl`
   - On Ubuntu/Linux:
     ```bash
     curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
     sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
     ```
   - Verify: `kubectl version --client`

2. **Install Minikube (Local Single-Node Kubernetes Cluster):**
   - On Windows: `winget install Kubernetes.minikube`
   - On Linux:
     ```bash
     curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
     sudo install minikube-linux-amd64 /usr/local/bin/minikube
     ```
   - Verify: `minikube version`

---

### Step 2: Start the Minikube Cluster
Start a local Kubernetes cluster using Docker as the virtualization driver:

```bash
minikube start --driver=docker
```
*Expected Output:*
```text
* minikube v1.33.1 on Ubuntu 22.04
* Using the docker driver based on user configuration
* Starting control plane node minikube in cluster minikube
* Pulling base image ...
* Creating docker container (CPUs=2, Memory=4000MB) ...
* Preparing Kubernetes v1.30.0 on Docker 26.1.1 ...
* Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```

Verify cluster connectivity:
```bash
kubectl cluster-info
kubectl get nodes
```

> `[SCREENSHOT PLACEHOLDER 4.1: Terminal showing minikube start and kubectl get nodes output]`

---

### Step 3: Load the HouseRent Docker Image into Minikube
Because Minikube operates inside its own Docker/VM environment, load the locally built image directly into the Minikube registry:

```bash
minikube image load houserent:v1.0
```
Verify the loaded image inside Minikube:
```bash
minikube image ls | grep houserent
```

---

### Step 4: Apply Kubernetes Manifests
Deploy the entire application stack:

```bash
# 1. Create dedicated namespace
kubectl apply -f kubernetes/namespace.yaml

# 2. Apply ConfigMap and Secret
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secret.yaml.example

# 3. Create Deployment (2 Replicas, Probes, Resource Quotas)
kubectl apply -f kubernetes/deployment.yaml

# 4. Create Services (ClusterIP on port 80 and NodePort on 30080)
kubectl apply -f kubernetes/service.yaml
```

Alternatively, use the automated script:
```bash
# Linux/macOS:
./scripts/deploy_k8s.sh deploy

# Windows PowerShell:
.\scripts\deploy_k8s.ps1 deploy
```

---

### Step 5: Inspect Cluster Resources
Examine the created objects in the `houserent` namespace:

```bash
kubectl get all -n houserent
```
*Expected Output:*
```text
NAME                                       READY   STATUS    RESTARTS   AGE
pod/houserent-deployment-7d9f6b9c4-abc12   1/1     Running   0          45s
pod/houserent-deployment-7d9f6b9c4-xyz89   1/1     Running   0          45s

NAME                                 TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
service/houserent-nodeport-service   NodePort    10.108.45.12     <none>        5000:30080/TCP   45s
service/houserent-service            ClusterIP   10.96.182.230    <none>        80/TCP           45s

NAME                                   READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/houserent-deployment   2/2     2            2           45s

NAME                                             DESIRED   CURRENT   READY   AGE
replicaset.apps/houserent-deployment-7d9f6b9c4   2         2         2       45s
```

> `[SCREENSHOT PLACEHOLDER 4.2: kubectl get all -n houserent displaying running Pods and Services]`

---

### Step 6: Access the Application via ClusterIP Port-Forwarding
ClusterIP services are internal to the cluster. To access the service on your local development machine:

```bash
kubectl port-forward svc/houserent-service 8080:80 -n houserent
```
Now open your browser and navigate to:
`http://localhost:8080`

Verify that all house listings, details, and tenant forms render seamlessly.

---

### Step 7: Access the Application via NodePort Service
NodePort exposes the application on port `30080` of every cluster node.

To open the NodePort service directly in Minikube:
```bash
minikube service houserent-nodeport-service -n houserent
```
Minikube will automatically open your default browser to `http://<minikube-ip>:30080`.

> `[SCREENSHOT PLACEHOLDER 4.3: HouseRent application accessed via Kubernetes NodePort service]`

---

### Step 8: Scaling the Deployment (Horizontal Scaling)
Demonstrate Kubernetes dynamic scaling from 2 to 4 Pod replicas:

```bash
kubectl scale deployment/houserent-deployment --replicas=4 -n houserent
```
Watch the Pods scale up in real-time:
```bash
kubectl get pods -n houserent -w
```
*Result:* Kubernetes spins up 2 additional Pods within seconds.

---

### Step 9: Performing a Zero-Downtime Rolling Update
Simulate rolling out version `v2.0` of the application container image:

```bash
kubectl set image deployment/houserent-deployment houserent=houserent:v2.0 -n houserent
```
Monitor the rollout process:
```bash
kubectl rollout status deployment/houserent-deployment -n houserent
```
*Expected Output:*
```text
Waiting for deployment "houserent-deployment" rollout to finish: 1 out of 4 new replicas have been updated...
Waiting for deployment "houserent-deployment" rollout to finish: 2 of 4 updated replicas are available...
deployment "houserent-deployment" successfully rolled out
```

---

### Step 10: Rolling Back a Deployment
If version `v2.0` causes an issue, immediately rollback to the previous stable revision:

```bash
kubectl rollout undo deployment/houserent-deployment -n houserent
kubectl rollout status deployment/houserent-deployment -n houserent
```
*Expected Output:*
```text
deployment.apps/houserent-deployment rolled back
```

---

### Step 11: Viewing Logs and Troubleshooting Pods
Inspect logs from all Pods in the deployment simultaneously using label selectors:

```bash
kubectl logs -l app=houserent -n houserent --tail=50
```

To troubleshoot an individual failing Pod:
```bash
# Describe pod events (e.g., ImagePullBackOff, CrashLoopBackOff, probe failures)
kubectl describe pod <pod-name> -n houserent

# Execute interactive shell inside running Pod
kubectl exec -it <pod-name> -n houserent -- /bin/bash
```

Clean up cluster resources:
```bash
kubectl delete -f kubernetes/
kubectl delete namespace houserent
```
