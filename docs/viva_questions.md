# HouseRent - College Project Viva Voce Questions & Answers Guide

This comprehensive reference contains essential viva questions and in-depth technical answers tailored for **BCA/MCA/B.Tech** examinations covering Web Development, Virtualization, Docker, Kubernetes, and Serverless Computing.

---

## Category 1: Application Architecture & Web Technologies

### Q1: What is the purpose of the HouseRent application?
**Answer:** HouseRent is a full-stack web application developed to manage house listings, tenants, and rental inquiries. It serves as a unified application benchmark deployed across five core paradigms: Local Host, Type-2 Virtual Machine (VirtualBox), Type-1/KVM Virtualization, Docker Containerization, Kubernetes Orchestration, and AWS Serverless Microservices.

### Q2: Why did you choose Python Flask for the backend?
**Answer:** Flask is a lightweight, modular WSGI web framework in Python. Unlike monolithic frameworks like Django, Flask allows explicit control over database connections, routing, middleware, and authentication decorators (`@login_required`, `@admin_required`). It is easy to explain during code evaluation and has low memory overhead, making it ideal for containerization and virtualized microservices.

### Q3: How is user authentication and password security implemented?
**Answer:** Passwords are never stored in plaintext. They are salted and hashed using `werkzeug.security.generate_password_hash` (which implements PBKDF2 with SHA-256 by default). Upon login, `check_password_hash` verifies the submitted credentials against the stored hash. Session-based authentication stores the authenticated user's ID, username, and role in cryptographically signed, HTTP-only session cookies.

### Q4: How is Cross-Site Request Forgery (CSRF) prevented?
**Answer:** The application issues a cryptographically secure pseudo-random 32-byte hexadecimal token (`secrets.token_hex(32)`) saved in the user's session. Every state-changing HTTP form (POST, PUT, DELETE) includes this token in a hidden field. The `app.before_request` hook validates that the form token matches the session token before processing the request.

### Q5: What database is used and how is SQL Injection prevented?
**Answer:** SQLite is used for local and containerized development. SQL Injection is prevented by strictly utilizing **parameterized queries** with placeholder tuples (`cursor.execute("SELECT * FROM users WHERE username = ?", (username,))`). Inputs are never concatenated directly into SQL query strings.

---

## Category 2: Module 1 - Virtualization Fundamentals

### Q6: What is a Hypervisor?
**Answer:** A Hypervisor, or Virtual Machine Monitor (VMM), is a piece of software, firmware, or hardware that creates, manages, and executes virtual machines by virtualizing physical hardware resources (CPU, RAM, storage, network interfaces).

### Q7: Differentiate between Type-1 and Type-2 Hypervisors with examples.
**Answer:**
- **Type-1 (Bare-Metal):** Runs directly on physical server hardware without a host OS. It offers higher performance, low overhead, and enterprise reliability. Examples: VMware ESXi, Microsoft Hyper-V, KVM, Xen.
- **Type-2 (Hosted):** Runs as an application inside an existing host operating system (e.g., Windows 11). Hardware access is mediated through the host OS kernel. Examples: Oracle VM VirtualBox, VMware Workstation Player.

### Q8: What is a Virtual Machine Snapshot? When should you take one?
**Answer:** A snapshot captures the exact state, disk data, and optionally memory of a virtual machine at a specific moment in time. You take a snapshot before applying major software updates, kernel upgrades, or schema migrations. If an update fails, the VM can be reverted to the snapshot within seconds.

### Q9: What is the difference between a Full Clone and a Linked Clone?
**Answer:**
- **Full Clone:** A completely independent copy of the VM with its own separate virtual disk image (`.vdi`). It requires full disk capacity but operates completely detached from the parent VM.
- **Linked Clone:** Created from a snapshot of the parent VM. It shares the parent's base disk image and only writes new changes to a delta disk. It saves disk space and creates faster, but becomes unusable if the parent VM or snapshot is deleted.

