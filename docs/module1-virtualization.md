# Module 1: Introduction to Virtualization

## 1. Overview and Objectives

This lab module introduces hardware virtualization fundamentals using **Oracle VM VirtualBox** on a Windows host machine. Students will create an isolated **Ubuntu Linux Virtual Machine (VM)**, configure hardware allocation (vCPUs, RAM, virtual disk storage), execute the **HouseRent** web application inside the guest operating system, take system snapshots, revert state, and clone the machine.

---

## 2. Theoretical Background

### 2.1 Type 1 vs. Type 2 Hypervisors

A **hypervisor** (also called a Virtual Machine Monitor or VMM) is software, firmware, or hardware that creates and runs virtual machines:

| Characteristic | Type 1 Hypervisor (Bare-Metal) | Type 2 Hypervisor (Hosted) |
| :--- | :--- | :--- |
| **Architecture** | Runs directly on physical hardware without a host OS. | Runs as an application inside an existing host OS (e.g., Windows). |
| **Performance** | Near-native speed; direct access to CPU/RAM. | Small performance overhead due to host OS abstraction. |
| **Examples** | VMware ESXi, Microsoft Hyper-V, Xen, KVM. | Oracle VM VirtualBox, VMware Workstation Player. |
| **Typical Use Case**| Enterprise data centers, cloud providers (AWS, Azure).| Student development environments, local testing labs. |

```
Type 1 Architecture:                     Type 2 Architecture (Used in Module 1):
+-----------------------------------+     +-----------------------------------+
|  Guest VM 1  |  Guest VM 2       |     |  Guest VM 1 (Ubuntu / HouseRent)  |
+-----------------------------------+     +-----------------------------------+
|     Type 1 Hypervisor (ESXi)      |     |  Type 2 Hypervisor (VirtualBox)   |
+-----------------------------------+     +-----------------------------------+
|     Bare-Metal Hardware           |     |     Host Operating System (Win)   |
+-----------------------------------+     +-----------------------------------+
                                          |     Bare-Metal Hardware           |
                                          +-----------------------------------+
```

### 2.2 Difference: Running HouseRent on Windows vs. Inside Ubuntu VM

