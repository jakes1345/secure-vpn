#!/bin/bash
# PhazeOS - FINAL ISO BOOT FIX
# Implements proper LiveCD boot logic: Find CD -> Mount -> Switch Root

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
cd $PHAZEOS

echo "=========================================="
echo "  FIXING ISO BOOT (LIVE CD METHOD)"
echo "=========================================="
echo ""

# 1. Create the boot initramfs (The "Shim")
# This tiny initramfs's ONLY job is to find the CD-ROM and mount it.
BOOT_INIT=/tmp/phazeos-boot
rm -rf $BOOT_INIT
mkdir -p $BOOT_INIT/{bin,dev,proc,sys,mnt,newroot}

# Install busybox
cp usr/bin/busybox $BOOT_INIT/bin/
ln -s busybox $BOOT_INIT/bin/sh
ln -s busybox $BOOT_INIT/bin/mount
ln -s busybox $BOOT_INIT/bin/mknod
ln -s busybox $BOOT_INIT/bin/mkdir
ln -s busybox $BOOT_INIT/bin/switch_root

# Create the critical init script
cat > $BOOT_INIT/init << 'BOOTEOF'
#!/bin/sh
# PhazeOS Live Boot Shim

# Mount system interfaces
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev

echo "🔎 Looking for PhazeOS Boot Media..."

# Try to mount the CD-ROM
# usually /dev/sr0 or /dev/cdrom
mkdir -p /mnt/cdrom
FOUND=0

for dev in /dev/sr0 /dev/cdrom /dev/vdb /dev/sdb; do
    if mount -t iso9660 -o ro $dev /mnt/cdrom 2>/dev/null; then
        if [ -e /mnt/cdrom/phazeos.squashfs ] || [ -d /mnt/cdrom/phazeos-rootfs ]; then
            echo "✅ Found PhazeOS on $dev"
            FOUND=1
            break
        fi
        umount /mnt/cdrom
    fi
done

if [ $FOUND -eq 0 ]; then
    echo "❌ FATAL: Could not find boot media!"
    echo "Dropping to shell..."
    exec /bin/sh
fi

echo "🚀 Booting PhazeOS..."

# If we used a directory structure on the ISO (easier for now):
# We need to bind mount it to newroot
mount --bind /mnt/cdrom/phazeos-rootfs /newroot

# Switch to the real system
exec switch_root /newroot /sbin/init

BOOTEOF

chmod +x $BOOT_INIT/init

# Build the shim initramfs
cd $BOOT_INIT
find . | cpio -o -H newc | gzip > $PHAZEOS/boot/initramfs-shim.img
cd $PHAZEOS

echo "✅ Boot shim created: $(du -h boot/initramfs-shim.img | cut -f1)"

# 2. Update the ISO structure
echo "📂 Updating ISO structure..."

# Ensure the rootfs is in the right place
mkdir -p iso-root/phazeos-rootfs
# Sync the full system again just to be sure we have everything
rsync -a --delete \
    --exclude=iso-root \
    --exclude=sources \
    --exclude=build \
    --exclude=iso-output \
    --exclude=toolchain \
    --exclude=boot \
    bin sbin etc lib lib64 usr var root home opt mnt tmp \
    iso-root/phazeos-rootfs/ 2>/dev/null || true

# create the init script inside the rootfs
cat > iso-root/phazeos-rootfs/sbin/init << 'REALINIT'
#!/bin/sh
export PATH=/bin:/sbin:/usr/bin:/usr/sbin
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
/etc/init.d/rcS
exec /sbin/getty 38400 tty1
REALINIT
chmod +x iso-root/phazeos-rootfs/sbin/init

# 3. Update Bootloader to use the shim
cat > iso-root/isolinux/isolinux.cfg << 'ISOLINUX'
DEFAULT phazeos
TIMEOUT 10
PROMPT 0

LABEL phazeos
    KERNEL /boot/vmlinuz-6.7.4-phazeos
    APPEND initrd=/boot/initramfs-shim.img root=/dev/sr0 quiet

ISOLINUX

# Copy the shim to the ISO boot folder
cp boot/initramfs-shim.img iso-root/boot/

# 4. Rebuild ISO
echo "Dv Rebuilding ISO..."
rm -f iso-output/*.iso
./05-create-iso.sh > /dev/null 2>&1

echo ""
echo "✅ FIXED ISO READY: $(ls -lh iso-output/*.iso | awk '{print $5, $9}')"
echo "This ISO searches for itself on CD-ROM and mounts it."
echo "Running launch script to update VirtualBox..."
