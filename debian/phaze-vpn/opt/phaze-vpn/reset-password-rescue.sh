#!/bin/bash
# Reset root password in OVH rescue mode
# This script mounts the actual system disk and allows you to reset the root password

set -e

echo "🔐 Password Reset in Rescue Mode"
echo "================================"
echo ""

# Detect the system disk (usually sdb1 for main partition)
SYSTEM_DISK=""
if [ -b /dev/sdb1 ]; then
    SYSTEM_DISK="/dev/sdb1"
    echo "✅ Found system disk: $SYSTEM_DISK"
elif [ -b /dev/vda1 ]; then
    SYSTEM_DISK="/dev/vda1"
    echo "✅ Found system disk: $SYSTEM_DISK"
else
    echo "❌ Could not detect system disk. Please check with: lsblk"
    exit 1
fi

# Create mount point
MOUNT_POINT="/mnt/root"
if [ ! -d "$MOUNT_POINT" ]; then
    mkdir -p "$MOUNT_POINT"
    echo "✅ Created mount point: $MOUNT_POINT"
fi

# Check if already mounted
if mountpoint -q "$MOUNT_POINT"; then
    echo "⚠️  $MOUNT_POINT is already mounted"
else
    echo "📦 Mounting system disk..."
    mount "$SYSTEM_DISK" "$MOUNT_POINT"
    echo "✅ System disk mounted"
fi

# Mount necessary filesystems for chroot (OVH official procedure)
echo "📦 Mounting required filesystems..."
mount -t proc proc "$MOUNT_POINT/proc" 2>/dev/null || true
mount -t sysfs sys "$MOUNT_POINT/sys" 2>/dev/null || true
mount --bind /dev "$MOUNT_POINT/dev" 2>/dev/null || true
mount --bind /dev/pts "$MOUNT_POINT/dev/pts" 2>/dev/null || true
echo "✅ Filesystems mounted"

echo ""
echo "=========================================="
echo "🔐 Ready to reset password!"
echo "=========================================="
echo ""
echo "You will now chroot into the system. Choose an option:"
echo ""
echo "Option 1: Reset root password interactively"
echo "  Type: chroot $MOUNT_POINT passwd root"
echo ""
echo "Option 2: Reset ubuntu user password (if exists)"
echo "  Type: chroot $MOUNT_POINT passwd ubuntu"
echo ""
echo "Option 3: Set password directly in /etc/shadow"
echo "  Type: chroot $MOUNT_POINT /bin/bash"
echo "  Then: openssl passwd -6 'YourNewPassword'"
echo "  Copy the hash and edit: vi /etc/shadow"
echo ""
echo "=========================================="
echo ""

# Interactive mode - let user choose
echo "Press ENTER to start interactive chroot session..."
read -r

chroot "$MOUNT_POINT" /bin/bash

echo ""
echo "=========================================="
echo "🧹 Cleaning up..."
echo "=========================================="

# Unmount filesystems
umount "$MOUNT_POINT/dev/pts" 2>/dev/null || true
umount "$MOUNT_POINT/dev" 2>/dev/null || true
umount "$MOUNT_POINT/sys" 2>/dev/null || true
umount "$MOUNT_POINT/proc" 2>/dev/null || true
umount "$MOUNT_POINT" 2>/dev/null || true

echo "✅ Cleanup complete"
echo ""
echo "Next steps:"
echo "1. Exit rescue mode in OVH control panel"
echo "2. Reboot the VPS to normal mode"
echo "3. Connect with: ssh root@15.204.11.19"

