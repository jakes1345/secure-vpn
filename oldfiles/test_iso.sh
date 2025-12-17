#!/bin/bash
# Quick ISO Test Script - Boot PhazeOS ISO in VM

ISO_DIR="/media/jack/Liunux/secure-vpn/phazeos-build/out"
ISO_FILE=$(find "$ISO_DIR" -name "*.iso" 2>/dev/null | head -1)

echo "=========================================="
echo "    PHAZEOS ISO TESTER"
echo "=========================================="
echo ""

# Check if ISO exists
if [ -z "$ISO_FILE" ] || [ ! -f "$ISO_FILE" ]; then
    echo "❌ ISO file not found!"
    echo ""
    echo "Looking in: $ISO_DIR"
    echo ""
    echo "Available ISO files:"
    find "$ISO_DIR" -name "*.iso" 2>/dev/null || echo "  None found"
    exit 1
fi

ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)
echo "✅ Found ISO: $(basename "$ISO_FILE")"
echo "💾 Size: $ISO_SIZE"
echo "📁 Path: $ISO_FILE"
echo ""

# Check for virtualization options
QEMU_CMD=""
VIRTUALBOX_CMD=""

if command -v qemu-system-x86_64 &> /dev/null; then
    QEMU_CMD="qemu-system-x86_64"
elif command -v qemu-kvm &> /dev/null; then
    QEMU_CMD="qemu-kvm"
fi

if command -v virtualbox &> /dev/null || command -v VBoxManage &> /dev/null; then
    VIRTUALBOX_CMD="virtualbox"
fi

# Show available options
echo "Available virtualization options:"
if [ -n "$QEMU_CMD" ]; then
    echo "  ✅ QEMU/KVM available"
else
    echo "  ❌ QEMU/KVM not installed"
fi

if [ -n "$VIRTUALBOX_CMD" ]; then
    echo "  ✅ VirtualBox available"
else
    echo "  ❌ VirtualBox not installed"
fi

echo ""

# If neither is available, show installation options
if [ -z "$QEMU_CMD" ] && [ -z "$VIRTUALBOX_CMD" ]; then
    echo "=========================================="
    echo "    INSTALLATION REQUIRED"
    echo "=========================================="
    echo ""
    echo "Choose one:"
    echo ""
    echo "1️⃣  Install QEMU/KVM (Recommended - faster):"
    echo "   sudo apt update"
    echo "   sudo apt install qemu-kvm qemu-system-x86 libvirt-daemon-system"
    echo ""
    echo "2️⃣  Install VirtualBox (Easier GUI):"
    echo "   sudo apt install virtualbox"
    echo ""
    echo "3️⃣  Create bootable USB (no VM needed):"
    echo "   # Find USB device:"
    echo "   lsblk"
    echo "   # Write ISO (REPLACE sdX!):"
    echo "   sudo dd if=\"$ISO_FILE\" of=/dev/sdX bs=4M status=progress && sync"
    echo ""
    exit 1
fi

# Ask user which to use
echo "How do you want to test the ISO?"
echo ""
if [ -n "$QEMU_CMD" ]; then
    echo "1) QEMU/KVM (fast, command-line)"
fi
if [ -n "$VIRTUALBOX_CMD" ]; then
    echo "2) VirtualBox (GUI, easier to use)"
fi
echo "3) Show manual instructions"
echo ""
read -p "Choose [1-3]: " choice

case $choice in
    1)
        if [ -z "$QEMU_CMD" ]; then
            echo "❌ QEMU not available!"
            exit 1
        fi
        
        # Check for KVM support
        if [ -c /dev/kvm ]; then
            KVM_ENABLED="-enable-kvm"
            echo "✅ KVM acceleration available"
        else
            KVM_ENABLED=""
            echo "⚠️  KVM not available (will be slower)"
        fi
        
        echo ""
        echo "🚀 Starting QEMU VM..."
        echo ""
        echo "Controls:"
        echo "  • Ctrl+Alt+G - Release mouse/keyboard"
        echo "  • Ctrl+Alt+F - Toggle fullscreen"
        echo "  • Ctrl+Alt+Q - Quit QEMU"
        echo ""
        echo "Press Ctrl+C to stop the VM"
        echo ""
        
        # Boot the ISO
        $QEMU_CMD $KVM_ENABLED \
            -m 4096 \
            -smp 2 \
            -cdrom "$ISO_FILE" \
            -boot d \
            -vga qxl \
            -display sdl \
            -usb -device usb-tablet \
            -netdev user,id=net0 \
            -device virtio-net,netdev=net0
        
        echo ""
        echo "VM stopped."
        ;;
    2)
        if [ -z "$VIRTUALBOX_CMD" ]; then
            echo "❌ VirtualBox not available!"
            exit 1
        fi
        
        echo ""
        echo "=========================================="
        echo "    VIRTUALBOX SETUP"
        echo "=========================================="
        echo ""
        echo "Manual steps:"
        echo ""
        echo "1. Open VirtualBox"
        echo "2. Click 'New' to create a VM"
        echo "3. Name: PhazeOS-Test"
        echo "4. Type: Linux"
        echo "5. Version: Arch Linux (64-bit)"
        echo "6. Memory: 4096 MB (or more)"
        echo "7. Hard disk: Create virtual hard disk (20GB+ recommended)"
        echo "8. Click 'Settings' → 'Storage'"
        echo "9. Under 'Controller: IDE', click the CD icon"
        echo "10. Click 'Choose a disk file'"
        echo "11. Select: $ISO_FILE"
        echo "12. Click 'Start' to boot"
        echo ""
        echo "Opening VirtualBox..."
        virtualbox &
        echo ""
        echo "✅ VirtualBox opened. Follow the steps above."
        ;;
    3)
        echo ""
        echo "=========================================="
        echo "    MANUAL TESTING OPTIONS"
        echo "=========================================="
        echo ""
        echo "OPTION 1: QEMU/KVM (if installed)"
        echo "  qemu-system-x86_64 -enable-kvm -m 4096 -smp 2 \\"
        echo "    -cdrom \"$ISO_FILE\" -boot d"
        echo ""
        echo "OPTION 2: Create Bootable USB"
        echo "  # Find USB device:"
        echo "  lsblk"
        echo "  # Write ISO (REPLACE sdX with your USB device!):"
        echo "  sudo dd if=\"$ISO_FILE\" of=/dev/sdX bs=4M status=progress && sync"
        echo "  # Then boot from USB"
        echo ""
        echo "OPTION 3: Mount and inspect ISO"
        echo "  sudo mkdir -p /mnt/iso"
        echo "  sudo mount -o loop \"$ISO_FILE\" /mnt/iso"
        echo "  ls -la /mnt/iso"
        echo "  sudo umount /mnt/iso"
        echo ""
        echo "OPTION 4: Verify ISO integrity"
        echo "  file \"$ISO_FILE\""
        echo "  isoinfo -d -i \"$ISO_FILE\""
        ;;
    *)
        echo "Invalid choice!"
        exit 1
        ;;
esac
