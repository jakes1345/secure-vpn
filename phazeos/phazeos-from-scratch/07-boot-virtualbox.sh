#!/bin/bash
# PhazeOS VirtualBox Setup and Boot
# Automatically creates a VM and boots PhazeOS ISO

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
ISO_PATH="$PHAZEOS/iso-output/phazeos-1.0-alpha-20251213.iso"
VM_NAME="PhazeOS-Test"

echo "=========================================="
echo "  CREATING VIRTUALBOX VM FOR PHAZEOS"
echo "=========================================="
echo ""

# Check if VM already exists, delete if it does
if VBoxManage list vms | grep -q "$VM_NAME"; then
    echo "🗑️  Removing existing VM..."
    VBoxManage unregistervm "$VM_NAME" --delete 2>/dev/null || true
fi

echo "🔧 Creating new VM: $VM_NAME"

# Create VM
VBoxManage createvm --name "$VM_NAME" --ostype "Linux_64" --register

# Configure VM
echo "⚙️  Configuring VM settings..."
VBoxManage modifyvm "$VM_NAME" \
    --memory 4096 \
    --cpus 4 \
    --boot1 dvd \
    --boot2 disk \
    --boot3 none \
    --boot4 none \
    --vram 128 \
    --graphicscontroller vmsvga \
    --audio-enabled off

# Create storage controller
echo "💾 Setting up storage..."
VBoxManage storagectl "$VM_NAME" \
    --name "IDE Controller" \
    --add ide \
    --controller PIIX4

# Attach ISO
echo "📀 Attaching PhazeOS ISO..."
VBoxManage storageattach "$VM_NAME" \
    --storagectl "IDE Controller" \
    --port 0 \
    --device 0 \
    --type dvddrive \
    --medium "$ISO_PATH"

echo "✅ VM created successfully!"
echo ""
echo "=========================================="
echo "🚀 STARTING PHAZEOS IN VIRTUALBOX"
echo "=========================================="
echo ""

# Start VM
VBoxManage startvm "$VM_NAME" --type gui

echo ""
echo "✅ PhazeOS is booting in VirtualBox!"
echo ""
echo "VM Name: $VM_NAME"
echo "Memory: 4GB"
echo "CPUs: 4"
echo "ISO: $ISO_PATH"
echo ""
echo "To stop the VM:"
echo "  VBoxManage controlvm $VM_NAME poweroff"
echo ""
echo "To delete the VM:"
echo "  VBoxManage unregistervm $VM_NAME --delete"
echo ""
