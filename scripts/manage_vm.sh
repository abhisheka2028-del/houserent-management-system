#!/usr/bin/env bash
# ==============================================================================
# HouseRent - Module 2: Virtual Machine Lifecycle Automation Script
# Automates virsh operations: start, stop, snapshot, clone, and status
# ==============================================================================

set -euo pipefail

VM_NAME="${1:-houserent-vm}"
ACTION="${2:-status}"

usage() {
    echo "Usage: $0 [VM_NAME] [ACTION] [ARGUMENT]"
    echo ""
    echo "Actions:"
    echo "  status               - Show VM state, CPU, and memory"
    echo "  start                - Power on the virtual machine"
    echo "  stop                 - Gracefully shut down the VM"
    echo "  force-stop           - Forcibly power off the VM (destroy)"
    echo "  restart              - Reboot the VM"
    echo "  ip                   - Display assigned IP address of the VM"
    echo "  snapshot-create <NAME> - Take a snapshot of the VM state"
    echo "  snapshot-list        - List all snapshots of this VM"
    echo "  snapshot-revert <NAME> - Revert VM state to a saved snapshot"
    echo "  clone <NEW_VM_NAME>  - Clone this VM to a new virtual machine"
    echo ""
    echo "Example: $0 houserent-vm start"
    echo "Example: $0 houserent-vm snapshot-create snap_pre_update"
}

case "${ACTION}" in
    status)
        echo "=== Status of VM: ${VM_NAME} ==="
        virsh dominfo "${VM_NAME}" || {
            echo "[-] VM '${VM_NAME}' not found. List of all VMs:"
            virsh list --all
        }
        ;;

    start)
        echo "[+] Starting VM: ${VM_NAME}..."
        virsh start "${VM_NAME}"
        echo "[+] VM started. Waiting for network assignment..."
        sleep 5
        virsh domifaddr "${VM_NAME}" || true
        ;;

    stop)
        echo "[*] Requesting graceful ACPI shutdown for: ${VM_NAME}..."
        virsh shutdown "${VM_NAME}"
        ;;

    force-stop)
        echo "[!] Forcibly destroying VM: ${VM_NAME}..."
        virsh destroy "${VM_NAME}"
        ;;

    restart)
        echo "[*] Rebooting VM: ${VM_NAME}..."
        virsh reboot "${VM_NAME}"
        ;;

    ip)
        echo "=== IP Addresses for: ${VM_NAME} ==="
        virsh domifaddr "${VM_NAME}"
        ;;

    snapshot-create)
        SNAP_NAME="${3:-snap_$(date +%Y%m%d_%H%M%S)}"
        echo "[+] Creating snapshot '${SNAP_NAME}' for VM: ${VM_NAME}..."
        virsh snapshot-create-as --domain "${VM_NAME}" --name "${SNAP_NAME}" --description "Automated snapshot from manage_vm.sh"
        echo "[+] Snapshot created successfully."
        ;;

    snapshot-list)
        echo "=== Snapshots for VM: ${VM_NAME} ==="
        virsh snapshot-list "${VM_NAME}"
        ;;

    snapshot-revert)
        SNAP_NAME="${3:?Error: Snapshot name argument required}"
        echo "[!] Reverting VM '${VM_NAME}' to snapshot: ${SNAP_NAME}..."
        virsh snapshot-revert --domain "${VM_NAME}" --snapshotname "${SNAP_NAME}"
        echo "[+] VM reverted successfully."
        ;;

    clone)
        NEW_VM="${3:?Error: Target clone VM name required}"
        echo "[+] Cloning VM '${VM_NAME}' into new VM '${NEW_VM}'..."
        virt-clone --original "${VM_NAME}" --name "${NEW_VM}" --auto-clone
        echo "[+] VM cloned successfully. New VM: ${NEW_VM}"
        ;;

    *)
        usage
        exit 1
        ;;
esac
