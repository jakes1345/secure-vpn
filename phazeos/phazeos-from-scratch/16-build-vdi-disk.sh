#!/bin/bash
# PhazeOS - DIRECT TO DISK BUILD
# Skips ISO/CD-ROM issues by building a real Hard Drive image.

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
DISK_IMG="phazeos-disk.img"
VDI_IMG="PhazeOS.vdi"
MOUNT_POINT="/mnt/phazeos-disk"

cd $PHAZEOS

echo "=========================================="
echo "  BUILDING VIRTUAL HARD DRIVE (VDI)"
echo "=========================================="
echo ""

# 1. Create a 1GB blank disk image
echo "💾 Creating 1GB raw disk image..."
dd if=/dev/zero of=$DISK_IMG bs=1M count=1024 status=progress

# 2. Partition it (One partition, bootable)
echo "🔧 Partitioning..."
parted -s $DISK_IMG mklabel msdos
parted -s $DISK_IMG mkpart primary ext4 1M 100%
parted -s $DISK_IMG set 1 boot on

# 3. Setup Loop Device
echo "🔄 Setting up loop device..."
LOOP_DEV=$(sudo losetup -fP --show $DISK_IMG)
echo "   Loop device: $LOOP_DEV"

# 4. Format Partition (ext4)
echo "🧹 Formatting ext4..."
sudo mkfs.ext4 "${LOOP_DEV}p1"

# 5. Mount it
echo "📂 Mounting..."
sudo mkdir -p $MOUNT_POINT
sudo mount "${LOOP_DEV}p1" $MOUNT_POINT

# 6. Install System
echo "📦 Installing PhazeOS system..."
# Copy everything EXCEPT build/source/tmp artifacts
sudo rsync -a \
    --exclude=iso-root \
    --exclude=iso-output \
    --exclude=sources \
    --exclude=build \
    --exclude=$DISK_IMG \
    --exclude=toolchain \
    --exclude=boot/initramfs* \
    bin sbin etc lib lib64 usr var root home opt mnt tmp \
    $MOUNT_POINT/

sudo mkdir -p $MOUNT_POINT/{dev,proc,sys,run,boot}

# Copy Kernel
sudo cp boot/vmlinuz-6.7.4-phazeos $MOUNT_POINT/boot/

# 7. Install GRUB Bootloader
echo "👢 Installing GRUB..."
sudo grub-install --target=i386-pc --boot-directory=$MOUNT_POINT/boot --modules="part_msdos ext2" $LOOP_DEV

# Configure GRUB
cat << 'GRUB' | sudo tee $MOUNT_POINT/boot/grub/grub.cfg
set default=0
set timeout=5

menuentry "PhazeOS 1.0 Alpha (Hard Disk)" {
    set root=(hd0,msdos1)
    linux /boot/vmlinuz-6.7.4-phazeos root=/dev/sda1 rw console=tty0
}
GRUB

# 8. Cleanup
echo "🧹 Cleaning up..."
sudo umount $MOUNT_POINT
sudo losetup -d $LOOP_DEV
sudo rm -rf $MOUNT_POINT

# 9. Convert to VDI (VirtualBox Format)
echo "🔄 Converting to VirtualBox VDI..."
rm -f $VDI_IMG
VBoxManage convertfromraw $DISK_IMG $VDI_IMG --format VDI

echo "✅ SUCCESS! Virtual Disk Created: $VDI_IMG"
echo "Running launch script for VDI..."
