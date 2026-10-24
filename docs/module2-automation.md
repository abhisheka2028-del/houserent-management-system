# Module 2: Virtualization Tools and Automation

## 1. Overview and Prerequisites

While Module 1 demonstrated graphical Type-2 virtualization using VirtualBox on Windows, **Module 2 explores enterprise-grade Linux Kernel-based Virtual Machine (KVM) and `libvirt` automation**.

> **Important Host OS Notice:** KVM is a native Linux kernel virtualization module and cannot run natively on Windows without a Linux host or a Linux VM with nested virtualization enabled. This demonstration is designed to be executed inside a native Linux environment (such as an Ubuntu 22.04/24.04 desktop/server) or an Ubuntu VM configured with **Nested Hardware Virtualization** (Intel VT-x / AMD-V pass-through).

---

## 2. Theoretical Background: KVM, QEMU, and Libvirt

- **KVM (Kernel-based Virtual Machine):** A Linux kernel module that turns Linux into a Type-1 hypervisor. It utilizes hardware extensions (`Intel VT-x` or `AMD-V`) to execute guest code directly on the physical processor.
- **QEMU (Quick EMUlator):** Provides software emulation for peripherals (disk controllers, network cards, graphics adapters, serial ports) that attach to the KVM core.
- **Libvirt (`libvirtd`):** An open-source management daemon and API that provides a unified, scriptable interface to manage KVM, QEMU, LXC, and Xen virtual machines.
- **`virsh`:** The command-line management tool for `libvirt`.
- **Virt-Manager:** The desktop graphical management console built on top of `libvirt`.

```
+-------------------------------------------------------------+
|    User Tools: virt-manager (GUI)  /  virsh (CLI Script)    |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                     libvirtd Daemon                         |
+-------------------------------------------------------------+
                              |
         +--------------------+--------------------+
         |                                         |
         v                                         v
+------------------+                      +------------------+
|  QEMU Device     |                      |    KVM Kernel    |
|    Emulation     |                      |      Module      |
+------------------+                      +------------------+
         |                                         |
         +--------------------+--------------------+
                              |
                              v
+-------------------------------------------------------------+
|                 Hardware (Intel VT-x / AMD-V)               |
+-------------------------------------------------------------+
```

---

## 3. Step-by-Step Practical Demonstration

### Step 1: Verify Hardware Virtualization Extensions
Before installing KVM, verify that the CPU supports virtualization and that it is enabled in the BIOS/UEFI:

```bash
# Count number of CPU cores with virtualization flags
egrep -c '(vmx|svm)' /proc/cpuinfo
```
- `vmx` indicates Intel VT-x.
- `svm` indicates AMD-V (AMD SVM).
- If output is `0`, virtualization is disabled in BIOS or nested virtualization is disabled on your hypervisor.

Install and run `cpu-checker`:
```bash
sudo apt update
sudo apt install -y cpu-checker
kvm-ok
```
*Expected Output:*
```text
INFO: /dev/kvm exists
KVM acceleration can be used
```

> `[SCREENSHOT PLACEHOLDER 2.1: Terminal showing successful kvm-ok output]`

---

### Step 2: Automated KVM Package Installation
We have provided an automated setup script in `scripts/setup_kvm.sh`.

Review and execute the script:
```bash
chmod +x scripts/setup_kvm.sh
./scripts/setup_kvm.sh
```

The script automatically executes:
```bash
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager virtinst
sudo systemctl enable --now libvirtd
sudo adduser "$USER" libvirt
sudo adduser "$USER" kvm
```

Apply group membership changes without rebooting:
```bash
newgrp libvirt
```

Verify that the `libvirtd` daemon is running:
```bash
systemctl status libvirtd --no-pager
```

> `[SCREENSHOT PLACEHOLDER 2.2: libvirtd service active and running in terminal]`

---

### Step 3: Launching Virt-Manager (GUI)
Launch the graphical console to visually inspect the hypervisor:
```bash
virt-manager
```
In the Virt-Manager window, you can view hypervisor resource consumption (CPU, Memory, Disk I/O) and network virtual switches (`default` NAT bridge `virbr0`).

> `[SCREENSHOT PLACEHOLDER 2.3: Virt-Manager GUI connected to QEMU/KVM hypervisor]`

---

### Step 4: Creating a VM via CLI with `virt-install`
Automate virtual machine creation with non-interactive CLI commands:

