#!/bin/bash
# Rebuild PhazeOS Kernel with ISO9660 Support

set -e

echo "========================================"
echo "🔨 Rebuilding Kernel with ISO9660"
echo "========================================"
echo ""

cd /media/jack/Liunux/secure-vpn/phazeos-from-scratch/kernel/linux-6.7.4

# Enable ISO9660 filesystem support in kernel config
echo "📝 Enabling ISO9660 in kernel config..."

# Add ISO9660 support if not present
if ! grep -q "CONFIG_ISO9660_FS=y" .config; then
    echo "CONFIG_ISO9660_FS=y" >> .config
fi

if ! grep -q "CONFIG_JOLIET=y" .config; then
    echo "CONFIG_JOLIET=y" >> .config
fi

if ! grep -q "CONFIG_ZISOFS=y" .config; then
    echo "CONFIG_ZISOFS=y" >> .config
fi

# Also ensure CD-ROM support
if ! grep -q "CONFIG_BLK_DEV_SR=y" .config; then
    echo "CONFIG_BLK_DEV_SR=y" >> .config
fi

if ! grep -q "CONFIG_CHR_DEV_SG=y" .config; then
    echo "CONFIG_CHR_DEV_SG=y" >> .config
fi

# Run olddefconfig to resolve dependencies
echo "🔧 Resolving dependencies..."
make olddefconfig

echo ""
echo "✅ Kernel config updated with:"
grep -E "CONFIG_ISO9660|CONFIG_JOLIET|CONFIG_ZISOFS|CONFIG_BLK_DEV_SR" .config

echo ""
echo "🔨 Building kernel (this will take 10-20 minutes)..."
echo "Using $(nproc) CPU cores..."

# Build kernel
make -j$(nproc) 2>&1 | tee ../../kernel-rebuild.log | grep -E "CC|LD|INSTALL|Building|Kernel:"

# Copy new kernel
echo ""
echo "📦 Installing new kernel..."
cp arch/x86/boot/bzImage ../../boot/vmlinuz-6.7.4-phazeos

echo ""
echo "✅ Kernel rebuilt successfully!"
echo "New kernel: ../../boot/vmlinuz-6.7.4-phazeos"
ls -lh ../../boot/vmlinuz-6.7.4-phazeos

echo ""
echo "Next: Rebuild ISO with new kernel"
