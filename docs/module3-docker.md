# Module 3: Containerization Using Docker

## 1. Overview and Objectives

This lab module covers **operating-system-level virtualization (containerization)** using **Docker** and **Docker Compose**. Students will package the HouseRent application and all its system dependencies into an immutable Docker image, execute it using the production-grade **Gunicorn WSGI server**, persist data across container restarts using volume mounts, publish the image to **Docker Hub**, and orchestrate multi-container configurations.

---

## 2. Theoretical Background: Containers vs. Virtual Machines

```
Virtual Machine Architecture:            Docker Container Architecture:
+-----------------------------------+     +-----------------------------------+
| App A (HouseRent) | App B         |     | App A (HouseRent) | App B         |
+-------------------+---------------+     +-------------------+---------------+
| Guest OS Libraries| Guest OS Libs |     | Container Libs    | Container Libs|
+-------------------+---------------+     +-------------------+---------------+
| Guest OS (Ubuntu) | Guest OS      |     | Docker Engine (cgroups/namespaces)|
+-------------------+---------------+     +-----------------------------------+
| Hypervisor (VirtualBox / KVM)     |     | Host OS Kernel (Linux / WSL2)     |
+-----------------------------------+     +-----------------------------------+
| Host Operating System             |     | Physical Server Hardware          |
+-----------------------------------+     +-----------------------------------+
| Physical Server Hardware          |
+-----------------------------------+
```

### Key Differences:
1. **Kernel Sharing:** VMs package an entire guest operating system including its own kernel (gigabytes in size, minutes to boot). Containers share the host Linux kernel and isolate processes using Linux **Namespaces** (PID, NET, IPC, MNT, UTS) and **Control Groups (cgroups)** for resource quotas.
2. **Speed & Overhead:** Docker containers start in 1–2 seconds and require only megabytes of RAM overhead.
3. **Immutability:** A Docker image represents an exact snapshot of the application binaries, runtime, and configuration, eliminating the classic *"it works on my machine"* syndrome.

---

## 3. Dockerfile and WSGI Architecture

In local development, Flask uses a single-threaded built-in server intended solely for debugging. In a containerized production environment, we use **Gunicorn (Green Unicorn)**, a Python WSGI HTTP server:
- Gunicorn pre-forks multiple worker processes (3 workers in our configuration).
- Binds to `0.0.0.0:5000` to accept external traffic routed by the Docker daemon.
- If a worker crashes, the master process automatically respawns it.

---

## 4. Step-by-Step Practical Demonstration

### Step 1: Inspect the Project Files
Ensure the following files are present in your workspace root:
- `Dockerfile`: Multi-stage specification with Gunicorn and healthchecks.
- `.dockerignore`: Prevents local files (`venv/`, `.git`, `*.db`) from polluting the container image.
- `docker-compose.yml`: Compose specification with persistent volumes.
- `requirements.txt`: Python dependencies.

---

### Step 2: Build the Docker Image
Execute the build command with a version tag:

```bash
# On Linux/macOS or Git Bash:
docker build -t houserent:v1.0 .

# Or via automated script:
./scripts/run_docker.sh build
# On Windows PowerShell:
.\scripts\run_docker.ps1 build
```

*Expected Output:*
```text
[+] Building 12.4s (12/12) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [1/6] FROM docker.io/library/python:3.10-slim
 => [2/6] WORKDIR /app
 => [3/6] RUN apt-get update && apt-get install -y curl
 => [4/6] COPY requirements.txt .
 => [5/6] RUN pip install --no-cache-dir -r requirements.txt
 => [6/6] COPY app.py config.py ./ ...
 => exporting to image
 => naming to docker.io/library/houserent:v1.0
```

Verify the image in local registry:
```bash
docker images | grep houserent
```

> `[SCREENSHOT PLACEHOLDER 3.1: Terminal showing docker build completion and docker images listing]`

---

### Step 3: Run the Container with Volume Persistence
Container storage is ephemeral by default; if the container is removed, changes to the SQLite database would be lost. We mount a persistent host directory (`./data`) to the container storage path (`/app/data`):

