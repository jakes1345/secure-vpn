#!/bin/bash
# PhazeOS - ULTIMATE VERIFICATION
# Runs the actual binary INSIDE the PhazeOS disk to prove it works.

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
DISK_IMG="phazeos-disk.img"
MOUNT_POINT="/mnt/phazeos-verify"

cd $PHAZEOS

echo "=========================================="
echo "  VERIFYING PHASE 1 & 2 INTEGRITY"
echo "=========================================="

if [ ! -f "$DISK_IMG" ]; then
    echo "❌ Error: Disk image not found!"
    exit 1
fi

# 1. Mount the PhazeOS Hard Drive
LOOP_DEV=$(sudo losetup -fP --show $DISK_IMG)
sudo mkdir -p $MOUNT_POINT
sudo mount "${LOOP_DEV}p1" $MOUNT_POINT

echo "✅ PhazeOS Disk Mounted."

# 2. Test 1: Filesystem Check
echo ""
echo "test 1: Checking Filesystem..."
if [ -f "$MOUNT_POINT/usr/bin/busybox" ]; then
    echo "  [PASS] BusyBox binary binary exists"
else
    echo "  [FAIL] BusyBox missing!"
fi

if [ -f "$MOUNT_POINT/usr/bin/test-phase2" ]; then
    echo "  [PASS] Test binary exists"
else
    echo "  [FAIL] Test binary missing!"
fi

# 3. Test 2: Run "ls" (Basic Command)
echo ""
echo "test 2: Executing 'ls' command inside PhazeOS..."
# We use chroot to run /bin/ls using the libraries ON THE DISK, not the host
if sudo chroot $MOUNT_POINT /bin/ls / > /dev/null 2>&1; then
    echo "  [PASS] Command execution works!"
else
    echo "  [FAIL] 'ls' command failed. Libraries missing or corrupt."
fi

# 4. Test 3: Run Dynamic Binary (The Big One)
echo ""
echo "test 3: Running Phase 2 Readiness Test (Dynamic Linking)..."
echo "---------------------------------------------------"
sudo chroot $MOUNT_POINT /usr/bin/test-phase2 || echo "  [FAIL] Execution Failed"
echo "---------------------------------------------------"

# 5. Cleanup
sudo umount $MOUNT_POINT
sudo losetup -d $LOOP_DEV
rm -rf $MOUNT_POINT

echo ""
echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
