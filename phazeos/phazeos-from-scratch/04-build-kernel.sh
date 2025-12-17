#!/bin/bash
# PhazeOS From Scratch - Custom Kernel Build
# Builds a privacy-focused, gaming-optimized kernel

set -e

PHAZEOS=/media/jack/Liunux/secure-vpn/phazeos-from-scratch
SOURCES=$PHAZEOS/sources
KERNEL=$PHAZEOS/kernel
LOGS=$PHAZEOS/build-logs
MAKEFLAGS="-j$(nproc)"

mkdir -p $KERNEL

echo "=========================================="
echo "  BUILDING PHAZEOS CUSTOM KERNEL"
echo "=========================================="
echo ""

cd $KERNEL

# Extract kernel source
echo "📦 Extracting kernel source..."
tar -xf $SOURCES/linux-6.7.4.tar.xz
cd linux-6.7.4

echo "✅ Kernel source extracted!"
echo ""

# Create custom kernel config
echo "⚙️  Generating custom PhazeOS kernel configuration..."

# Start with default config
make defconfig 2>&1 | tee $LOGS/kernel-defconfig.log

# Custom PhazeOS kernel configuration
cat >> .config << 'EOF'

# ============================================
# PHAZEOS CUSTOM KERNEL CONFIGURATION
# ============================================

# System Type
CONFIG_64BIT=y
CONFIG_X86_64=y
CONFIG_X86=y

# Processor Features
CONFIG_PROCESSOR_SELECT=y
CONFIG_CPU_SUP_INTEL=y
CONFIG_CPU_SUP_AMD=y

# ============================================
# GAMING OPTIMIZATIONS
# ============================================

# Low-latency preemption (better for gaming)
CONFIG_PREEMPT=y
CONFIG_PREEMPT_COUNT=y
CONFIG_PREEMPTION=y

# High-resolution timer (1000 Hz for gaming)
CONFIG_HZ_1000=y
CONFIG_HZ=1000

# Performance CPU governor
CONFIG_CPU_FREQ_DEFAULT_GOV_PERFORMANCE=y
CONFIG_CPU_FREQ_GOV_PERFORMANCE=y
CONFIG_CPU_FREQ_GOV_ONDEMAND=y
CONFIG_CPU_FREQ_GOV_SCHEDUTIL=y

# Timer tick handling
CONFIG_NO_HZ_FULL=y
CONFIG_NO_HZ_COMMON=y

# ============================================
# GRAPHICS SUPPORT (Gaming)
# ============================================

# DRM (Direct Rendering Manager)
CONFIG_DRM=y
CONFIG_DRM_FBDEV_EMULATION=y

# AMD GPU
CONFIG_DRM_AMDGPU=y
CONFIG_DRM_AMDGPU_SI=y
CONFIG_DRM_AMDGPU_CIK=y
CONFIG_DRM_AMD_DC=y

# Intel GPU
CONFIG_DRM_I915=y
CONFIG_DRM_I915_GVT=y

# NVIDIA (Nouveau)
CONFIG_DRM_NOUVEAU=y

# Framebuffer
CONFIG_FB=y
CONFIG_FB_VESA=y
CONFIG_FB_EFI=y

# ============================================
# SECURITY & PRIVACY
# ============================================

# Security hardening
CONFIG_SECURITY=y
CONFIG_SECURITY_SELINUX=n
CONFIG_SECURITY_APPARMOR=y
CONFIG_SECURITY_YAMA=y

# Kernel hardening
CONFIG_INIT_ON_ALLOC_DEFAULT_ON=y
CONFIG_INIT_ON_FREE_DEFAULT_ON=y
CONFIG_HARDENED_USERCOPY=y
CONFIG_FORTIFY_SOURCE=y
CONFIG_SECURITY_DMESG_RESTRICT=y

# Privacy features
CONFIG_SECCOMP=y
CONFIG_SECURITY_LANDLOCK=y

# ============================================
# NETWORKING
# ============================================

# Advanced networking
CONFIG_NETFILTER=y
CONFIG_NETFILTER_ADVANCED=y
CONFIG_NF_CONNTRACK=y
CONFIG_NETFILTER_XT_MATCH_STATE=y

# IPTables
CONFIG_IP_NF_IPTABLES=y
CONFIG_IP_NF_FILTER=y
CONFIG_IP_NF_NAT=y

# NFTables
CONFIG_NF_TABLES=y
CONFIG_NFT_NAT=y

# Wireless
CONFIG_WIRELESS=y
CONFIG_CFG80211=y
CONFIG_MAC80211=y

# Bluetooth
CONFIG_BT=y
CONFIG_BT_RFCOMM=y
CONFIG_BT_BNEP=y
CONFIG_BT_HIDP=y

# ============================================
# VPN SUPPORT
# ============================================

# WireGuard
CONFIG_WIREGUARD=y

# OpenVPN (TUN/TAP)
CONFIG_TUN=y
CONFIG_TAP=y

# IPsec
CONFIG_INET_ESP=y
CONFIG_INET_XFRM_MODE_TRANSPORT=y
CONFIG_INET_XFRM_MODE_TUNNEL=y

# ============================================
# FILESYSTEM SUPPORT
# ============================================

# Essential filesystems
CONFIG_EXT4_FS=y
CONFIG_EXT4_FS_POSIX_ACL=y
CONFIG_EXT4_FS_SECURITY=y

CONFIG_BTRFS_FS=y
CONFIG_BTRFS_FS_POSIX_ACL=y

CONFIG_XFS_FS=y
CONFIG_F2FS_FS=y