### Q10: Why run HouseRent inside an Ubuntu VM instead of directly on Windows?
**Answer:**
1. Running inside an Ubuntu VM provides environment parity with Linux cloud servers (POSIX compliance, `ext4` filesystem).
2. Production WSGI servers like Gunicorn do not run natively on Windows.
3. Complete isolation prevents dependency collisions with host software.

---

## Category 3: Module 2 - Virtualization Tools & Automation (KVM & Libvirt)

### Q11: What is KVM? Is it Type-1 or Type-2?
**Answer:** KVM (Kernel-based Virtual Machine) is a module in the Linux kernel that converts Linux into a Type-1 (bare-metal/hybrid) hypervisor. It enables the kernel to use hardware-assisted virtualization extensions (Intel VT-x or AMD-V).

### Q12: What role does QEMU play alongside KVM?
**Answer:** KVM provides kernel-level CPU and memory virtualization, but it does not emulate peripheral hardware. QEMU (Quick EMUlator) provides user-space emulation for network cards, disk controllers, graphics adapters, and PCI buses.

### Q13: What is `libvirt` and what is `virsh`?
**Answer:** `libvirt` is an open-source management toolkit and daemon (`libvirtd`) that provides an abstraction API to interact with hypervisors like KVM. `virsh` is the command-line interface tool used to control and automate `libvirt` domains (VMs), storage pools, networks, and snapshots.

### Q14: How do you verify if a CPU supports hardware virtualization on Linux?
**Answer:** By inspecting `/proc/cpuinfo`:
```bash
egrep -c '(vmx|svm)' /proc/cpuinfo
```
- `vmx` indicates Intel VT-x.
- `svm` indicates AMD-V.
Alternatively, run `kvm-ok` from the `cpu-checker` package.

### Q15: What is nested virtualization?
**Answer:** Nested virtualization allows running a hypervisor (such as KVM) inside a virtual machine that is already running on a hypervisor (such as VirtualBox or Hyper-V).

---

## Category 4: Module 3 - Containerization Using Docker

### Q16: What is Docker? How do Containers differ from Virtual Machines?
**Answer:** Docker is a platform for building, running, and managing containers. Containers share the host operating system's kernel and isolate processes using Linux **Namespaces** and **cgroups**. Unlike VMs, containers do not package a guest OS kernel, making them lightweight (MBs vs GBs), fast to boot (1-2 seconds vs minutes), and highly resource-efficient.

### Q17: What Linux kernel features enable container isolation?
**Answer:**
1. **Namespaces:** Provide isolation for PID (processes), NET (networking), MNT (mount points), IPC (inter-process communication), and UTS (hostnames).
2. **Control Groups (cgroups):** Enforce resource limits and metering on CPU cores, RAM, disk I/O, and network bandwidth.

### Q18: Why did you use Gunicorn instead of `flask run` in the Docker container?
**Answer:** Flask's built-in development server is single-threaded and not designed for production concurrency or security. Gunicorn is a production-grade WSGI HTTP server that uses a pre-fork worker model (running 3 concurrent worker processes). It efficiently handles multiple concurrent requests and automatically restarts crashed workers.

### Q19: Why does the Docker container bind to `0.0.0.0` instead of `127.0.0.1`?
**Answer:** `127.0.0.1` is the loopback interface scoped strictly inside the container's isolated network namespace. Binding to `127.0.0.1` would make the web app unreachable from outside the container. Binding to `0.0.0.0` listens on all network interfaces within the container, allowing Docker to route external host traffic into port 5000.

### Q20: How did you solve SQLite data persistence in Docker?
**Answer:** Container filesystems are ephemeral; removing a container erases its internal changes. We configured a Docker **host volume mount** (`-v ./data:/app/data` or `volumes:` in `docker-compose.yml`) that maps the host machine's directory into the container. When SQLite writes to `/app/data/houserent.db`, the data is written directly to the host disk and survives container recreation.

---

