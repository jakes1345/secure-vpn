#!/bin/bash
# Fix: Create MINIMAL initramfs + mount rootfs from ISO

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch

cd $PHAZEOS

echo "=========================================="
echo "  FIXING: Creating Minimal Initramfs"
echo "=========================================="
echo ""

# Create TINY initramfs (just for boot)
MINI_INITRAMFS=/tmp/mini-initramfs
rm -rf $MINI_INITRAMFS
mkdir -p $MINI_INITRAMFS/{bin,sbin,dev,proc,sys,newroot}

# Copy ONLY busybox
cp usr/bin/busybox $MINI_INITRAMFS/bin/
ln -s busybox $MINI_INITRAMFS/bin/sh

# Minimal init that mounts the ISO
cat > $MINI_INITRAMFS/init << 'MINIINIT'
#!/bin/sh

/bin/busybox --install -s /bin

mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev

# Find and mount the ISO
mount -t iso9660 /dev/sr0 /newroot 2>/dev/null || mount /dev/sr0 /newroot

# Switch root
exec switch_root /newroot /sbin/init
MINIINIT

chmod +x $MINI_INITRAMFS/init

# Build tiny initramfs
cd $MINI_INITRAMFS
find . | cpio -o -H newc | gzip > $PHAZEOS/boot/initramfs-6.7.4-phazeos.img
cd $PHAZEOS

echo "✅ Minimal initramfs: $(du -h boot/initramfs-6.7.4-phazeos.img | cut -f1)"

# Now create the REAL rootfs as a separate directory in ISO
echo "📁 Creating ISO root filesystem..."
mkdir -p iso-root/phazeos-rootfs
rsync -a {bin,sbin,etc,lib,lib64,usr,var,root,home,mnt,opt} iso-root/phazeos-rootfs/ 2>/dev/null || true

# Create init in rootfs
cat > iso-root/phazeos-rootfs/sbin/init << 'REALINIT'
#!/bin/sh
PATH=/bin:/sbin:/usr/bin:/usr/sbin
export PATH

/etc/init.d/rcS
exec /bin/sh
REALINIT

chmod +x iso-root/phazeos-rootfs/sbin/init

echo "✅ Rootfs created"

# Rebuild ISO
echo "📀 Rebuilding ISO..."
rm -f iso-output/*.iso
./05-create-iso.sh > /dev/null 2>&1

echo "✅ ISO rebuilt: $(du -h iso-output/*.iso | cut -f1)"
echo ""
echo "Initramfs is now tiny - should boot!"
echo ""
