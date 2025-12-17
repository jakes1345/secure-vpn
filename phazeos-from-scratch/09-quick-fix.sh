#!/bin/bash
# Quick Fix - Use Pre-built BusyBox (The Smart Way)

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch

cd $PHAZEOS

echo "=========================================="
echo "  QUICK FIX - USING PRE-BUILT BUSYBOX"
echo "=========================================="
echo ""

# Copy pre-built BusyBox
echo "📦 Installing BusyBox..."
mkdir -p bin sbin usr/bin
cp busybox-static usr/bin/busybox
chmod +x usr/bin/busybox

# Create symlinks
ln -sf ../usr/bin/busybox bin/sh
ln -sf ../usr/bin/busybox sbin/init

echo "✅ BusyBox installed!"

# Create init script
cat > init << 'EOF'
#!/bin/sh
echo "=========================================="
echo "  Welcome to PhazeOS 1.0 Alpha!"
echo "=========================================="
echo ""

mount -t proc proc /proc
mount -t sysfs sysfs /sys  
mount -t devtmpfs devtmpfs /dev

echo "✅ System ready!"
echo ""
exec /bin/sh
EOF

chmod +x init
echo "✅ Init script created!"

# Create initramfs
echo "🗜️  Creating initramfs..."
mkdir -p /tmp/initramfs/{bin,sbin,dev,proc,sys}
cp usr/bin/busybox /tmp/initramfs/bin/
ln -sf busybox /tmp/initramfs/bin/sh
ln -sf busybox /tmp/initramfs/sbin/init
cp init /tmp/initramfs/

cd /tmp/initramfs
find . | cpio -o -H newc | gzip > $PHAZEOS/boot/initramfs-6.7.4-phazeos.img
cd $PHAZEOS

echo "✅ Initramfs: $(du -h boot/initramfs-6.7.4-phazeos.img | cut -f1)"

# Rebuild ISO
echo "📀 Rebuilding ISO..."
./05-create-iso.sh > /dev/null 2>&1

echo ""
echo "=========================================="
echo "✅  PHAZEOS IS NOW BOOTABLE!"
echo "=========================================="
echo ""
ls -lh iso-output/*.iso
echo ""
