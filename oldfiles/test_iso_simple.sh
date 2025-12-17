#!/bin/bash
# Simple ISO test - minimal config to see if it boots

ISO_FILE="/media/jack/Liunux/secure-vpn/phazeos-build/out/archlinux-2025.12.08-x86_64.iso"

echo "Testing ISO with minimal QEMU config..."
echo "ISO: $ISO_FILE"
echo ""

# Try simplest possible boot
qemu-system-x86_64 \
    -enable-kvm \
    -m 4096 \
    -smp 2 \
    -cdrom "$ISO_FILE" \
    -boot d \
    -vga std \
    -display gtk \
    -serial stdio
