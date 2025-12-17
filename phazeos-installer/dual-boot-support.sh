#!/bin/bash
# PhazeOS Dual Boot Support
# Detects and configures Windows 11 for dual boot

echo "=========================================="
echo "    PHAZEOS DUAL BOOT SUPPORT"
echo "    Windows 11 Detection & Configuration"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs root privileges."
    echo "Please run: sudo $0"
    exit 1
fi

# Detect Windows partitions
echo "🔍 Detecting Windows 11 installation..."
WINDOWS_PARTITIONS=$(lsblk -o NAME,FSTYPE,MOUNTPOINT | grep -i ntfs | grep -v loop)

if [ -z "$WINDOWS_PARTITIONS" ]; then
    echo "⚠️  No Windows partitions detected."
    echo "If Windows is installed, ensure NTFS partitions are visible."
    exit 1
fi

echo "✅ Windows partitions detected:"
echo "$WINDOWS_PARTITIONS"
echo ""

# Detect EFI partition
echo "🔍 Detecting EFI partition..."
EFI_PARTITION=$(lsblk -o NAME,FSTYPE,MOUNTPOINT | grep -i efi | head -1 | awk '{print $1}')

if [ -z "$EFI_PARTITION" ]; then
    echo "⚠️  No EFI partition detected."
    echo "Dual boot requires UEFI firmware."
    exit 1
fi

echo "✅ EFI partition: /dev/$EFI_PARTITION"
echo ""

# Install required packages
echo "📦 Installing dual boot support packages..."
pacman -S --noconfirm ntfs-3g os-prober grub-efi-x86_64 efibootmgr

# Run os-prober to detect Windows
echo ""
echo "🔍 Running os-prober to detect Windows..."
os-prober

# Update GRUB to include Windows
echo ""
echo "🔄 Updating GRUB configuration..."
grub-mkconfig -o /boot/grub/grub.cfg

echo ""
echo "=========================================="
echo "    ✅ DUAL BOOT CONFIGURED!"
echo "=========================================="
echo ""
echo "Windows 11 should now appear in GRUB boot menu."
echo ""
echo "To verify:"
echo "  1. Reboot your system"
echo "  2. You should see GRUB menu with:"
echo "     - PhazeOS"
echo "     - Windows 11"
echo ""
echo "If Windows doesn't appear, run:"
echo "  sudo os-prober"
echo "  sudo update-grub"
echo ""
