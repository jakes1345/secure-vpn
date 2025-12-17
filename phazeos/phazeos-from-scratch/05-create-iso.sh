#!/bin/bash
# PhazeOS From Scratch - ISO Creation
# Creates a bootable ISO image

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
ISO_ROOT=$PHAZEOS/iso-root
ISO_OUTPUT=$PHAZEOS/iso-output
LOGS=$PHAZEOS/build-logs

mkdir -p $ISO_ROOT $ISO_OUTPUT

echo "=========================================="
echo "  CREATING PHAZEOS BOOTABLE ISO"
echo "=========================================="
echo ""

# Copy system to ISO staging area
echo "📦 Copying system files to ISO staging area..."
rsync -av --progress $PHAZEOS/boot $ISO_ROOT/ 2>&1 | tee $LOGS/iso-copy-boot.log
rsync -av --progress $PHAZEOS/usr $ISO_ROOT/ 2>&1 | tee $LOGS/iso-copy-usr.log
rsync -av --progress $PHAZEOS/etc $ISO_ROOT/ 2>&1 | tee $LOGS/iso-copy-etc.log
rsync -av --progress $PHAZEOS/lib $ISO_ROOT/ 2>&1 | tee $LOGS/iso-copy-lib.log
rsync -av --progress $PHAZEOS/bin $ISO_ROOT/ 2>&1 | tee $LOGS/iso-copy-bin.log
rsync -av --progress $PHAZEOS/sbin $ISO_ROOT/ 2>&1 | tee $LOGS/iso-copy-sbin.log

echo "✅ System files copied!"
echo ""

# Create ISO directory structure
mkdir -p $ISO_ROOT/boot/grub

# Install GRUB
echo "🔧 Installing GRUB bootloader..."

# Create GRUB config
cat > $ISO_ROOT/boot/grub/grub.cfg << 'GRUBEOF'
set timeout=5
set default=0

menuentry "PhazeOS 1.0 Alpha" {
    linux /boot/vmlinuz-6.7.4-phazeos root=/dev/ram0 init=/sbin/init quiet splash
    initrd /boot/initramfs-6.7.4-phazeos.img
}

menuentry "PhazeOS 1.0 Alpha (Safe Mode)" {
    linux /boot/vmlinuz-6.7.4-phazeos root=/dev/ram0 init=/sbin/init nomodeset
    initrd /boot/initramfs-6.7.4-phazeos.img
}

menuentry "PhazeOS 1.0 Alpha (Debug Mode)" {
    linux /boot/vmlinuz-6.7.4-phazeos root=/dev/ram0 init=/sbin/init debug
    initrd /boot/initramfs-6.7.4-phazeos.img
}
GRUBEOF

echo "✅ GRUB configured!"
echo ""

# Create isolinux config for BIOS boot
echo "🔧 Creating isolinux configuration..."
mkdir -p $ISO_ROOT/isolinux

cat > $ISO_ROOT/isolinux/isolinux.cfg << 'ISOLINUXEOF'
DEFAULT phazeos
TIMEOUT 50
PROMPT 1

LABEL phazeos
    KERNEL /boot/vmlinuz-6.7.4-phazeos
    APPEND initrd=/boot/initramfs-6.7.4-phazeos.img root=/dev/ram0 init=/sbin/init quiet splash

LABEL safe
    KERNEL /boot/vmlinuz-6.7.4-phazeos
    APPEND initrd=/boot/initramfs-6.7.4-phazeos.img root=/dev/ram0 init=/sbin/init nomodeset

LABEL debug
    KERNEL /boot/vmlinuz-6.7.4-phazeos
    APPEND initrd=/boot/initramfs-6.7.4-phazeos.img root=/dev/ram0 init=/sbin/init debug
ISOLINUXEOF

# Copy isolinux files
if [ -f /usr/lib/syslinux/bios/isolinux.bin ]; then
    cp /usr/lib/syslinux/bios/isolinux.bin $ISO_ROOT/isolinux/
    cp /usr/lib/syslinux/bios/ldlinux.c32 $ISO_ROOT/isolinux/
elif [ -f /usr/lib/ISOLINUX/isolinux.bin ]; then
    cp /usr/lib/ISOLINUX/isolinux.bin $ISO_ROOT/isolinux/
    cp /usr/lib/syslinux/modules/bios/ldlinux.c32 $ISO_ROOT/isolinux/
fi

echo "✅ Isolinux configured!"
echo ""

# Create ISO info file
cat > $ISO_ROOT/phazeos-info.txt << 'EOF'
========================================
  PHAZEOS 1.0 ALPHA - LIVE ISO
========================================

Welcome to PhazeOS!

This is a LIVE ISO of PhazeOS 1.0 Alpha.

