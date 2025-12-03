#!/bin/bash
# Complete password reset script for OVH VPS
# This ensures the password is set correctly for both root and ubuntu users

set -e

echo "🔐 Complete Password Reset Script"
echo "=================================="
echo ""

# Check if we're in rescue mode
if [ -f /.rescue ] || hostname | grep -q rescue || [ -d /root/rescue-scripts ]; then
    echo "✅ Detected rescue mode - this is correct!"
    RESCUE_MODE=true
else
    echo "⚠️  Not in rescue mode - you need to boot into rescue mode first!"
    echo "   Go to OVH Control Panel → VPS → Boot → Boot in rescue mode"
    exit 1
fi

SYSTEM_DISK="/dev/sdb1"
MOUNT_POINT="/mnt/root"
NEW_PASSWORD="Jakes1328!@"

echo ""
echo "Step 1: Mounting system disk..."
if [ ! -d "$MOUNT_POINT" ]; then
    mkdir -p "$MOUNT_POINT"
fi

if ! mountpoint -q "$MOUNT_POINT"; then
    mount "$SYSTEM_DISK" "$MOUNT_POINT" || {
        echo "❌ Failed to mount $SYSTEM_DISK"
        echo "   Check with: lsblk"
        exit 1
    }
    echo "✅ System disk mounted"
else
    echo "✅ System disk already mounted"
fi

echo ""
echo "Step 2: Mounting required filesystems..."
mount -t proc proc "$MOUNT_POINT/proc" 2>/dev/null || true
mount -t sysfs sys "$MOUNT_POINT/sys" 2>/dev/null || true
mount --bind /dev "$MOUNT_POINT/dev" 2>/dev/null || true
mount --bind /dev/pts "$MOUNT_POINT/dev/pts" 2>/dev/null || true
echo "✅ Filesystems mounted"

echo ""
echo "Step 3: Setting passwords inside chroot..."
echo "=========================================="

# Use chroot to set password non-interactively (using chpasswd - more reliable)
chroot "$MOUNT_POINT" /bin/bash <<EOF
echo "Setting root password using chpasswd..."
echo "root:${NEW_PASSWORD}" | chpasswd
if [ $? -eq 0 ]; then
    echo "✅ Root password set successfully"
else
    echo "❌ Failed to set root password"
    exit 1
fi

# Check if ubuntu user exists and set password
if id "ubuntu" &>/dev/null 2>&1; then
    echo "Setting ubuntu user password..."
    echo "ubuntu:${NEW_PASSWORD}" | chpasswd
    if [ $? -eq 0 ]; then
        echo "✅ Ubuntu user password set successfully"
    else
        echo "⚠️  Failed to set ubuntu password"
    fi
else
    echo "⚠️  Ubuntu user not found, skipping"
fi

# Enable root login via SSH (if disabled)
echo ""
echo "Configuring SSH to allow root login..."
if [ -f /etc/ssh/sshd_config ]; then
    # Backup original
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
    
    # Enable root login
    sed -i 's/^#*PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
    sed -i 's/PermitRootLogin.*no/PermitRootLogin yes/' /etc/ssh/sshd_config
    sed -i 's/PermitRootLogin.*prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
    
    # Show what was changed
    echo "SSH PermitRootLogin setting:"
    grep "^PermitRootLogin" /etc/ssh/sshd_config || echo "  (added: PermitRootLogin yes)"
    echo "✅ SSH configured to allow root login"
else
    echo "⚠️  /etc/ssh/sshd_config not found"
fi

# Verify password hash was updated
echo ""
echo "Verifying password was saved..."
if grep -q "^root:" /etc/shadow; then
    echo "✅ Root user found in shadow file"
    echo "Password hash updated: $(grep '^root:' /etc/shadow | cut -d: -f2 | cut -c1-20)..."
else
    echo "⚠️  Could not verify password hash"
fi
EOF

echo ""
echo "Step 4: Unmounting filesystems..."
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
echo "1. Go to OVH Control Panel → VPS → Boot"
echo "2. DISABLE rescue mode (change to LOCAL boot)"
echo "3. Reboot the VPS"
echo "4. Wait 2-3 minutes for reboot"
echo "5. Test connection: ssh root@15.204.11.19"
echo "   Password: ${NEW_PASSWORD}"
echo ""
echo "If root doesn't work, try: ssh ubuntu@15.204.11.19"
echo ""

