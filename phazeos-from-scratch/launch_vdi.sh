#!/bin/bash
# 🚀 PhazeOS - Auto-Launch VDI (Hard Disk)
# Launches the pre-installed VDI image

set -e

PHAZEOS_DIR="/media/jack/Liunux/secure-vpn/phazeos-from-scratch"
VDI_PATH="$PHAZEOS_DIR/PhazeOS.vdi"
VM_NAME="PhazeOS"

echo "=================================================="
echo "      🤖 PHAZEOS VDI LAUNCHER"
echo "=================================================="

# 1. CLEANUP
echo ""
echo "🧹 Cleaning up..."
pkill -f qemu-system || true
pkill -f VirtualBox || true
VBoxManage closemedium disk "$VDI_PATH" 2>/dev/null || true
VBoxManage closemedium disk "$PHAZEOS_DIR/PhazeOS_Final.vdi" 2>/dev/null || true
sleep 1

# 2. UNLOAD KVM
echo "🔌 Unloading KVM..."
if lsmod | grep -q kvm; then
    sudo modprobe -r kvm_amd kvm_intel kvm
fi

# 3. RECREATE VM
if VBoxManage list vms | grep -q "\"$VM_NAME\""; then
    echo "🗑️  Removing old VM..."
    VBoxManage controlvm "$VM_NAME" poweroff 2>/dev/null || true
    sleep 2
    VBoxManage unregistervm "$VM_NAME" --delete
fi

echo "🛠️  Creating VM..."
VBoxManage createvm --name "$VM_NAME" --ostype "Linux_64" --register

VBoxManage modifyvm "$VM_NAME" --memory 4096 --cpus 4 --vram 128 --graphicscontroller vmsvga --boot1 disk --audio-enabled off

# 4. ATTACH THE VDI WE BUILT
echo "💾 Attaching PhazeOS Hard Disk..."
VBoxManage storagectl "$VM_NAME" --name "SATA Controller" --add sata --controller IntelAhci
VBoxManage storageattach "$VM_NAME" --storagectl "SATA Controller" --port 0 --device 0 --type hdd --medium "$VDI_PATH"

# 5. LAUNCH
echo "🚀 LAUNCHING..."
VBoxManage startvm "$VM_NAME" --type gui
