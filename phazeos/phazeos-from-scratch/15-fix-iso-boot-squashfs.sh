#!/bin/bash
# PhazeOS - SQUASHFS BOOT FIX (The Professional Way)
# Compresses the OS so it loads fast and reliably from CD.

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
cd $PHAZEOS

echo "=========================================="
echo "  FIXING ISO BOOT (SQUASHFS METHOD)"
echo "=========================================="

# 1. Create the SquashFS Image (Compressed OS)
echo "🗜️  Compressing filesystem (this may take a minute)..."
mkdir -p iso-root/live
rm -f iso-root/live/filesystem.squashfs

# Make sure we have a clean source directory
# We exclude the build artifacts to keep it clean
mksquashfs \
    bin sbin etc lib lib64 usr var root home opt mnt tmp \
    iso-root/live/filesystem.squashfs \
    -comp xz -noappend -wildcards \
    -e "iso-root" "iso-output" "build" "sources" "toolchain" "boot"

echo "✅ Filesystem compressed: $(du -h iso-root/live/filesystem.squashfs | cut -f1)"

# 2. Create the Boot Shim (Tiny Initramfs)
BOOT_INIT=/tmp/phazeos-boot-squash
rm -rf $BOOT_INIT
mkdir -p $BOOT_INIT/{bin,dev,proc,sys,mnt,cdrom,new_root,run}

cp usr/bin/busybox $BOOT_INIT/bin/
ln -s busybox $BOOT_INIT/bin/sh
ln -s busybox $BOOT_INIT/bin/mount
ln -s busybox $BOOT_INIT/bin/umount
ln -s busybox $BOOT_INIT/bin/mknod
ln -s busybox $BOOT_INIT/bin/mkdir
ln -s busybox $BOOT_INIT/bin/ls
ln -s busybox $BOOT_INIT/bin/switch_root
ln -s busybox $BOOT_INIT/bin/sleep

cat > $BOOT_INIT/init << 'BOOTSHIM'
#!/bin/sh
export PATH=/bin

mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mkdir -p /dev/pts
mount -t devpts devpts /dev/pts

echo "🚀 PhazeOS Boot Loader"
echo "🔎 Searching for live media..."

# Find CDROM
FOUND_DEV=""
for dev in /dev/sr0 /dev/sr1 /dev/cdrom /dev/sda /dev/sdb; do
   if mount -t iso9660 -o ro $dev /cdrom 2>/dev/null; then
       if [ -f /cdrom/live/filesystem.squashfs ]; then
           echo "✅ Found media on $dev"
           FOUND_DEV=$dev
           break
       fi
       umount /cdrom
   fi
done

if [ -z "$FOUND_DEV" ]; then
   echo "❌ ERROR: Boot media not found!"
   echo "Dropping to shell..."
   exec /bin/sh
fi

echo "📂 Mounting System Image..."
mkdir -p /run/system
# Mount squashfs - requires kernel support for squashfs and loop
# If we missed loop support in kernel, this is where it might fail,
# but our config usually includes it.
if ! mount -t squashfs -o loop /cdrom/live/filesystem.squashfs /new_root; then
    echo "❌ Failed to mount squashfs. Kernel might miss loop/squashfs support."
    echo "Attempting raw bind mount fallback..."
    # Fallback to mounting directory if squashfs mount fails
    mount --bind /cdrom/phazeos-rootfs /new_root 2>/dev/null
fi

echo "➡️  Switching Root..."
exec switch_root /new_root /sbin/init

BOOTSHIM
chmod +x $BOOT_INIT/init

# Build Shim
cd $BOOT_INIT
find . | cpio -o -H newc | gzip > $PHAZEOS/boot/initramfs-shim.img
cd $PHAZEOS

# 3. Update ISO Config
cp boot/initramfs-shim.img iso-root/boot/
cat > iso-root/isolinux/isolinux.cfg << 'CFG'
DEFAULT phazeos
TIMEOUT 10
PROMPT 1

LABEL phazeos
    KERNEL /boot/vmlinuz-6.7.4-phazeos
    APPEND initrd=/boot/initramfs-shim.img root=/dev/ram0 quiet
CFG

# 4. Burn ISO
echo "📀 Building ISO..."
rm -f iso-output/*.iso
./05-create-iso.sh > /dev/null 2>&1

echo "✅ DONE. Running VirtualBox..."
