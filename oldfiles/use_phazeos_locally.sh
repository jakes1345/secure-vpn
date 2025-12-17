#!/bin/bash
# PhazeOS Local Testing & Usage Script

ISO_DIR="/media/jack/Liunux/secure-vpn/phazeos-build/out"
ISO_FILE=$(find "$ISO_DIR" -name "*.iso" 2>/dev/null | head -1)

echo "=========================================="
echo "    PHAZEOS - LOCAL USAGE GUIDE"
echo "=========================================="
echo ""

if [ -z "$ISO_FILE" ]; then
    echo "❌ ISO not found yet!"
    echo "Build is still in progress."
    echo ""
    echo "Check progress with:"
    echo "  ./check_build_progress.sh"
    exit 1
fi

ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)
ISO_NAME=$(basename "$ISO_FILE")

echo "✅ ISO Ready!"
echo "📦 File: $ISO_NAME"
echo "💾 Size: $ISO_SIZE"
echo "📁 Location: $ISO_FILE"
echo ""
echo "=========================================="
echo "    WHAT YOU CAN DO NOW"
echo "=========================================="
echo ""

echo "1️⃣  TEST IN VIRTUAL MACHINE (Recommended First)"
echo "   Quick test without affecting your system:"
echo ""
echo "   # Using QEMU/KVM:"
echo "   qemu-system-x86_64 -enable-kvm -m 4096 -smp 2 \\"
echo "     -cdrom \"$ISO_FILE\" \\"
echo "     -boot d"
echo ""
echo "   # Using VirtualBox:"
echo "   - Create new VM (Type: Linux, Version: Arch Linux)"
echo "   - Set RAM: 4096MB+"
echo "   - Attach ISO as optical drive"
echo "   - Boot and test"
echo ""

echo "2️⃣  CREATE BOOTABLE USB"
echo "   Install to real hardware:"
echo ""
echo "   # Find your USB device:"
echo "   lsblk"
echo ""
echo "   # Write ISO to USB (REPLACE sdX with your device!):"
echo "   sudo dd if=\"$ISO_FILE\" of=/dev/sdX bs=4M status=progress && sync"
echo ""
echo "   ⚠️  WARNING: This will ERASE everything on the USB!"
echo ""

echo "3️⃣  SHARE WITH OTHERS"
echo "   Copy to external drive or share via:"
echo ""
echo "   # Copy to external drive:"
echo "   cp \"$ISO_FILE\" /path/to/external/drive/"
echo ""
echo "   # Or create a torrent/magnet link"
echo "   # Or upload to file sharing service"
echo ""

echo "4️⃣  VERIFY ISO INTEGRITY"
echo "   Create checksum for verification:"
echo ""
echo "   sha256sum \"$ISO_FILE\" > phazeos.sha256"
echo "   cat phazeos.sha256"
echo ""

echo "=========================================="
echo "    INSTALLATION TIPS"
echo "=========================================="
echo ""
echo "📖 Full guide: PHAZEOS_INSTALLATION_GUIDE.md"
echo ""
echo "Quick tips:"
echo "  • Minimum 20GB disk space"
echo "  • UEFI boot required"
echo "  • After install, run: sudo bash /root/phazeos_customize.sh"
echo "  • Default user: Create during installation"
echo ""

echo "=========================================="
echo "    NEED HELP?"
echo "=========================================="
echo ""
echo "Build issues:"
echo "  tail -f phazeos_rebuild.log"
echo ""
echo "Test in VM first before installing to real hardware!"
echo ""
