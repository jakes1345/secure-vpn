#!/bin/bash
# Setup VirtualBox for PhazeOS ISO testing

echo "=========================================="
echo "    SETTING UP VIRTUALBOX"
echo "=========================================="
echo ""

# Check if already installed
if command -v virtualbox &> /dev/null || command -v VBoxManage &> /dev/null; then
    echo "✅ VirtualBox is already installed!"
    VBoxManage --version
    echo ""
else
    echo "📦 Installing VirtualBox..."
    echo ""
    echo "Run these commands:"
    echo "  sudo apt update"
    echo "  sudo apt install -y virtualbox virtualbox-ext-pack"
    echo ""
    read -p "Press Enter after installing VirtualBox, or Ctrl+C to cancel..."
fi

ISO_FILE="/media/jack/Liunux/secure-vpn/phazeos-build/out/archlinux-2025.12.08-x86_64.iso"

if [ ! -f "$ISO_FILE" ]; then
    echo "❌ ISO not found: $ISO_FILE"
    exit 1
fi

echo ""
echo "=========================================="
echo "    CREATING VIRTUALBOX VM"
echo "=========================================="
echo ""

VM_NAME="PhazeOS-Test"
VM_RAM=6144  # 6GB
VM_DISK=20480  # 20GB

# Check if VM already exists
if VBoxManage showvminfo "$VM_NAME" &>/dev/null; then
    echo "⚠️  VM '$VM_NAME' already exists!"
    read -p "Delete and recreate? (y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        VBoxManage unregistervm "$VM_NAME" --delete
        echo "✅ Deleted old VM"
    else
        echo "Using existing VM"
        exit 0
    fi
fi

echo "Creating VM: $VM_NAME"
echo "  RAM: ${VM_RAM}MB"
echo "  Disk: ${VM_DISK}MB"
echo ""

# Create VM
VBoxManage createvm --name "$VM_NAME" --ostype "ArchLinux_64" --register

# Configure VM
VBoxManage modifyvm "$VM_NAME" \
    --memory "$VM_RAM" \
    --vram 128 \
    --acpi on \
    --boot1 dvd \
    --boot2 disk \
    --boot3 none \
    --boot4 none \
    --graphicscontroller vboxsvga \
    --audio none \
    --usb on \
    --usbehci on

# Create and attach disk
echo "Creating virtual disk..."
VBoxManage createhd --filename "$HOME/VirtualBox VMs/$VM_NAME/$VM_NAME.vdi" \
    --size "$VM_DISK" --format VDI

VBoxManage storagectl "$VM_NAME" --name "SATA Controller" --add sata --controller IntelAHCI
VBoxManage storageattach "$VM_NAME" --storagectl "SATA Controller" \
    --port 0 --device 0 --type hdd \
    --medium "$HOME/VirtualBox VMs/$VM_NAME/$VM_NAME.vdi"

# Attach ISO
echo "Attaching ISO..."
VBoxManage storagectl "$VM_NAME" --name "IDE Controller" --add ide --controller PIIX4
VBoxManage storageattach "$VM_NAME" --storagectl "IDE Controller" \
    --port 0 --device 0 --type dvddrive \
    --medium "$ISO_FILE"

# Enable hardware acceleration if available
VBoxManage modifyvm "$VM_NAME" --paravirtprovider kvm

echo ""
echo "✅ VM created successfully!"
echo ""
echo "=========================================="
echo "    NEXT STEPS"
echo "=========================================="
echo ""
echo "1. Open VirtualBox GUI:"
echo "   virtualbox &"
echo ""
echo "2. Or start the VM from command line:"
echo "   VBoxManage startvm \"$VM_NAME\" --type gui"
echo ""
echo "3. In VirtualBox:"
echo "   - Select '$VM_NAME'"
echo "   - Click 'Start'"
echo "   - Select 'Arch Linux install medium (x86_64, BIOS)' from boot menu"
echo "   - Wait for desktop to load"
echo ""
