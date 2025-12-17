#!/bin/bash
# PhazeOS - EMERGENCY FIX VDI
# Restores working BusyBox and ensures system is usable

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
DISK_IMG="phazeos-disk.img"
VDI_IMG="PhazeOS.vdi"
MOUNT_POINT="/mnt/phazeos-fix"

cd $PHAZEOS

echo "=========================================="
echo "  FIXING DISK IMAGE"
echo "=========================================="

# 1. Mount image
LOOP_DEV=$(sudo losetup -fP --show $DISK_IMG)
sudo mkdir -p $MOUNT_POINT
sudo mount "${LOOP_DEV}p1" $MOUNT_POINT

# 2. FIX BUSYBOX (The Foundation)
echo "🔧 Restore BusyBox..."
# Check source location
if [ -f "usr/bin/busybox" ]; then
    echo "   Found source busybox in usr/bin/"
    sudo cp -v usr/bin/busybox $MOUNT_POINT/usr/bin/
    sudo chmod 755 $MOUNT_POINT/usr/bin/busybox
else
    echo "❌ CRITICAL: Source busybox missing! Using fallback..."
    # Fallback to the static binary we downloaded earlier if needed
    if [ -f "busybox-static" ]; then
        sudo cp -v busybox-static $MOUNT_POINT/usr/bin/busybox
        sudo chmod 755 $MOUNT_POINT/usr/bin/busybox
    fi
fi

# Ensure /bin/sh exists
sudo mkdir -p $MOUNT_POINT/bin
if [ ! -e "$MOUNT_POINT/bin/sh" ]; then
    echo "   Restoring /bin/sh symlink..."
    sudo ln -sf ../usr/bin/busybox $MOUNT_POINT/bin/sh
fi

# 3. FIX LIBRARIES (Just in case)
echo "🔧 Verifying Libraries..."
if [ -f "usr/lib/libc.so.6" ]; then
    sudo cp -v usr/lib/libc.so.6 $MOUNT_POINT/lib/
    sudo cp -v usr/lib/libm.so.6 $MOUNT_POINT/lib/
    # Ensure dynamic linker is in correct place (usually /lib64)
    sudo mkdir -p $MOUNT_POINT/lib64
    sudo cp -v lib64/ld-linux-x86-64.so.2 $MOUNT_POINT/lib64/
else
    echo "⚠️  Libraries not found in source, skipping check."
fi

# 4. Cleanup
sudo umount $MOUNT_POINT
sudo losetup -d $LOOP_DEV

# 5. Re-convert
echo "🔄 Updating VDI..."
rm -f $VDI_IMG
VBoxManage convertfromraw $DISK_IMG $VDI_IMG --format VDI

echo "✅ FIXED! BusyBox verified."
echo "Running debug check again..."
./debug_disk.sh
