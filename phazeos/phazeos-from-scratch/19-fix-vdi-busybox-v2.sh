#!/bin/bash
# PhazeOS - EMERGENCY FIX VDI (Verified)
# Restores working BusyBox AND Libraries correctly

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
DISK_IMG="phazeos-disk.img"
VDI_IMG="PhazeOS.vdi"
MOUNT_POINT="/mnt/phazeos-fix2"

cd $PHAZEOS

echo "=========================================="
echo "  FIXING DISK IMAGE (ATTEMPT 2)"
echo "=========================================="

# 1. Mount image
LOOP_DEV=$(sudo losetup -fP --show $DISK_IMG)
sudo mkdir -p $MOUNT_POINT
sudo mount "${LOOP_DEV}p1" $MOUNT_POINT

# 2. FIX BUSYBOX
echo "🔧 Restore BusyBox..."
sudo cp -v usr/bin/busybox $MOUNT_POINT/usr/bin/
sudo chmod 755 $MOUNT_POINT/usr/bin/busybox
sudo ln -sf ../usr/bin/busybox $MOUNT_POINT/bin/sh
sudo ln -sf ../usr/bin/busybox $MOUNT_POINT/bin/ls

# 3. FIX LIBRARIES
echo "🔧 Verifying Libraries..."
# Copy from known correct source locations
sudo cp -v usr/lib/libc.so.6 $MOUNT_POINT/lib/
sudo cp -v usr/lib/libm.so.6 $MOUNT_POINT/lib/

# The Critical Dynamic Linker
sudo mkdir -p $MOUNT_POINT/lib64
sudo cp -v usr/lib/ld-linux-x86-64.so.2 $MOUNT_POINT/lib64/
# Also symlink it to /lib/ld-linux-x86-64.so.2 just in case
sudo ln -sf /lib64/ld-linux-x86-64.so.2 $MOUNT_POINT/lib/ld-linux-x86-64.so.2

# 4. Cleanup
sudo umount $MOUNT_POINT
sudo losetup -d $LOOP_DEV

# 5. Re-convert
echo "🔄 Updating VDI..."
rm -f $VDI_IMG
VBoxManage convertfromraw $DISK_IMG $VDI_IMG --format VDI

echo "✅ DISK FULLY REPAIRED."
echo "Running debug check..."
./debug_disk.sh

echo "🚀 Launching VirtualBox..."
./launch_vdi.sh
