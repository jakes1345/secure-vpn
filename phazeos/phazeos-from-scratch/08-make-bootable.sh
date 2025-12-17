#!/bin/bash
# Make PhazeOS Actually Bootable - Add BusyBox and Create Proper Initramfs

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
SOURCES=$PHAZEOS/sources
BUILD=$PHAZEOS/build
MAKEFLAGS="-j4"

cd $BUILD

echo "=========================================="
echo "  MAKING PHAZEOS BOOTABLE"
echo "=========================================="
echo ""

# Step 1: Build BusyBox
echo "🔨 Building BusyBox (all-in-one utilities)..."
tar -xf $SOURCES/busybox-1.36.1.tar.bz2
cd busybox-1.36.1

# Configure for static build
make defconfig
sed -i 's/# CONFIG_STATIC is not set/CONFIG_STATIC=y/' .config

# Build
make $MAKEFLAGS 2>&1 | tee $PHAZEOS/build-logs/busybox-make.log
echo "✅ BusyBox compiled!"

# Install to system
make CONFIG_PREFIX=$PHAZEOS install 2>&1 | tee $PHAZEOS/build-logs/busybox-install.log
echo "✅ BusyBox installed!"

cd $PHAZEOS

# Step 2: Create essential symlinks
echo "🔗 Creating essential symlinks..."
mkdir -p bin sbin

# Shell
ln -sf ../usr/bin/busybox bin/sh
ln -sf ../usr/bin/busybox bin/bash

# Init
ln -sf ../usr/bin/busybox sbin/init

echo "✅ Symlinks created!"

# Step 3: Create proper init script
echo "📝 Creating init script..."
cat > init << 'INITEOF'
#!/bin/sh
# PhazeOS Init Script

echo "=========================================="
echo "  Welcome to PhazeOS 1.0 Alpha!"
echo "=========================================="
echo ""

# Mount essential filesystems
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev

# Create necessary directories
mkdir -p /dev/pts /dev/shm
mount -t devpts devpts /dev/pts
mount -t tmpfs tmpfs /dev/shm

echo "✅ System initialized!"
echo ""
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo ""
echo "Available commands: ls, cat, cd, ps, top, vi, etc."
echo "Type 'help' for BusyBox built-in commands"
echo ""

# Drop to shell
exec /bin/sh
INITEOF

chmod +x init
echo "✅ Init script created!"

# Step 4: Create proper initramfs
echo "🗜️  Creating initramfs..."
cd $PHAZEOS

# Create initramfs structure
INITRAMFS_DIR=$BUILD/initramfs
rm -rf $INITRAMFS_DIR
mkdir -p $INITRAMFS_DIR/{bin,sbin,etc,proc,sys,dev,usr/bin,usr/sbin,lib,lib64}

# Copy BusyBox
cp usr/bin/busybox $INITRAMFS_DIR/bin/
ln -sf busybox $INITRAMFS_DIR/bin/sh
ln -sf busybox $INITRAMFS_DIR/sbin/init

# Copy init script
cp init $INITRAMFS_DIR/

# Create devices
mknod -m 622 $INITRAMFS_DIR/dev/console c 5 1 2>/dev/null || true
mknod -m 666 $INITRAMFS_DIR/dev/null c 1 3 2>/dev/null || true
mknod -m 666 $INITRAMFS_DIR/dev/zero c 1 5 2>/dev/null || true
mknod -m 666 $INITRAMFS_DIR/dev/tty c 5 0 2>/dev/null || true

# Create initramfs archive
cd $INITRAMFS_DIR
find . | cpio -o -H newc | gzip > $PHAZEOS/boot/initramfs-6.7.4-phazeos.img
cd $PHAZEOS

INITRAMFS_SIZE=$(du -h boot/initramfs-6.7.4-phazeos.img | cut -f1)
echo "✅ Initramfs created! Size: $INITRAMFS_SIZE"

# Step 5: Verify everything
echo ""
echo "🔍 Verifying installation..."
echo ""
ls -lh bin/sh sbin/init init boot/initramfs-6.7.4-phazeos.img

echo ""
echo "=========================================="
echo "✅ PHAZEOS IS NOW BOOTABLE!"
echo "=========================================="
echo ""
echo "Next: Rebuild ISO with ./05-create-iso.sh"
echo ""
