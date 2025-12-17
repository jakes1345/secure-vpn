#!/bin/bash
# PhazeOS - DEBUG DISK IMAGE
# Mounts the image and checks what is ACTUALLY inside

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
DISK_IMG="phazeos-disk.img"
MOUNT_POINT="/mnt/phazeos-debug"

cd $PHAZEOS

echo "=========================================="
echo "  DEBUGGING DISK IMAGE"
echo "=========================================="

if [ ! -f "$DISK_IMG" ]; then
    echo "❌ Error: $DISK_IMG not found!"
    exit 1
fi

# Setup Loop
LOOP_DEV=$(sudo losetup -fP --show $DISK_IMG)
echo "🔄 Mounted on $LOOP_DEV"

# Mount Partition
sudo mkdir -p $MOUNT_POINT
sudo mount "${LOOP_DEV}p1" $MOUNT_POINT

echo ""
echo "🔍 Checking /usr/bin/test-phase2..."
ls -l $MOUNT_POINT/usr/bin/test-phase2

echo ""
echo "🔍 Checking /bin/ls (BusyBox symlink)..."
ls -l $MOUNT_POINT/bin/ls $MOUNT_POINT/bin/busybox

echo ""
echo "🔍 Checking Libraries..."
ls -l $MOUNT_POINT/lib/libc.so.6 $MOUNT_POINT/lib64/ld-linux-x86-64.so.2

echo ""
echo "🧪 Trying to run test binary (via chroot)..."
sudo chroot $MOUNT_POINT /usr/bin/test-phase2 || echo "❌ Binary execution failed!"

# Cleanup
sudo umount $MOUNT_POINT
sudo losetup -d $LOOP_DEV