1. **Kernel and Environment Isolation:**
   - On Windows, HouseRent runs as a local process sharing the Windows NT kernel, environment variables, and filesystem conventions (such as backslashes `\` and case-insensitive paths).
   - In the Ubuntu VM, HouseRent runs on top of a true Linux kernel (`ext4` filesystem, POSIX threads, standard `/` paths). Production deployment tools like **Gunicorn** run natively in Linux but are not supported on Windows.
2. **Dependency Encapsulation:**
   - Changes to the host Windows machine (Python updates, PATH edits) do not impact the Ubuntu VM.
   - If an error occurs, the VM can be wiped, rolled back, or restored within seconds without altering the host OS.
3. **Resource Partitioning:**
   - The VM has strictly dedicated resource quotas (e.g., exactly 2 CPU cores and 4096 MB RAM), preventing runaway memory leaks from freezing the host computer.

---

## 3. Step-by-Step Practical Demonstration

### Step 1: Install VirtualBox on Windows
1. Download Oracle VirtualBox (version 7.x) and the VirtualBox Extension Pack from the official website (`https://www.virtualbox.org/`).
2. Run the installer `.exe` with default networking drivers enabled.
3. Verify installation: Open Command Prompt or PowerShell and verify:
   ```cmd
   VBoxManage --version
   ```
   *Expected Output:* `7.0.x_r...`

> `[SCREENSHOT PLACEHOLDER 1.1: VirtualBox Manager UI on Windows]`

---

### Step 2: Download Ubuntu ISO Image
1. Download Ubuntu 22.04 LTS or 24.04 LTS Desktop/Server ISO (`ubuntu-22.04-desktop-amd64.iso`) from `https://ubuntu.com/download/desktop`.

---

### Step 3: Create and Configure the Ubuntu Virtual Machine
1. Open VirtualBox Manager and click **New**.
2. Set configuration parameters:
   - **Name:** `HouseRent-Ubuntu-VM`
   - **Type:** `Linux`
   - **Version:** `Ubuntu (64-bit)`
   - **Base Memory (RAM):** `4096 MB` (4 GB)
   - **Processors (vCPUs):** `2 CPUs`
   - **Virtual Hard Disk:** `Create a Virtual Hard Disk Now` -> `VDI (VirtualBox Disk Image)` -> `Dynamically Allocated` -> Size: `25 GB`
3. Network Configuration:
   - Go to **Settings** -> **Network** -> **Adapter 1**.
   - Attached to: `Bridged Adapter` (to get an IP address on your local WiFi/LAN) or `NAT` with Port Forwarding:
     - Name: `HouseRent-Rule`
     - Protocol: `TCP`
     - Host Port: `5000`
     - Guest Port: `5000`

> `[SCREENSHOT PLACEHOLDER 1.2: VM Hardware Specifications Dialog (RAM, CPU, Storage)]`

---

### Step 4: Install Ubuntu OS and Configure Guest Environment
1. Start the VM, attach the downloaded ISO, and complete the installation wizard.
2. Once booted into the Ubuntu desktop/terminal, update system packages and install Python:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3 python3-pip python3-venv git curl
   ```
3. Verify installed tools:
   ```bash
   python3 --version
   pip3 --version
   ```
   *Expected Output:* `Python 3.10.x` or `Python 3.12.x`

> `[SCREENSHOT PLACEHOLDER 1.3: Ubuntu Guest Terminal with Python and Git verified]`

---

### Step 5: Transfer and Run HouseRent Application inside Ubuntu VM
1. Clone the repository or copy the `HouseRent` folder into Ubuntu:
   ```bash
   git clone https://github.com/<your-username>/HouseRent.git
   cd HouseRent
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Seed sample database:
   ```bash
   python database/seed_data.py
   ```
5. Run the web application:
   ```bash
   python app.py
   ```
   *Expected Output:*
   ```text
   * Serving Flask app 'app'
   * Debug mode: on
   * Running on all addresses (0.0.0.0)
   * Running on http://127.0.0.1:5000
   * Running on http://192.168.x.x:5000
   ```
6. Open your Windows host browser and visit `http://localhost:5000` (or `http://<VM_IP>:5000`).

> `[SCREENSHOT PLACEHOLDER 1.4: HouseRent Homepage loaded in browser served from Ubuntu VM]`

---

### Step 6: Creating a VM Snapshot
A **snapshot** preserves the complete state, storage, and memory of the virtual machine at a specific point in time.

1. Stop the application (`Ctrl+C`).
2. In VirtualBox Manager, select `HouseRent-Ubuntu-VM`, click the hamburger icon next to the VM name, and select **Snapshots**.
3. Click **Take Snapshot**.
   - **Name:** `Clean_Python_HouseRent_Installed`
   - **Description:** `Base state with Python 3, Flask dependencies, and seeded SQLite database.`
4. Alternatively via Command Prompt on Windows:
   ```cmd
   VBoxManage snapshot "HouseRent-Ubuntu-VM" take "Clean_Python_HouseRent_Installed" --description "Base functional state"
   ```

> `[SCREENSHOT PLACEHOLDER 1.5: VirtualBox Snapshot Tree showing 'Clean_Python_HouseRent_Installed']`

---

### Step 7: Demonstrating Snapshot Restoration (Disaster Recovery)
1. Inside the Ubuntu VM, simulate an accidental corruption or file deletion:
   ```bash
   rm -rf database/houserent.db
   rm -rf templates/
   ```
2. Verify the application fails to start:
   ```bash
   python app.py
   ```
   *Error observed:* `TemplateNotFound / OperationalError`
3. Power off the VM.
4. Select the snapshot `Clean_Python_HouseRent_Installed` and click **Restore**.
5. Power on the VM and check the directory:
   ```bash
   ls database/
   ls templates/
   python app.py
   ```
   *Result:* All deleted files and the database are fully recovered!

> `[SCREENSHOT PLACEHOLDER 1.6: VM Restored successfully after simulated failure]`

---

### Step 8: Cloning the Virtual Machine
A **clone** creates a duplicate of an existing VM to scale or test without modifying the original template.

1. Power off `HouseRent-Ubuntu-VM`.
2. In VirtualBox, right-click `HouseRent-Ubuntu-VM` and choose **Clone**.
   - **New Machine Name:** `HouseRent-Ubuntu-VM-Clone`
   - **Clone Type:** **Full Clone** (independent disk image) vs. **Linked Clone** (shares base disk, saves disk space).
   - **MAC Address Policy:** `Generate new MAC addresses for all network adapters` (ensures both VMs receive distinct IP addresses).
3. Start both the primary VM and the cloned VM to demonstrate multi-instance virtualization.

> `[SCREENSHOT PLACEHOLDER 1.7: Primary VM and Cloned VM running simultaneously in VirtualBox]`

---

## 4. Key Takeaways for Project Viva

1. **Why use a Type-2 hypervisor for development?** It allows running a full production-like Linux server directly on student laptops without repartitioning hard drives or dual-booting.
2. **What is the difference between a Full Clone and a Linked Clone?** A Full Clone copies the entire virtual hard drive independently; a Linked Clone references the snapshot of the master VM and only writes new changes to a delta disk.
3. **What is guest memory ballooning?** A hypervisor technique allowing the host to reclaim unused memory from the guest VM.