```bash
# On Linux/macOS:
mkdir -p ./data
docker run -d \
  --name houserent-app \
  -p 5000:5000 \
  -v "$(pwd)/data:/app/data" \
  -e FLASK_ENV=production \
  -e SECRET_KEY="production-docker-secret-key-2026" \
  -e DATABASE_PATH="/app/data/houserent.db" \
  houserent:v1.0

# On Windows PowerShell:
.\scripts\run_docker.ps1 run
```

---

### Step 4: Verify Container Execution and Port Mapping
Check running containers:
```bash
docker ps
```
*Expected Output:*
```text
CONTAINER ID   IMAGE            COMMAND                  CREATED         STATUS                   PORTS                    NAMES
8f9e2b1c4a5d   houserent:v1.0   "gunicorn --workers …"   5 seconds ago   Up 4 seconds (healthy)   0.0.0.0:5000->5000/tcp   houserent-app
```

Open a web browser and visit: `http://localhost:5000`.
Test creating an account, adding a house listing, or submitting a rental request.

> `[SCREENSHOT PLACEHOLDER 3.2: docker ps showing running healthy container and web UI in browser]`

---

### Step 5: View Streaming Application Logs
Inspect real-time Gunicorn WSGI access logs and application prints:

```bash
docker logs -f houserent-app
```
*Expected Output:*
```text
[2026-10-09 06:30:15 +0000] [1] [INFO] Starting gunicorn 22.0.0
[2026-10-09 06:30:15 +0000] [1] [INFO] Listening at: http://0.0.0.0:5000 (1)
[2026-10-09 06:30:15 +0000] [1] [INFO] Using worker: sync
[2026-10-09 06:30:15 +0000] [7] [INFO] Booting worker with pid: 7
[2026-10-09 06:30:15 +0000] [8] [INFO] Booting worker with pid: 8
[2026-10-09 06:30:15 +0000] [9] [INFO] Booting worker with pid: 9
127.0.0.1 - - [09/Oct/2026:06:30:20 +0000] "GET /health HTTP/1.1" 200 68 "-" "curl/7.88.1"
```

---

### Step 6: Verify Database Persistence Across Container Destruction
1. Add a new house listing or submit a rental request while `houserent-app` is running.
2. Stop and completely destroy the container:
   ```bash
   docker stop houserent-app
   docker rm houserent-app
   ```
3. Start a brand new container mounting the same volume:
   ```bash
   # On Linux/macOS:
   ./scripts/run_docker.sh run
   # On Windows:
   .\scripts\run_docker.ps1 run
   ```
4. Refresh `http://localhost:5000`. Notice that the newly added listing and tenant requests **persist intact** because the database file resided safely on host path `./data/houserent.db`.

> `[SCREENSHOT PLACEHOLDER 3.3: Data persistence verified after destroying and recreating container]`

---

### Step 7: Publishing the Image to Docker Hub
To deploy this application to Kubernetes in Module 4 or share it with evaluators, publish the image to Docker Hub:

1. Log in to Docker Hub:
   ```bash
   docker login
   ```
2. Tag the image with your Docker Hub username:
   ```bash
   # Replace <your_dockerhub_username> with your actual Docker Hub username
   docker tag houserent:v1.0 <your_dockerhub_username>/houserent:v1.0
   ```
3. Push the image to the public registry:
   ```bash
   docker push <your_dockerhub_username>/houserent:v1.0
   ```
4. Verify by pulling and running the image on any other machine:
   ```bash
   docker run -d -p 5000:5000 <your_dockerhub_username>/houserent:v1.0
   ```

> `[SCREENSHOT PLACEHOLDER 3.4: Docker Hub web repository showing published houserent:v1.0 tag]`

---

### Step 8: Multi-Container Orchestration with Docker Compose
Run the entire stack with a single command:
```bash
docker compose up -d
docker compose ps
docker compose logs
docker compose down
```

---

## 5. Troubleshooting Common Container Issues

1. **Port Already in Use (`bind: address already in use`):**
   - Identify what process is occupying port 5000:
     - On Windows: `netstat -ano | findstr :5000`
     - On Linux: `sudo lsof -i :5000`
   - Map a different host port: `-p 5050:5000` and visit `http://localhost:5050`.

2. **Container Exits Immediately with Status 0 or 1:**
   - Inspect container logs to find the traceback: `docker logs <container_id>`.
   - Ensure the command binds to `0.0.0.0` and not `127.0.0.1` (which would only accept connections inside the container namespace).