Features:
- Custom Linux kernel 6.7.4-phazeos
- Gaming optimizations (1000 Hz, low-latency)
- Security hardening (AppArmor, YAMA)
- Privacy features built-in
- VPN support (WireGuard, OpenVPN)

This is a minimal system. To install additional
packages, you'll need the PhazeOS package manager
(coming in Phase 2).

Boot to shell to explore the system!

Website: https://phazeos.org
Support: https://phazeos.org/support

Built: $(date)
========================================
EOF

# Create version file
echo "1.0-alpha" > $ISO_ROOT/phazeos-version

# Generate ISO
echo "🔥 Generating ISO image..."

ISO_NAME="phazeos-1.0-alpha-$(date +%Y%m%d).iso"

# Check if we have the required tools
if command -v xorriso &> /dev/null; then
    # Using xorriso (modern method)
    xorriso -as mkisofs \
        -iso-level 3 \
        -full-iso9660-filenames \
        -volid "PHAZEOS_1_0" \
        -eltorito-boot isolinux/isolinux.bin \
        -eltorito-catalog isolinux/boot.cat \
        -no-emul-boot \
        -boot-load-size 4 \
        -boot-info-table \
        -isohybrid-mbr /usr/lib/syslinux/bios/isohdpfx.bin \
        -eltorito-alt-boot \
        -e boot/grub/efi.img \
        -no-emul-boot \
        -isohybrid-gpt-basdat \
        -output $ISO_OUTPUT/$ISO_NAME \
        $ISO_ROOT 2>&1 | tee $LOGS/iso-create.log
        
elif command -v genisoimage &> /dev/null; then
    # Using genisoimage (older method)
    genisoimage \
        -rational-rock \
        -volid "PHAZEOS_1_0" \
        -cache-inodes \
        -joliet \
        -full-iso9660-filenames \
        -b isolinux/isolinux.bin \
        -c isolinux/boot.cat \
        -no-emul-boot \
        -boot-load-size 4 \
        -boot-info-table \
        -output $ISO_OUTPUT/$ISO_NAME \
        $ISO_ROOT 2>&1 | tee $LOGS/iso-create.log
        
    # Make it bootable
    if command -v isohybrid &> /dev/null; then
        isohybrid $ISO_OUTPUT/$ISO_NAME 2>&1 | tee -a $LOGS/iso-create.log
    fi
else
    echo "❌ Error: Neither xorriso nor genisoimage found!"
    echo "Install with: sudo apt install xorriso"
    exit 1
fi

echo "✅ ISO created!"
echo ""

# Calculate checksums
echo "🔐 Generating checksums..."
cd $ISO_OUTPUT
sha256sum $ISO_NAME > $ISO_NAME.sha256
md5sum $ISO_NAME > $ISO_NAME.md5

echo "✅ Checksums generated!"
echo ""

# Get ISO size
ISO_SIZE=$(du -h $ISO_OUTPUT/$ISO_NAME | cut -f1)

# Create ISO info
cat > $ISO_OUTPUT/ISO-INFO.txt << EOF
PhazeOS 1.0 Alpha ISO Information
==================================

Filename: $ISO_NAME
Size: $ISO_SIZE
Build Date: $(date)

Checksums:
  MD5: $(cat $ISO_NAME.md5 | cut -d' ' -f1)
  SHA256: $(cat $ISO_NAME.sha256 | cut -d' ' -f1)

Boot Methods:
- BIOS (Legacy): isolinux
- UEFI: GRUB2

Default Boot Options:
1. PhazeOS 1.0 Alpha (normal boot)
2. PhazeOS 1.0 Alpha (safe mode - nomodeset)
3. PhazeOS 1.0 Alpha (debug mode)

To test this ISO:
  ./06-test-boot.sh

To write to USB:
  sudo dd if=$ISO_NAME of=/dev/sdX bs=4M status=progress

To test in VirtualBox:
  Create new VM, attach ISO, boot

To test in QEMU:
  qemu-system-x86_64 -cdrom $ISO_NAME -m 4G -enable-kvm

For more information:
  See README.md in phazeos-from-scratch directory

========================================
EOF

echo "=========================================="
echo "✅ ISO CREATION COMPLETE!"
echo "=========================================="
echo ""
echo "ISO created: $ISO_OUTPUT/$ISO_NAME"
echo "Size: $ISO_SIZE"
echo ""
echo "Checksums:"
echo "  MD5: $(cat $ISO_NAME.md5 | cut -d' ' -f1)"
echo "  SHA256: $(cat $ISO_NAME.sha256 | cut -d' ' -f1)"
echo ""
echo "Next step: ./06-test-boot.sh"
echo ""