# FAT/VFAT (for EFI, USB drives)
CONFIG_VFAT_FS=y
CONFIG_FAT_DEFAULT_UTF8=y

# NTFS (read Windows drives)
CONFIG_NTFS3_FS=y
CONFIG_NTFS3_LZX_XPRESS=y

# ISO9660 (CDs)
CONFIG_ISO9660_FS=y
CONFIG_JOLIET=y
CONFIG_UDF_FS=y

# Network filesystems
CONFIG_NETWORK_FILESYSTEMS=y
CONFIG_NFS_FS=y
CONFIG_CIFS=y

# Encryption
CONFIG_FS_ENCRYPTION=y
CONFIG_ECRYPT_FS=y

# ============================================
# HARDWARE SUPPORT
# ============================================

# USB Support
CONFIG_USB_SUPPORT=y
CONFIG_USB=y
CONFIG_USB_XHCI_HCD=y
CONFIG_USB_EHCI_HCD=y
CONFIG_USB_STORAGE=y

# Sound (ALSA)
CONFIG_SOUND=y
CONFIG_SND=y
CONFIG_SND_PCI=y
CONFIG_SND_HDA_INTEL=y
CONFIG_SND_HDA_CODEC_REALTEK=y

# Input devices
CONFIG_INPUT_KEYBOARD=y
CONFIG_INPUT_MOUSE=y
CONFIG_INPUT_JOYSTICK=y
CONFIG_INPUT_EVDEV=y

# ============================================
# PHAZEOS BRANDING
# ============================================

# Custom version string
CONFIG_LOCALVERSION="-phazeos"
CONFIG_LOCALVERSION_AUTO=n

EOF

# Apply custom config
echo "🔧 Applying configuration..."
make olddefconfig 2>&1 | tee $LOGS/kernel-olddefconfig.log

echo "✅ Kernel configured!"
echo ""

# Build kernel
echo "🔨 Compiling kernel (this takes 30-60 minutes)..."
make $MAKEFLAGS 2>&1 | tee $LOGS/kernel-make.log

echo "✅ Kernel compiled!"
echo ""

# Install kernel modules
echo "📦 Installing kernel modules..."
make INSTALL_MOD_PATH=$PHAZEOS modules_install 2>&1 | tee $LOGS/kernel-modules-install.log

echo "✅ Kernel modules installed!"
echo ""

# Copy kernel image
echo "📋 Copying kernel image..."
cp -v arch/x86/boot/bzImage $PHAZEOS/boot/vmlinuz-6.7.4-phazeos
cp -v System.map $PHAZEOS/boot/System.map-6.7.4-phazeos
cp -v .config $PHAZEOS/boot/config-6.7.4-phazeos

echo "✅ Kernel installed!"
echo ""

# Generate initramfs
echo "🔧 Generating initramfs..."
cd $PHAZEOS

# Create initramfs structure
mkdir -p initramfs/{bin,sbin,etc,proc,sys,dev,tmp,usr/{bin,sbin}}

# Copy BusyBox (if built)
if [ -f $SOURCES/busybox-1.36.1.tar.bz2 ]; then
    echo "Building BusyBox for initramfs..."
    cd $KERNEL
    tar -xf $SOURCES/busybox-1.36.1.tar.bz2
    cd busybox-1.36.1
    
    make defconfig 2>&1 | tee $LOGS/busybox-defconfig.log
    sed -i 's/# CONFIG_STATIC is not set/CONFIG_STATIC=y/' .config
    make $MAKEFLAGS 2>&1 | tee $LOGS/busybox-make.log
    make CONFIG_PREFIX=$PHAZEOS/initramfs install 2>&1 | tee $LOGS/busybox-install.log
    
    cd $KERNEL
    rm -rf busybox-1.36.1
fi

# Create init script
cat > $PHAZEOS/initramfs/init << 'INITEOF'
#!/bin/sh

# Mount essential filesystems
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev

# Print boot message
echo ""
echo "=========================================="
echo "  PHAZEOS - Privacy-Focused Gaming OS"
echo "=========================================="
echo ""

# Switch to real root
exec switch_root /newroot /sbin/init
INITEOF

chmod +x $PHAZEOS/initramfs/init

# Create initramfs image
cd $PHAZEOS/initramfs
find . | cpio -H newc -o | gzip > $PHAZEOS/boot/initramfs-6.7.4-phazeos.img

cd $PHAZEOS

echo "✅ Initramfs generated!"
echo ""

# Save kernel info
cat > $PHAZEOS/boot/kernel-info.txt << EOF
PhazeOS Custom Kernel Information
==================================
Version: 6.7.4-phazeos
Build Date: $(date)
Configuration:
- Gaming optimizations (1000 Hz, PREEMPT)
- Security hardening (AppArmor, YAMA)
- Privacy features (Seccomp, Landlock)
- VPN support (WireGuard, OpenVPN)
- Full hardware support

Files:
- Kernel: /boot/vmlinuz-6.7.4-phazeos
- Initramfs: /boot/initramfs-6.7.4-phazeos.img
- System.map: /boot/System.map-6.7.4-phazeos
- Config: /boot/config-6.7.4-phazeos

Modules installed to: /lib/modules/6.7.4-phazeos/
EOF

echo "=========================================="
echo "✅ KERNEL BUILD COMPLETE!"
echo "=========================================="
echo ""
echo "Kernel: /boot/vmlinuz-6.7.4-phazeos"
echo "Initramfs: /boot/initramfs-6.7.4-phazeos.img"
echo ""
echo "Next step: ./05-create-iso.sh"
echo ""
