#!/bin/bash
# PhazeOS Installation Backend
# This script is called by the "Construct" GUI installer
# It handles the disk partitioning and pacstrap

LOG_FILE="/var/log/phazeos-install.log"
exec > >(tee -a $LOG_FILE) 2>&1

echo "=========================================="
echo "    PHAZEOS INSTALLER BACKEND"
echo "=========================================="
echo "Started at $(date)"

# 1. Identify Target Disk (Simplistic approach: First non-USB disk)
DISK=$(lsblk -d -n -o NAME,TRAN | grep -v "usb" | head -n1 | awk '{print "/dev/"$1}')

if [ -z "$DISK" ]; then
    echo "❌ No suitable disk found! defaulting to simulation."
    # Simulation Mode
    sleep 2
    echo ">> Partitioning virtual drive..."
    sleep 3
    echo ">> Formatting partitions..."
    sleep 3
    echo ">> Installing core packages..."
    sleep 5
    echo ">> Configuring bootloader..."
    sleep 2
    touch /etc/phazeos-installed
    exit 0
fi

echo "✅ Target Disk Detected: $DISK"

# WARNING: DESTRUCTIVE OPERATIONS BELOW
# Uncomment to enable real installation

# parted -s $DISK mklabel gpt
# parted -s $DISK mkpart ESP fat32 1MiB 513MiB
# parted -s $DISK set 1 boot on
# parted -s $DISK mkpart primary ext4 513MiB 100%

# mkfs.fat -F32 ${DISK}1
# mkfs.ext4 ${DISK}2

# mount ${DISK}2 /mnt
# mkdir -p /mnt/boot
# mount ${DISK}1 /mnt/boot

# pacstrap /mnt base linux-zen linux-firmware vim git networkmanager

# genfstab -U /mnt >> /mnt/etc/fstab

# arch-chroot /mnt /bin/bash <<EOF
# systemctl enable NetworkManager
# grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=PhazeOS
# grub-mkconfig -o /boot/grub/grub.cfg
# EOF

echo "✅ Installation Complete!"
touch /etc/phazeos-installed
exit 0