## Category 5: Module 4 - Container Orchestration Using Kubernetes

### Q21: What is Kubernetes? Why do we need it when we already have Docker?
**Answer:** Docker manages individual containers on a single host. Kubernetes is an enterprise orchestration platform that manages clusters of containers across multiple host machines. It provides automated scheduling, self-healing (restarting failed containers), horizontal auto-scaling, rolling updates, service discovery, and load balancing.

### Q22: What is a Pod in Kubernetes?
**Answer:** A Pod is the smallest deployable computing unit in Kubernetes. It represents a single instance of a running process in the cluster and wraps one or more tightly coupled containers that share storage volumes, IP address, and network port space.

### Q23: What is the relationship between a Deployment and a ReplicaSet?
**Answer:** A Deployment is a higher-level declarative controller that manages ReplicaSets. The ReplicaSet's job is simply to ensure that a specified number of Pod replicas (e.g., 2) are running at all times. The Deployment provides declarative updates: when you update an image version, the Deployment creates a new ReplicaSet, rolls out new Pods, and terminates old Pods gracefully.

### Q24: What is the difference between ClusterIP and NodePort Services?
**Answer:**
- **ClusterIP:** The default service type. Exposes the service on a cluster-internal IP address. The application is only reachable from within the cluster or via `kubectl port-forward`.
- **NodePort:** Exposes the service on a static high port (between 30000–32767, such as 30080) on every cluster node's IP address. It allows direct external access from outside the cluster.

### Q25: Explain Readiness and Liveness Probes.
**Answer:**
- **Readiness Probe (`/health`):** Checks whether the container is ready to accept incoming user traffic. If the probe fails, Kubernetes stops sending traffic to the Pod via the Service until it passes.
- **Liveness Probe (`/health`):** Checks whether the container process is still alive and responsive. If the probe fails, Kubernetes terminates the container and restarts it automatically.

### Q26: Why is SQLite NOT suitable for multi-replica Kubernetes Deployments?
**Answer:** SQLite is a single-file database that relies on operating system file locks. In a multi-replica Deployment (e.g., 2 Pods), each Pod has an independent container filesystem, meaning Pod A cannot see records written by Pod B. Even with a shared network volume (`ReadWriteMany` PVC), concurrent network write locks cause database lock contention and file corruption. In production, multi-replica applications must connect to a centralized RDBMS such as PostgreSQL or MySQL.

---

## Category 6: Module 5 - Serverless Architecture (AWS Lambda & API Gateway)

### Q27: What is Serverless Computing / Function as a Service (FaaS)?
**Answer:** Serverless computing is an execution model where cloud providers dynamically manage the allocation and provisioning of compute servers. Code executes in stateless, event-triggered compute sandboxes (like AWS Lambda). Developers only write functions and are billed strictly for the execution duration and memory used, with zero cost when idle.

### Q28: How does Amazon API Gateway integrate with AWS Lambda?
**Answer:** Amazon API Gateway acts as the public HTTP entry point. When an external client makes a `GET /houses/availability` or `POST /rental-request` request, API Gateway transforms the HTTP request into a JSON event payload, invokes the AWS Lambda function, and formats Lambda's return dictionary back into an HTTP response (with status code, CORS headers, and JSON body).

### Q29: What is an S3 ObjectCreated Event Trigger?
**Answer:** It is an asynchronous event trigger where Amazon S3 automatically invokes an AWS Lambda function whenever an object is uploaded (`s3:ObjectCreated:*`, such as a PDF lease agreement or house photograph). The Lambda function receives metadata about the bucket name, object key, and file size in the event payload.

### Q30: What is the Cold Start problem in AWS Lambda?
**Answer:** A cold start occurs when a Lambda function is invoked after being idle, or during traffic spikes. The cloud provider must spin up a new container sandbox, download the code, and initialize the runtime before executing the handler (typically adding 100–300ms of latency). Subsequent invocations on warm containers execute in single-digit milliseconds.
