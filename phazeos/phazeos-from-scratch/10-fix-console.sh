#!/bin/bash
# PhazeOS - Step 1: Fix Console Output & Make It Interactive
# This will make PhazeOS actually WORK

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch

cd $PHAZEOS

echo "=========================================="
echo "  STEP 1: FIXING CONSOLE OUTPUT"
echo "=========================================="
echo ""

# 1. Fix isolinux config with proper console
echo "📝 Fixing bootloader config..."
cat > iso-root/isolinux/isolinux.cfg << 'EOF'
DEFAULT phazeos
TIMEOUT 30
PROMPT 0

LABEL phazeos
    KERNEL /boot/vmlinuz-6.7.4-phazeos
    APPEND initrd=/boot/initramfs-6.7.4-phazeos.img root=/dev/ram0 console=tty0 console=ttyS0,115200n8 quiet

LABEL safe
    KERNEL /boot/vmlinuz-6.7.4-phazeos
    APPEND initrd=/boot/initramfs-6.7.4-phazeos.img root=/dev/ram0 console=tty0 nomodeset

LABEL debug
    KERNEL /boot/vmlinuz-6.7.4-phazeos
    APPEND initrd=/boot/initramfs-6.7.4-phazeos.img root=/dev/ram0 console=tty0 console=ttyS0,115200n8 debug loglevel=7
EOF

# 2. Create proper init with getty
echo "🔧 Creating init with getty..."
cat > init-proper << 'INITEOF'
#!/bin/sh
# PhazeOS Init - Proper Version

# Print welcome
clear
echo "========================================"
echo "  PhazeOS 1.0 Alpha - FROM SCRATCH!"
echo "========================================"
echo ""
echo "Kernel: $(uname -r)"
echo "Hostname: phazeos"
echo ""

# Create essential mounts
/bin/mount -t proc proc /proc 2>/dev/null || true
/bin/mount -t sysfs sysfs /sys 2>/dev/null || true
/bin/mount -t devtmpfs devtmpfs /dev 2>/dev/null || true
/bin/mount -t tmpfs tmpfs /tmp 2>/dev/null || true

# Set hostname
echo "phazeos" > /proc/sys/kernel/hostname 2>/dev/null || true

# Print status
echo "✅ System initialized!"
echo ""
echo "Available commands:"
echo "  ls, cat, cp, mv, rm, mkdir, cd"
echo "  ps, top, free, df, mount"
echo "  vi, sh, bash"
echo ""
echo "Type 'help' for full BusyBox command list"
echo ""
echo "---"
echo ""

# Start shell with prompt
export PS1='phazeos:$(pwd)# '
exec /bin/sh
INITEOF

chmod +x init-proper

# 3. Rebuild initramfs with everything
echo "🗜️  Building complete initramfs..."
INITRAMFS=/tmp/phazeos-initramfs
rm -rf $INITRAMFS
mkdir -p $INITRAMFS/{bin,sbin,dev,proc,sys,tmp,etc,usr/{bin,sbin},lib,root}

# Copy BusyBox
cp usr/bin/busybox $INITRAMFS/bin/
cd $INITRAMFS/bin
for cmd in sh ash bash ls cat cp mv rm mkdir rmdir ln chmod chown ps mount umount echo; do
    ln -sf busybox $cmd 2>/dev/null || true
done
cd $PHAZEOS

cp usr/bin/busybox $INITRAMFS/sbin/
cd $INITRAMFS/sbin
for cmd in init getty login halt reboot poweroff; do
    ln -sf busybox $cmd 2>/dev/null || true
done
cd $PHAZEOS

# Copy init script
cp init-proper $INITRAMFS/init
chmod +x $INIT$RAMFS/init

# Create some basic devices
cd $INITRAMFS/dev
mknod -m 666 console c 5 1 2>/dev/null || true
mknod -m 666 null c 1 3 2>/dev/null || true
mknod -m 666 zero c 1 5 2>/dev/null || true
mknod -m 666 tty c 5 0 2>/dev/null || true
mknod -m 666 tty0 c 4 0 2>/dev/null || true
mknod -m 666 ttyS0 c 4 64 2>/dev/null || true
cd $PHAZEOS

# Create initramfs
cd $INITRAMFS
find . | cpio -o -H newc | gzip > $PHAZEOS/boot/initramfs-6.7.4-phazeos.img
cd $PHAZEOS

INITRAMFS_SIZE=$(du -h boot/initramfs-6.7.4-phazeos.img | cut -f1)
echo "✅ Initramfs created: $INITRAMFS_SIZE"

# 4. Rebuild ISO
echo "📀 Rebuilding ISO..."
rm -f iso-output/*.iso
./05-create-iso.sh > /dev/null 2>&1

ISO_SIZE=$(du -h iso-output/*.iso | cut -f1)
echo "✅ ISO rebuilt: $ISO_SIZE"

echo ""
echo "=========================================="
echo "✅ STEP 1 COMPLETE!"
echo "=========================================="
echo ""
echo "Test with:"
echo "  qemu-system-x86_64 -cdrom iso-output/phazeos-*.iso -m 4G"
echo ""
echo "You should now see:"
echo "  - Boot messages"
echo "  - Welcome screen"
echo "  - Working shell prompt"
echo ""
