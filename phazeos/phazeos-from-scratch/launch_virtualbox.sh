#!/bin/bash
# 🚀 PhazeOS - Auto-Launch in VirtualBox
# This handles the KVM/VirtualBox conflict automatically

set -e

PHAZEOS_DIR="/media/jack/Liunux/secure-vpn/phazeos-from-scratch"
ISO_PATH="$PHAZEOS_DIR/iso-output/phazeos-1.0-alpha-20251213.iso"
VM_NAME="PhazeOS"

echo "=================================================="
echo "      🤖 PHAZEOS VIRTUALBOX AUTO-LAUNCHER"
echo "=================================================="

# 1. CLEANUP & PREP
echo ""
echo "🧹 Cleaning up previous sessions..."
pkill -f qemu-system || true
pkill -f VirtualBox || true
sleep 1

# 2. FIX HARDWARE CONFLICT (The Critical Step)
echo "🔌 Unloading KVM modules (Password required to free hardware for VBox)..."
if lsmod | grep -q kvm; then
    sudo modprobe -r kvm_amd kvm_intel kvm
    echo "✅ KVM unloaded. Hardware is ready for VirtualBox."
else
    echo "✅ KVM was not loaded. Good to go."
fi

# 3. DESTROY OLD VM (Start Fresh)
if VBoxManage list vms | grep -q "\"$VM_NAME\""; then
    echo "🗑️  Removing old VM..."
    VBoxManage controlvm "$VM_NAME" poweroff 2>/dev/null || true
    sleep 2
    VBoxManage unregistervm "$VM_NAME" --delete
fi

# 4. CREATE NEW VM
echo "🛠️  Creating fresh VirtualBox VM..."
VBoxManage createvm --name "$VM_NAME" --ostype "Linux_64" --register

# System Settings
VBoxManage modifyvm "$VM_NAME" \
    --memory 4096 \
    --cpus 4 \
    --vram 128 \
    --graphicscontroller vmsvga \
    --boot1 dvd \
    --boot2 disk \
    --audio-enabled off

# Storage
echo "💾 Attaching Storage..."
VBoxManage storagectl "$VM_NAME" --name "SATA Controller" --add sata --controller IntelAhci
VBoxManage storageattach "$VM_NAME" --storagectl "SATA Controller" --port 0 --device 0 --type dvddrive --medium "$ISO_PATH"

# Create a dummy hard drive (so it doesn't complain)
HDD_PATH="$PHAZEOS_DIR/${VM_NAME}.vdi"
if [ ! -f "$HDD_PATH" ]; then
    VBoxManage createmedium disk --filename "$HDD_PATH" --size 10240
fi
VBoxManage storageattach "$VM_NAME" --storagectl "SATA Controller" --port 1 --device 0 --type hdd --medium "$HDD_PATH"

# 5. LAUNCH
echo ""
echo "🚀 LAUNCHING PHAZEOS..."
echo "=================================================="
VBoxManage startvm "$VM_NAME" --type gui
 echo ""
echo "✅ Done! Look for the VirtualBox window."