```bash
virt-install \
  --name houserent-kvm-vm \
  --ram 4096 \
  --vcpus 2 \
  --disk path=/var/lib/libvirt/images/houserent-kvm.qcow2,size=20,format=qcow2 \
  --os-variant ubuntu22.04 \
  --network network=default \
  --graphics none \
  --location 'http://archive.ubuntu.com/ubuntu/dists/jammy/main/installer-amd64/' \
  --extra-args 'console=ttyS0,115200n8 serial'
```

---

### Step 5: Automating VM Operations with `scripts/manage_vm.sh`
We have packaged complete VM lifecycle automation into `scripts/manage_vm.sh`.

#### 1. Inspect Virtual Machine Status
```bash
./scripts/manage_vm.sh houserent-kvm-vm status
```
*Expected Output:*
```text
=== Status of VM: houserent-kvm-vm ===
Id:             1
Name:           houserent-kvm-vm
UUID:           7b4f5a...
OS Type:        hvm
State:          running
CPU(s):         2
Max memory:     4194304 KiB
Used memory:    4194304 KiB
```

#### 2. Obtain Dynamic IP Address Assigned by libvirt DHCP
```bash
./scripts/manage_vm.sh houserent-kvm-vm ip
```
*Expected Output:*
```text
=== IP Addresses for: houserent-kvm-vm ===
 Name       MAC address          Protocol     Address
-------------------------------------------------------------------------------
 vnet0      52:54:00:8f:2b:11    ipv4         192.168.122.85/24
```

#### 3. Take an Automated Snapshot
```bash
./scripts/manage_vm.sh houserent-kvm-vm snapshot-create snapshot_v1_baseline
```

#### 4. List Existing Snapshots
```bash
./scripts/manage_vm.sh houserent-kvm-vm snapshot-list
```

#### 5. Gracefully Shut Down the VM
```bash
./scripts/manage_vm.sh houserent-kvm-vm stop
```

#### 6. Clone the Virtual Machine
```bash
./scripts/manage_vm.sh houserent-kvm-vm clone houserent-kvm-backup-vm
```

> `[SCREENSHOT PLACEHOLDER 2.4: Execution output of manage_vm.sh performing snapshot and clone]`

---

### Step 6: Running HouseRent as a Linux systemd Service Inside the VM
To ensure the HouseRent web server restarts automatically when the VM boots, configure a `systemd` service unit:

1. SSH into the VM:
   ```bash
   ssh ubuntu@192.168.122.85
   ```
2. Create systemd service file `/etc/systemd/system/houserent.service`:
   ```ini
   [Unit]
   Description=HouseRent Web Application Service
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/HouseRent
   ExecStart=/home/ubuntu/HouseRent/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
   Restart=always
   Environment=FLASK_ENV=production
   Environment=SECRET_KEY=production-kvm-systemd-key

   [Install]
   WantedBy=multi-user.target
   ```
3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now houserent.service
   sudo systemctl status houserent.service
   ```
4. Access the web application from the host browser via the VM IP:
   `http://192.168.122.85:5000`

> `[SCREENSHOT PLACEHOLDER 2.5: systemctl status showing active (running) houserent.service]`

---

## 4. Common Troubleshooting Scenarios

### Error 1: Permission Denied on `/dev/kvm`
- **Symptom:** `error: failed to connect to the hypervisor: Permission denied on /dev/kvm`
- **Root Cause:** Current user is not in the `kvm` or `libvirt` group.
- **Fix:** Run `sudo usermod -aG kvm,libvirt $USER` and log out/in. Verify with `groups`.

### Error 2: `libvirtd.service` Fails to Start
- **Symptom:** `Failed to start libvirtd.service: Unit is masked or socket missing`
- **Fix:** Run `sudo systemctl unmask libvirtd && sudo systemctl restart libvirtd`.

### Error 3: Nested Virtualization Disabled on Host
- **Symptom:** `KVM acceleration not available: CPU does not support hardware virtualization`
- **Fix:** If running Ubuntu inside VirtualBox or Hyper-V, enable nested virtualization:
  - In VirtualBox: VM Settings -> System -> Processor -> Check **Enable Nested VT-x/AMD-V**.
  - In PowerShell (for Hyper-V): `Set-VMProcessor -VMName "UbuntuVM" -ExposeVirtualizationExtensions $true`.
