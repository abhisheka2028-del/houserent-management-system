#!/usr/bin/env bash
# ==============================================================================
# HouseRent - Module 2: KVM & Virt-Manager Automated Environment Setup
# Supported Environment: Ubuntu 22.04 / 24.04 LTS (Hardware Virtualization Required)
# ==============================================================================

set -euo pipefail

echo "============================================================"
echo "    HouseRent: KVM & libvirt Virtualization Setup Script    "
echo "============================================================"

# Step 1: Verify Hardware Virtualization Extensions (Intel VT-x or AMD-V)
echo "[1/5] Checking CPU virtualization extensions..."
CPU_VIRT_COUNT=$(egrep -c '(vmx|svm)' /proc/cpuinfo || true)

if [ "${CPU_VIRT_COUNT}" -eq 0 ]; then
    echo "[-] ERROR: Hardware virtualization (VT-x/AMD-V) is NOT enabled in your BIOS/UEFI or host hypervisor."
    echo "    If running inside a VM (nested virtualization), ensure 'Nested VT-x/AMD-V' is enabled in VM settings."
    exit 1
else
    echo "[+] SUCCESS: Hardware virtualization supported (${CPU_VIRT_COUNT} logical cores detected)."
fi

# Step 2: Install cpu-checker to verify KVM acceleration
echo "[2/5] Checking KVM kernel module support with cpu-checker..."
if ! command -v kvm-ok &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y cpu-checker
fi

if kvm-ok; then
    echo "[+] SUCCESS: KVM acceleration can be used on this system."
else
    echo "[-] WARNING: KVM acceleration reported warnings. Please verify BIOS virtualization flags."
fi

# Step 3: Install KVM, QEMU, Libvirt and Virt-Manager packages
echo "[3/5] Installing QEMU, KVM, libvirt-daemon, bridge-utils, and virt-manager..."
sudo apt-get update -y
sudo apt-get install -y \
    qemu-kvm \
    libvirt-daemon-system \
    libvirt-clients \
    bridge-utils \
    virt-manager \
    virtinst

# Step 4: Enable and Start libvirtd Systemd Service
echo "[4/5] Enabling and starting libvirtd service..."
sudo systemctl enable --now libvirtd
sudo systemctl status libvirtd --no-pager | head -n 10

# Step 5: Add current user to libvirt and kvm groups
echo "[5/5] Configuring user permissions for libvirt and kvm groups..."
sudo adduser "$USER" libvirt
sudo adduser "$USER" kvm

echo ""
echo "============================================================"
echo "[+] KVM virtualization installation completed successfully!"
echo "    NOTE: You must log out and log back in (or run 'newgrp libvirt')"
echo "    for group permission changes to take effect."
echo "    To launch GUI Virtual Machine Manager, run: virt-manager"
echo "============================================================"
