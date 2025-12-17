#!/bin/bash
# Quick VirtualBox Test for PhazeOS

VM_NAME="PhazeOS-Test"
ISO_PATH="/media/jack/Liunux/secure-vpn/phazeos-build/out/phazeos-2025.12.10-x86_64.iso"

echo "🚀 Creating VirtualBox VM for PhazeOS..."

# Delete old VM if exists
VBoxManage unregistervm "$VM_NAME" --delete 2>/dev/null

# Create new VM
VBoxManage createvm --name "$VM_NAME" --ostype "ArchLinux_64" --register

# Configure VM
VBoxManage modifyvm "$VM_NAME" \
  --memory 8192 \
  --cpus 4 \
  --vram 128 \
  --graphicscontroller vmsvga \
  --boot1 dvd \
  --boot2 disk \
  --boot3 none \
  --boot4 none \
  --audio-driver pulse \
  --audiocontroller hda \
  --clipboard-mode bidirectional

# Create virtual hard disk (20GB)
VBoxManage createhd --filename "$HOME/VirtualBox VMs/$VM_NAME/$VM_NAME.vdi" --size 20480

# Add storage controllers
VBoxManage storagectl "$VM_NAME" --name "SATA" --add sata --controller IntelAhci
VBoxManage storageattach "$VM_NAME" --storagectl "SATA" --port 0 --device 0 --type hdd --medium "$HOME/VirtualBox VMs/$VM_NAME/$VM_NAME.vdi"

VBoxManage storagectl "$VM_NAME" --name "IDE" --add ide
VBoxManage storageattach "$VM_NAME" --storagectl "IDE" --port 0 --device 0 --type dvddrive --medium "$ISO_PATH"

echo "✅ VM Created!"
echo ""
echo "Starting VM..."
VBoxManage startvm "$VM_NAME" --type gui

echo ""
echo "🎮 PhazeOS should now be booting in VirtualBox!"
echo "   - If you want to install, click 'Install PhazeOS' on the desktop"
echo "   - If you just want to test, use it as a live system"
echo ""
echo "To stop: VBoxManage controlvm '$VM_NAME' poweroff"
