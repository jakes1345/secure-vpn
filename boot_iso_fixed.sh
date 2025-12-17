#!/bin/bash
# Fixed ISO boot script with better options

ISO_FILE="/media/jack/Liunux/secure-vpn/phazeos-build/out/archlinux-2025.12.08-x86_64.iso"
DISK_FILE="/media/jack/Liunux/secure-vpn/phazeos-test-disk.qcow2"

echo "=========================================="
echo "    BOOTING PHAZEOS ISO (FIXED)"
echo "=========================================="
echo ""

if [ ! -f "$ISO_FILE" ]; then
    echo "❌ ISO not found: $ISO_FILE"
    exit 1
fi

# Create disk if it doesn't exist
if [ ! -f "$DISK_FILE" ]; then
    echo "Creating virtual disk..."
    qemu-img create -f qcow2 "$DISK_FILE" 20G
fi

echo "✅ ISO: $(basename "$ISO_FILE")"
echo "💾 Virtual Disk: $(basename "$DISK_FILE")"
echo ""
echo "🚀 Starting QEMU..."
echo ""
echo "This version includes:"
echo "  • Virtual disk for live system"
echo "  • Better network config"
echo "  • More memory"
echo "  • VGA acceleration"
echo ""
echo "Controls: Ctrl+Alt+G (release mouse), Ctrl+Alt+Q (quit)"
echo ""

# Try with KVM first, fallback to no-KVM if needed
if [ -c /dev/kvm ]; then
    echo "Using KVM acceleration..."
    qemu-system-x86_64 \
        -enable-kvm \
        -cpu host \
        -m 6144 \
        -smp 4 \
        -drive file="$DISK_FILE",format=qcow2 \
        -cdrom "$ISO_FILE" \
        -boot d \
        -vga virtio \
        -display gtk \
        -usb -device usb-tablet \
        -netdev user,id=net0,hostfwd=tcp::2222-:22 \
        -device virtio-net,netdev=net0 \
        -rtc base=utc \
        -name "PhazeOS-Test"
else
    echo "⚠️  KVM not available, using software emulation (slower)..."
    qemu-system-x86_64 \
        -cpu qemu64 \
        -m 6144 \
        -smp 4 \
        -drive file="$DISK_FILE",format=qcow2 \
        -cdrom "$ISO_FILE" \
        -boot d \
        -vga virtio \
        -display gtk \
        -usb -device usb-tablet \
        -netdev user,id=net0,hostfwd=tcp::2222-:22 \
        -device virtio-net,netdev=net0 \
        -rtc base=utc \
        -name "PhazeOS-Test"
fi
