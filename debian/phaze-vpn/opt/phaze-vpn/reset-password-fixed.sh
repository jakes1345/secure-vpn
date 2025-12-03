#!/bin/bash
# Fixed password reset script - handles special characters correctly

set -e

MOUNT_POINT="/mnt/root"
SYSTEM_DISK="/dev/sdb1"
# Use single quotes to prevent bash from interpreting ! character
PASSWORD='Jakes1328!@'

echo "🔐 Password Reset Script"
echo "========================"
echo ""

# Create mount point
echo "Step 1: Creating mount point..."
mkdir -p "$MOUNT_POINT"
echo "✅ Mount point created: $MOUNT_POINT"

# Mount system disk
echo ""
echo "Step 2: Mounting system disk..."
mount "$SYSTEM_DISK" "$MOUNT_POINT"
echo "✅ System disk mounted"

# Mount required filesystems
echo ""
echo "Step 3: Mounting required filesystems..."
mkdir -p "$MOUNT_POINT/proc" "$MOUNT_POINT/sys" "$MOUNT_POINT/dev" "$MOUNT_POINT/dev/pts"
mount -t proc proc "$MOUNT_POINT/proc"
mount -t sysfs sys "$MOUNT_POINT/sys"
mount --bind /dev "$MOUNT_POINT/dev"
mount --bind /dev/pts "$MOUNT_POINT/dev/pts"
echo "✅ Filesystems mounted"

# Set passwords using chpasswd (single quotes prevent ! from being interpreted)
echo ""
echo "Step 4: Setting passwords..."
chroot "$MOUNT_POINT" bash -c "echo 'root:${PASSWORD}' | chpasswd" && echo "✅ Root password set"

if chroot "$MOUNT_POINT" bash -c "id ubuntu >/dev/null 2>&1"; then
    chroot "$MOUNT_POINT" bash -c "echo 'ubuntu:${PASSWORD}' | chpasswd" && echo "✅ Ubuntu password set"
else
    echo "⚠️  Ubuntu user not found, skipping"
fi

# Enable root SSH login
echo ""
echo "Step 5: Configuring SSH..."
chroot "$MOUNT_POINT" bash -c "sed -i 's/^#*PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config"
chroot "$MOUNT_POINT" bash -c "sed -i '/^PermitRootLogin.*no/c\PermitRootLogin yes' /etc/ssh/sshd_config" 2>/dev/null || true
chroot "$MOUNT_POINT" bash -c "grep '^PermitRootLogin' /etc/ssh/sshd_config || echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config"
echo "✅ SSH configured"

# Verify password was set
echo ""
echo "Step 6: Verifying password..."
if chroot "$MOUNT_POINT" bash -c "grep -q '^root:' /etc/shadow"; then
    echo "✅ Password hash found in /etc/shadow"
    chroot "$MOUNT_POINT" bash -c "grep '^root:' /etc/shadow | cut -d: -f1-2 | head -c 50 && echo '...'"
else
    echo "❌ Password hash not found!"
fi

# Unmount
echo ""
echo "Step 7: Unmounting..."
umount "$MOUNT_POINT/dev/pts" 2>/dev/null || true
umount "$MOUNT_POINT/dev" 2>/dev/null || true
umount "$MOUNT_POINT/sys" 2>/dev/null || true
umount "$MOUNT_POINT/proc" 2>/dev/null || true
umount "$MOUNT_POINT" 2>/dev/null || true
echo "✅ Unmounted"

echo ""
echo "=========================================="
echo "✅ Password reset complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Exit rescue mode in OVH Control Panel"
echo "2. Change boot mode from 'Rescue' to 'LOCAL'"
echo "3. Reboot the VPS"
echo "4. Wait 2-3 minutes"
echo "5. Test: ssh root@15.204.11.19"
echo "   Password: Jakes1328!@"
echo ""

