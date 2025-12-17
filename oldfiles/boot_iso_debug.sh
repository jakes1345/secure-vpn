#!/bin/bash
# Boot ISO with debug output and boot parameters

ISO_FILE="/media/jack/Liunux/secure-vpn/phazeos-build/out/phazeos-2025.12.11-x86_64.iso"

echo "=========================================="
echo "    BOOTING WITH DEBUG OPTIONS"
echo "=========================================="
echo ""
echo "This will:"
echo "  • Show serial console output"
echo "  • Add boot parameters to skip potential hangs"
echo "  • Use simpler VGA"
echo ""

# Boot with serial output visible and boot parameters
qemu-system-x86_64 \
    -enable-kvm \
    -cpu host \
    -m 6144 \
    -smp 4 \
    -cdrom "$ISO_FILE" \
    -boot d \
    -vga std \
    -display gtk \
    -serial mon:stdio \
    -no-reboot \
    -d guest_errors \
    2>&1 | tee /tmp/qemu-boot.log

echo ""
echo "Boot log saved to: /tmp/qemu-boot.log"
