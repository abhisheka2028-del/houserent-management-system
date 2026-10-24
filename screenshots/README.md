# HouseRent - Project Screenshots and Evaluation Evidence

This directory is designated for your college project report screenshots, lab observation records, and viva demonstration evidence.

Save your captured screenshots using the suggested filenames below:

---

## 1. Web Application & UI Screenshots

| Filename | Description | Status |
| :--- | :--- | :--- |
| `01_home_page.png` | HouseRent landing page with hero banner, search bar, and statistics | *[Screenshot Placeholder]* |
| `02_browse_houses.png` | House listings page showing house cards and search/filter inputs | *[Screenshot Placeholder]* |
| `03_house_detail.png` | Detailed house listing with amenities and rental inquiry form | *[Screenshot Placeholder]* |
| `04_login_page.png` | User authentication form with demo credential shortcuts | *[Screenshot Placeholder]* |
| `05_register_page.png` | Tenant registration form with input validation | *[Screenshot Placeholder]* |
| `06_admin_dashboard.png` | Admin dashboard with statistics counter and recent inquiries table | *[Screenshot Placeholder]* |
| `07_admin_manage_requests.png` | Admin request management page showing Approve and Reject actions | *[Screenshot Placeholder]* |
| `08_tenant_my_requests.png` | Tenant view displaying status badges (Pending, Approved, Rejected) | *[Screenshot Placeholder]* |

---

## 2. Module 1: VirtualBox & Ubuntu Virtualization

| Filename | Description | Status |
| :--- | :--- | :--- |
| `09_virtualbox_vm_settings.png` | VirtualBox VM hardware allocation (2 vCPUs, 4GB RAM, 25GB VDI) | *[Screenshot Placeholder]* |
| `10_ubuntu_terminal_running_app.png` | HouseRent web server running inside Ubuntu terminal | *[Screenshot Placeholder]* |
| `11_virtualbox_snapshot_tree.png` | VirtualBox Snapshot Manager showing snapshot point | *[Screenshot Placeholder]* |
| `12_virtualbox_cloned_vm.png` | Primary VM and cloned VM listed side-by-side in VirtualBox | *[Screenshot Placeholder]* |

---

## 3. Module 2: KVM, QEMU & Virt-Manager Automation

| Filename | Description | Status |
| :--- | :--- | :--- |
| `13_kvm_ok_check.png` | Terminal showing CPU virtualization check (`kvm-ok` / `egrep`) | *[Screenshot Placeholder]* |
| `14_virt_manager_gui.png` | Virt-Manager desktop console connected to QEMU/KVM hypervisor | *[Screenshot Placeholder]* |
| `15_manage_vm_script_run.png` | Execution output of `./scripts/manage_vm.sh` taking a snapshot | *[Screenshot Placeholder]* |
| `16_systemd_service_status.png` | Terminal output of `systemctl status houserent.service` | *[Screenshot Placeholder]* |

---

## 4. Module 3: Docker Containerization

| Filename | Description | Status |
| :--- | :--- | :--- |
| `17_docker_build_output.png` | Terminal output showing `docker build -t houserent:v1.0 .` | *[Screenshot Placeholder]* |
| `18_docker_ps_healthy.png` | Output of `docker ps` showing healthy Gunicorn container on port 5000 | *[Screenshot Placeholder]* |
| `19_docker_volume_persistence.png` | SQLite data persisted on host `./data` after container recreation | *[Screenshot Placeholder]* |
| `20_docker_hub_repository.png` | Web page of Docker Hub repository with published image tag | *[Screenshot Placeholder]* |

---

## 5. Module 4: Kubernetes Orchestration (Minikube)

| Filename | Description | Status |
| :--- | :--- | :--- |
| `21_minikube_status_nodes.png` | Terminal output of `minikube start` and `kubectl get nodes` | *[Screenshot Placeholder]* |
| `22_kubectl_get_all.png` | `kubectl get all -n houserent` showing multi-replica Pods and Services | *[Screenshot Placeholder]* |
| `23_kubectl_scaling.png` | `kubectl scale deployment houserent-deployment --replicas=4` | *[Screenshot Placeholder]* |
| `24_kubectl_rolling_update.png` | `kubectl rollout status` demonstrating zero-downtime rolling update | *[Screenshot Placeholder]* |

---

## 6. Module 5: AWS Serverless (Lambda, API Gateway & S3)

| Filename | Description | Status |
| :--- | :--- | :--- |
| `25_serverless_local_tests.png` | Terminal output of `python serverless/test_local.py` passing | *[Screenshot Placeholder]* |
| `26_api_gateway_postman_test.png` | API Gateway endpoint response in Postman or curl | *[Screenshot Placeholder]* |
| `27_cloudwatch_s3_trigger_logs.png` | CloudWatch Logs showing S3 ObjectCreated Lambda event execution | *[Screenshot Placeholder]* |

---

## 7. Automated Test Suite Execution Evidence

| Filename | Description | Status |
| :--- | :--- | :--- |
| `28_pytest_28_passed.png` | Pytest console output verifying all 28 automated tests passed | *[Screenshot Placeholder]* |
