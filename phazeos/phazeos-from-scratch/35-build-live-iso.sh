#!/bin/bash
# PhazeOS - Live ISO Builder (OverlayFS + SquashFS)
# Creates a fully functional Live CD/USB that supports writing to RAM.

set -e

PH_DIR="/media/jack/Liunux/secure-vpn/phazeos-from-scratch"
ISO_ROOT="$PH_DIR/iso-root"
ISO_OUTPUT="$PH_DIR/iso-output"
BOOT_INIT="$PH_DIR/boot-shim"
DATE=$(date +%Y%m%d)

echo "=========================================="
echo "  💿 BUILDING LIVE ISO (OverlayFS)"
echo "=========================================="

mkdir -p "$ISO_ROOT/live" "$ISO_ROOT/boot" "$ISO_ROOT/isolinux" "$ISO_OUTPUT"

# 1. Create SquashFS (Read-Only System Image)
echo "🗜️  Compressing filesystem..."
rm -f "$ISO_ROOT/live/filesystem.squashfs"
# Exclude artifacts and the target ISO root itself
mksquashfs \
    "$PH_DIR/bin" "$PH_DIR/sbin" "$PH_DIR/etc" "$PH_DIR/lib" "$PH_DIR/lib64" \
    "$PH_DIR/usr" "$PH_DIR/var" "$PH_DIR/root" "$PH_DIR/home" "$PH_DIR/opt" \
    "$PH_DIR/mnt" "$PH_DIR/tmp" "$PH_DIR/run" "$PH_DIR/srv" \
    "$ISO_ROOT/live/filesystem.squashfs" \
    -comp xz -noappend -wildcards \
    -e "iso-root" "iso-output" "build" "sources" "toolchain" "boot" "phazeos-disk.img" "PhazeOS.vdi"

echo "✅ SquashFS size: $(du -h "$ISO_ROOT/live/filesystem.squashfs" | cut -f1)"

# 2. Build Custom Initramfs (The Boot Shim)
echo "🔧 Building Initramfs with OverlayFS support..."
rm -rf "$BOOT_INIT"
mkdir -p "$BOOT_INIT"/{bin,dev,proc,sys,mnt,cdrom,new_root,run/rw,run/ro}

# Copy Busybox and Utils
cp "$PH_DIR/usr/bin/busybox" "$BOOT_INIT/bin/"
for tool in sh mount umount mknod mkdir ls switch_root sleep grep awk cut stat losetup; do
    ln -s busybox "$BOOT_INIT/bin/$tool"
done

# Init Script
cat > "$BOOT_INIT/init" << 'EOF'
#!/bin/sh
export PATH=/bin

# Banner
echo "========================================"
echo "   🚀 PhazeOS Live Boot (OverlayFS)"
echo "========================================"

# Mount kernel filesystems
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mkdir -p /dev/pts
mount -t devpts devpts /dev/pts

# Load Modules (if needed, usually kernel has them built-in or we load from /lib)
# We assume overlay and squashfs are in kernel or accessible.

echo "🔎 Searching for boot media..."
FOUND=""
# Slow down slightly for USB detection
sleep 2

for dev in /dev/sr* /dev/sd* /dev/nvme*; do
    [ -e "$dev" ] || continue
    mount -t iso9660 -o ro "$dev" /cdrom 2>/dev/null
    if [ -f /cdrom/live/filesystem.squashfs ]; then
        echo "✅ Found Live Media on $dev"
        FOUND="yes"
        break
    else
        umount /cdrom 2>/dev/null
    fi
done

if [ -z "$FOUND" ]; then
    echo "❌ FATAL: Could not find boot media (filesystem.squashfs)"
    echo "Dropping to emergency shell..."
    exec /bin/sh
fi

echo "📂 Mounting System Layers..."

# 1. Loop mount the SquashFS (Read-Only)
mount -t squashfs -o loop /cdrom/live/filesystem.squashfs /run/ro || {
    echo "❌ Failed to mount squashfs. Kernel missing loop/squashfs support?"
    exec /bin/sh
}

# 2. Mount TmpFS for writes (Read-Write)
mount -t tmpfs -o size=50% tmpfs /run/rw
mkdir -p /run/rw/upper /run/rw/work

# 3. Create OverlayFS (Merge RO + RW)
echo "✨ Assembling OverlayFS..."
mount -t overlay overlay -o lowerdir=/run/ro,upperdir=/run/rw/upper,workdir=/run/rw/work /new_root || {
    echo "❌ Failed to mount OverlayFS!"
    exec /bin/sh
}

# 4. Clean up and Switch Root
echo "➡️  Switching Root..."
# Move mounts to new locations
mkdir -p /new_root/run/initramfs/cdrom
mount --move /cdrom /new_root/run/initramfs/cdrom
mkdir -p /new_root/run/initramfs/ro
mount --move /run/ro /new_root/run/initramfs/ro
mkdir -p /new_root/run/initramfs/rw
mount --move /run/rw /new_root/run/initramfs/rw

# Unmount boot utils
umount /dev/pts
umount /dev
umount /sys
umount /proc

# Execute real init
exec switch_root /new_root /bin/runit-init
# Fallback
exec switch_root /new_root /sbin/init
EOF

chmod +x "$BOOT_INIT/init"

# Compress Initramfs
cd "$BOOT_INIT"
find . | cpio -o -H newc | gzip > "$ISO_ROOT/boot/initramfs.img"
cd "$PH_DIR"

# 3. Copy Kernel (COMPLETE version with ISO9660)
cp "$PH_DIR/boot/vmlinuz-6.7.4-phazeos-complete" "$ISO_ROOT/boot/"

# 4. Bootloader Configuration (ISOLINUX/Syslinux)
echo "Boot Config..."
cat > "$ISO_ROOT/isolinux/isolinux.cfg" << 'EOF'
DEFAULT phazeos
TIMEOUT 50
PROMPT 1

LABEL phazeos
    MENU LABEL PhazeOS Live
    KERNEL /boot/vmlinuz-6.7.4-phazeos-complete
    APPEND initrd=/boot/initramfs.img root=/dev/null quiet splash loglevel=3

LABEL debug
    MENU LABEL PhazeOS Debug
    KERNEL /boot/vmlinuz-6.7.4-phazeos-complete
    APPEND initrd=/boot/initramfs.img root=/dev/null debug
EOF

# Ensure Syslinux binaries
if [ -f /usr/lib/syslinux/bios/isolinux.bin ]; then
    cp /usr/lib/syslinux/bios/isolinux.bin "$ISO_ROOT/isolinux/"
    cp /usr/lib/syslinux/bios/ldlinux.c32 "$ISO_ROOT/isolinux/"
else
    # Fallback search
    find /usr/lib -name isolinux.bin -exec cp {} "$ISO_ROOT/isolinux/" \; -quit
    find /usr/lib -name ldlinux.c32 -exec cp {} "$ISO_ROOT/isolinux/" \; -quit
fi

# 5. Build ISO
ISO_NAME="phazeos-live-$DATE.iso"
echo "📀 Generating ISO: $ISO_NAME"

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
    -output "$ISO_OUTPUT/$ISO_NAME" \
    "$ISO_ROOT"

echo "✅ SUCCESS! ISO Ready: $ISO_OUTPUT/$ISO_NAME"
echo "To dual boot:"
echo "1. Burn to USB: sudo dd if=$ISO_OUTPUT/$ISO_NAME of=/dev/sdX bs=4M status=progress"
echo "2. Boot from USB"
echo "3. Run 'sudo install-phazeos' in the terminal"
