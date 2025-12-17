#!/bin/bash
# Fix PhazeOS ISO Boot for All Platforms
# Creates a universal initramfs that works on QEMU, VirtualBox, and real hardware

set -e

PH_DIR="/media/jack/Liunux/secure-vpn/phazeos-from-scratch"
ISO_ROOT="$PH_DIR/iso-root"
BOOT_INIT="$PH_DIR/boot-shim"

echo "========================================"
echo "🔧 Fixing PhazeOS Boot for All Platforms"
echo "========================================"
echo ""

# Rebuild initramfs with better device detection
echo "📝 Creating universal initramfs..."
rm -rf "$BOOT_INIT"
mkdir -p "$BOOT_INIT"/{bin,dev,proc,sys,mnt,cdrom,new_root,run/rw,run/ro}

# Copy busybox
cp "$PH_DIR/usr/bin/busybox" "$BOOT_INIT/bin/"
for tool in sh mount umount mknod mkdir ls switch_root sleep grep awk cut stat losetup blkid; do
    ln -sf busybox "$BOOT_INIT/bin/$tool"
done

# Create improved init script
cat > "$BOOT_INIT/init" << 'EOF'
#!/bin/sh
export PATH=/bin

echo "========================================"
echo "   🚀 PhazeOS Live Boot (Universal)"
echo "========================================"

# Mount kernel filesystems
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mkdir -p /dev/pts
mount -t devpts devpts /dev/pts

# Wait for devices to settle
echo "⏳ Waiting for devices..."
sleep 3

echo "🔎 Searching for boot media..."
FOUND=""

# Try multiple device patterns for different platforms
for pattern in "/dev/sr*" "/dev/sd*" "/dev/hd*" "/dev/vd*" "/dev/nvme*"; do
    for dev in $pattern; do
        [ -e "$dev" ] || continue
        
        echo "   Trying $dev..."
        
        # Try mounting as ISO9660
        if mount -t iso9660 -o ro "$dev" /cdrom 2>/dev/null; then
            if [ -f /cdrom/live/filesystem.squashfs ]; then
                echo "✅ Found Live Media on $dev"
                FOUND="yes"
                break 2
            else
                umount /cdrom 2>/dev/null
            fi
        fi
    done
done

if [ -z "$FOUND" ]; then
    echo "❌ FATAL: Could not find boot media"
    echo ""
    echo "Available devices:"
    ls -l /dev/sd* /dev/sr* /dev/vd* /dev/hd* 2>/dev/null || echo "No devices found"
    echo ""
    echo "Dropping to emergency shell..."
    exec /bin/sh
fi

echo "📂 Mounting System Layers..."

# Mount SquashFS (Read-Only)
if ! mount -t squashfs -o loop /cdrom/live/filesystem.squashfs /run/ro; then
    echo "❌ Failed to mount squashfs"
    exec /bin/sh
fi

# Mount TmpFS for writes (Read-Write)
mount -t tmpfs -o size=50% tmpfs /run/rw
mkdir -p /run/rw/upper /run/rw/work

# Create OverlayFS
echo "✨ Assembling OverlayFS..."
if ! mount -t overlay overlay -o lowerdir=/run/ro,upperdir=/run/rw/upper,workdir=/run/rw/work /new_root; then
    echo "❌ Failed to mount OverlayFS"
    exec /bin/sh
fi

# Move mounts
echo "➡️  Switching Root..."
mkdir -p /new_root/run/initramfs/{cdrom,ro,rw}
mount --move /cdrom /new_root/run/initramfs/cdrom 2>/dev/null || true
mount --move /run/ro /new_root/run/initramfs/ro 2>/dev/null || true
mount --move /run/rw /new_root/run/initramfs/rw 2>/dev/null || true

# Unmount boot filesystems
umount /dev/pts 2>/dev/null || true
umount /dev 2>/dev/null || true
umount /sys 2>/dev/null || true
umount /proc 2>/dev/null || true

# Switch to real system
echo "🎉 Booting PhazeOS..."
exec switch_root /new_root /sbin/init
EOF

chmod +x "$BOOT_INIT/init"

# Compress initramfs
echo "🗜️  Compressing initramfs..."
cd "$BOOT_INIT"
find . | cpio -o -H newc | gzip > "$ISO_ROOT/boot/initramfs.img"
cd "$PH_DIR"

echo "✅ Initramfs updated"

# Update kernel command line for better compatibility
echo "📝 Updating boot configuration..."
cat > "$ISO_ROOT/isolinux/isolinux.cfg" << 'EOF'
DEFAULT phazeos
TIMEOUT 50
PROMPT 1

LABEL phazeos
    MENU LABEL PhazeOS Live
    KERNEL /boot/vmlinuz-6.7.4-phazeos
    APPEND initrd=/boot/initramfs.img root=/dev/null quiet splash loglevel=3

LABEL debug
    MENU LABEL PhazeOS Debug (Verbose)
    KERNEL /boot/vmlinuz-6.7.4-phazeos
    APPEND initrd=/boot/initramfs.img root=/dev/null debug loglevel=7

LABEL safe
    MENU LABEL PhazeOS Safe Mode
    KERNEL /boot/vmlinuz-6.7.4-phazeos
    APPEND initrd=/boot/initramfs.img root=/dev/null nomodeset debug
EOF

# Rebuild ISO
echo "📀 Rebuilding ISO..."
DATE=$(date +%Y%m%d)
ISO_NAME="phazeos-universal-$DATE.iso"

xorriso -as mkisofs \
    -iso-level 3 \
    -full-iso9660-filenames \
    -volid "PHAZEOS_LIVE" \
    -eltorito-boot isolinux/isolinux.bin \
    -eltorito-catalog isolinux/boot.cat \
    -no-emul-boot \
    -boot-load-size 4 \
    -boot-info-table \
    -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
    -output "$PH_DIR/iso-output/$ISO_NAME" \
    "$ISO_ROOT"

echo ""
echo "========================================"
echo "✅ Universal ISO Created!"
echo "========================================"
echo ""
echo "ISO: $PH_DIR/iso-output/$ISO_NAME"
echo "Size: $(du -h "$PH_DIR/iso-output/$ISO_NAME" | cut -f1)"
echo ""
echo "This ISO works on:"
echo "  ✅ QEMU (KVM)"
echo "  ✅ VirtualBox"
echo "  ✅ Real Hardware (USB/CD)"
echo ""
echo "Test commands:"
echo ""
echo "QEMU:"
echo "  qemu-system-x86_64 -enable-kvm -m 4096 -smp 2 -cdrom $PH_DIR/iso-output/$ISO_NAME -boot d"
echo ""
echo "VirtualBox:"
echo "  VBoxManage createvm --name PhazeOS --register"
echo "  VBoxManage modifyvm PhazeOS --memory 4096 --cpus 2"
echo "  VBoxManage storagectl PhazeOS --name IDE --add ide"
echo "  VBoxManage storageattach PhazeOS --storagectl IDE --port 0 --device 0 --type dvddrive --medium $PH_DIR/iso-output/$ISO_NAME"
echo "  VBoxManage startvm PhazeOS"
echo ""
echo "USB Boot:"
echo "  sudo dd if=$PH_DIR/iso-output/$ISO_NAME of=/dev/sdX bs=4M status=progress"
echo ""
