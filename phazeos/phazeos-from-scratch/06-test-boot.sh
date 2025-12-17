#!/bin/bash
# PhazeOS From Scratch - Boot Test
# Tests the ISO in QEMU

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
ISO_OUTPUT=$PHAZEOS/iso-output

echo "=========================================="
echo "  TESTING PHAZEOS ISO IN QEMU"
echo "=========================================="
echo ""

# Find the ISO
ISO_FILE=$(ls -t $ISO_OUTPUT/*.iso 2>/dev/null | head -n1)

if [ -z "$ISO_FILE" ]; then
    echo "❌ No ISO file found in $ISO_OUTPUT"
    echo "Run ./05-create-iso.sh first!"
    exit 1
fi

echo "Testing ISO: $(basename $ISO_FILE)"
echo ""

# Check if QEMU is installed
if ! command -v qemu-system-x86_64 &> /dev/null; then
    echo "❌ QEMU not found!"
    echo "Install with: sudo apt install qemu-system-x86"
    exit 1
fi

echo "🚀 Starting QEMU..."
echo ""
echo "QEMU Configuration:"
echo "  - Memory: 4GB"
echo "  - CPUs: 4"
echo "  - KVM: Enabled (if available)"
echo "  - Display: GTK"
echo ""
echo "Press Ctrl+Alt+G to release mouse"
echo "Press Ctrl+Alt+F to toggle fullscreen"
echo "Close window to exit"
echo ""

# Create virtual disk for testing persistence
DISK_IMG=$ISO_OUTPUT/test-disk.qcow2
if [ ! -f $DISK_IMG ]; then
    echo "📦 Creating virtual disk for testing..."
    qemu-img create -f qcow2 $DISK_IMG 20G
    echo "✅ Virtual disk created (20GB)"
    echo ""
fi

# Run QEMU
qemu-system-x86_64 \
    -cdrom "$ISO_FILE" \
    -boot d \
    -m 4G \
    -smp 4 \
    -enable-kvm \
    -cpu host \
    -display gtk \
    -device virtio-vga-gl \
    -machine q35,accel=kvm \
    -device virtio-net-pci,netdev=net0 \
    -netdev user,id=net0 \
    -hda $DISK_IMG \
    -serial stdio \
    -name "PhazeOS 1.0 Alpha Test" \
    2>&1 | tee $PHAZEOS/build-logs/qemu-test.log

echo ""
echo "=========================================="
echo "✅ QEMU TEST COMPLETE!"
echo "=========================================="
echo ""
echo "QEMU log saved to: build-logs/qemu-test.log"
echo ""
