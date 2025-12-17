#!/bin/bash
# Build COMPLETE PhazeOS Kernel with ALL Required Features

set -e

echo "========================================"
echo "🔨 Building COMPLETE PhazeOS Kernel"
echo "========================================"
echo ""

cd /media/jack/Liunux/secure-vpn/phazeos-from-scratch/kernel/linux-6.7.4

echo "📝 Creating complete kernel config with ALL features..."

# Start with defconfig
make defconfig

# CRITICAL FILESYSTEMS
cat >> .config << 'EOF'

# Filesystems - CRITICAL
CONFIG_ISO9660_FS=y
CONFIG_JOLIET=y
CONFIG_ZISOFS=y
CONFIG_SQUASHFS=y
CONFIG_SQUASHFS_XZ=y
CONFIG_SQUASHFS_ZLIB=y
CONFIG_OVERLAY_FS=y
CONFIG_EXT4_FS=y
CONFIG_VFAT_FS=y
CONFIG_FAT_FS=y
CONFIG_PROC_FS=y
CONFIG_SYSFS=y
CONFIG_TMPFS=y
CONFIG_DEVTMPFS=y
CONFIG_DEVTMPFS_MOUNT=y

# Block Devices - CRITICAL
CONFIG_BLK_DEV_SR=y
CONFIG_BLK_DEV_SD=y
CONFIG_CHR_DEV_SG=y
CONFIG_BLK_DEV_LOOP=y

# SCSI Support
CONFIG_SCSI=y
CONFIG_SCSI_LOWLEVEL=y
CONFIG_ATA=y
CONFIG_ATA_PIIX=y
CONFIG_SATA_AHCI=y

# VirtIO (for QEMU/KVM)
CONFIG_VIRTIO=y
CONFIG_VIRTIO_BLK=y
CONFIG_VIRTIO_SCSI=y
CONFIG_VIRTIO_NET=y
CONFIG_VIRTIO_PCI=y

# Graphics - CRITICAL for Desktop
CONFIG_DRM=y
CONFIG_DRM_FBDEV_EMULATION=y
CONFIG_FB=y
CONFIG_FRAMEBUFFER_CONSOLE=y
CONFIG_DRM_BOCHS=y
CONFIG_DRM_VIRTIO_GPU=y
CONFIG_DRM_QXL=y

# Input Devices
CONFIG_INPUT=y
CONFIG_INPUT_KEYBOARD=y
CONFIG_INPUT_MOUSE=y
CONFIG_INPUT_EVDEV=y

# USB Support
CONFIG_USB=y
CONFIG_USB_XHCI_HCD=y
CONFIG_USB_EHCI_HCD=y
CONFIG_USB_OHCI_HCD=y
CONFIG_USB_STORAGE=y
CONFIG_USB_HID=y

# Networking
CONFIG_NET=y
CONFIG_INET=y
CONFIG_PACKET=y
CONFIG_UNIX=y
CONFIG_NETDEVICES=y
CONFIG_ETHERNET=y
CONFIG_E1000=y
CONFIG_E1000E=y

# Sound
CONFIG_SOUND=y
CONFIG_SND=y
CONFIG_SND_HDA_INTEL=y

# Wayland/DRM Requirements
CONFIG_DRM_KMS_HELPER=y
CONFIG_DRM_GEM_SHMEM_HELPER=y

# Security
CONFIG_SECURITY=y
CONFIG_SECURITYFS=y

# Misc Essential
CONFIG_PRINTK=y
CONFIG_BUG=y
CONFIG_ELF_CORE=y
CONFIG_FUTEX=y
CONFIG_EPOLL=y
CONFIG_SIGNALFD=y
CONFIG_TIMERFD=y
CONFIG_EVENTFD=y
CONFIG_SHMEM=y
CONFIG_AIO=y
CONFIG_ADVISE_SYSCALLS=y
CONFIG_MEMBARRIER=y
CONFIG_KALLSYMS=y
CONFIG_BPF_SYSCALL=y
CONFIG_CGROUPS=y

# Module Support
CONFIG_MODULES=y
CONFIG_MODULE_UNLOAD=y

# Compression
CONFIG_KERNEL_GZIP=y
CONFIG_RD_GZIP=y
CONFIG_RD_XZ=y

# Initramfs
CONFIG_BLK_DEV_INITRD=y
CONFIG_INITRAMFS_SOURCE=""

# SMP
CONFIG_SMP=y
CONFIG_NR_CPUS=64

# KVM Guest
CONFIG_HYPERVISOR_GUEST=y
CONFIG_PARAVIRT=y
CONFIG_KVM_GUEST=y

EOF

# Resolve dependencies
echo "🔧 Resolving all dependencies..."
make olddefconfig

echo ""
echo "✅ Complete config created!"
echo ""
echo "Key features enabled:"
grep -E "CONFIG_ISO9660_FS|CONFIG_SQUASHFS|CONFIG_OVERLAY_FS|CONFIG_DRM|CONFIG_VIRTIO|CONFIG_BLK_DEV_SR" .config

echo ""
echo "🔨 Building kernel with ALL features..."
echo "This will take 15-30 minutes with $(nproc) cores..."
echo ""

# Build
time make -j$(nproc)

# Install
echo ""
echo "📦 Installing kernel..."
cp arch/x86/boot/bzImage ../../boot/vmlinuz-6.7.4-phazeos-complete

echo ""
echo "========================================"
echo "✅ COMPLETE KERNEL BUILT!"
echo "========================================"
echo ""
ls -lh ../../boot/vmlinuz-6.7.4-phazeos-complete
echo ""
echo "This kernel has EVERYTHING:"
echo "  ✅ ISO9660 filesystem"
echo "  ✅ SquashFS"
echo "  ✅ OverlayFS"
echo "  ✅ Graphics (DRM, FB)"
echo "  ✅ VirtIO (QEMU/KVM)"
echo "  ✅ SCSI/SATA"
echo "  ✅ USB"
echo "  ✅ Networking"
echo "  ✅ Sound"
echo ""
