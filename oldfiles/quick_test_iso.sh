#!/bin/bash
# Quick test PhazeOS ISO in QEMU

ISO_PATH="/media/jack/Liunux/secure-vpn/phazeos-build/out"
# Use the LATEST ISO (Dec 11 - 7.5GB with all packages)
ISO_FILE="$ISO_PATH/phazeos-2025.12.11-x86_64.iso"

echo "=========================================="
echo "    PHAZEOS ISO - QUICK TEST OPTIONS"
echo "=========================================="
echo ""

if [ ! -f "$ISO_FILE" ]; then
    echo "❌ ISO not found: $ISO_FILE"
    echo "Available ISOs:"
    ls -lh "$ISO_PATH"/*.iso 2>/dev/null
    exit 1
fi

ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)
echo "✅ ISO: $(basename "$ISO_FILE")"
echo "💾 Size: $ISO_SIZE"
echo "📁 Path: $ISO_FILE"
echo ""

echo "=========================================="
echo "    TEST OPTIONS"
echo "=========================================="
echo ""

echo "1️⃣  INSTALL QEMU & TEST NOW (Recommended)"
echo "   Fastest option - installs and boots immediately:"
echo ""
echo "   sudo apt update && sudo apt install -y qemu-kvm qemu-system-x86"
echo "   qemu-system-x86_64 -enable-kvm -m 4096 -smp 2 -cdrom \"$ISO_FILE\" -boot d"
echo ""

echo "2️⃣  INSTALL VIRTUALBOX & TEST"
echo "   GUI option - easier to use:"
echo ""
echo "   sudo apt install -y virtualbox"
echo "   # Then open VirtualBox GUI and create VM with this ISO"
echo ""

echo "3️⃣  VERIFY ISO (No VM needed)"
echo "   Check if ISO is valid:"
echo ""
echo "   file \"$ISO_FILE\""
echo "   isoinfo -d -i \"$ISO_FILE\" 2>/dev/null || echo 'Install genisoimage for detailed info'"
echo ""

echo "4️⃣  MOUNT & INSPECT ISO"
echo "   Look at ISO contents:"
echo ""
echo "   sudo mkdir -p /mnt/phazeos-iso"
echo "   sudo mount -o loop \"$ISO_FILE\" /mnt/phazeos-iso"
echo "   ls -la /mnt/phazeos-iso"
echo "   sudo umount /mnt/phazeos-iso"
echo ""

echo "5️⃣  CREATE BOOTABLE USB"
echo "   Test on real hardware:"
echo ""
echo "   # Find USB: lsblk"
echo "   # Write ISO (REPLACE sdX!):"
echo "   sudo dd if=\"$ISO_FILE\" of=/dev/sdX bs=4M status=progress && sync"
echo ""

echo "=========================================="
echo "    QUICK COMMANDS"
echo "=========================================="
echo ""
echo "# Install QEMU and boot:"
echo "sudo apt install -y qemu-kvm qemu-system-x86 && \\"
echo "qemu-system-x86_64 -enable-kvm -m 4096 -smp 2 -cdrom \"$ISO_FILE\" -boot d"
echo ""
echo "# Or just verify ISO:"
echo "file \"$ISO_FILE\""
echo ""
