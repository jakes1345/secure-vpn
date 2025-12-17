#!/bin/bash
# PhazeOS - Fix Library Paths
# Ensures the dynamic linker and libc are found where the kernel expects them.

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch

echo "=========================================="
echo "  FIXING LIBRARY PATHS"
echo "=========================================="

# 1. Ensure lib64 exists
if [ ! -d "$PHAZEOS/lib64" ]; then
    echo "Creating /lib64..."
    mkdir -p "$PHAZEOS/lib64"
fi

# 2. Link the Dynamic Loader (CRITICAL)
# The binary expects /lib64/ld-linux-x86-64.so.2
# We have it in /usr/lib/ld-linux-x86-64.so.2
echo "Linking Dynamic Loader..."
rm -f "$PHAZEOS/lib64/ld-linux-x86-64.so.2"
ln -sfv ../usr/lib/ld-linux-x86-64.so.2 "$PHAZEOS/lib64/ld-linux-x86-64.so.2"

# 3. Ensure /lib points effectively or contains essential libs
# Some binaries look in /lib for libc.so.6
if [ ! -d "$PHAZEOS/lib" ]; then
    mkdir -p "$PHAZEOS/lib"
fi

echo "Linking libc.so.6 to /lib (just in case)..."
# Check if /lib/libc.so.6 exists, if not link it
if [ ! -f "$PHAZEOS/lib/libc.so.6" ]; then
    ln -sfv ../usr/lib/libc.so.6 "$PHAZEOS/lib/libc.so.6"
fi

# 4. Check for magic directory structure
# Some distros symlink /lib64 -> /usr/lib64 and /lib -> /usr/lib
# We are doing a split approach, which is fine as long as files are found.

echo "✅ Library paths fixed."
