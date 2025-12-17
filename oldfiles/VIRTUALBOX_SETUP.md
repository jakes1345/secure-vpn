# VirtualBox Setup for PhazeOS Testing

## Why VirtualBox?
- ✅ **Easier GUI** - Point and click interface
- ✅ **Better mouse/keyboard** - Seamless integration
- ✅ **Screenshot support** - Easy to document
- ✅ **Snapshots** - Save VM state
- ✅ **Free and open source**

## Quick Install

```bash
# Install VirtualBox
sudo apt update
sudo apt install -y virtualbox virtualbox-ext-pack

# Add your user to vboxusers group (for USB support)
sudo usermod -aG vboxusers $USER

# Log out and back in for group changes to take effect
```

## Automated Setup

```bash
# Run the setup script
./setup_virtualbox.sh
```

## Manual Setup

### 1. Create VM in VirtualBox GUI:
- **Name:** PhazeOS-Test
- **Type:** Linux
- **Version:** Arch Linux (64-bit)
- **RAM:** 6144 MB (6GB) or more
- **Hard disk:** Create new, 20GB+, VDI format

### 2. Configure VM:
- **Settings → System → Processor:** Enable PAE/NX, 2+ CPUs
- **Settings → Display:** 
  - Video Memory: 128MB
  - Graphics Controller: VBoxSVGA
- **Settings → Storage:**
  - Controller: IDE → Empty → Choose disk file
  - Select: `phazeos-build/out/archlinux-2025.12.08-x86_64.iso`

### 3. Boot:
- Click "Start"
- Select "Arch Linux install medium (x86_64, BIOS)" from boot menu
- Wait for desktop to load

## Alternative: GNOME Boxes (Even Simpler!)

If you're on GNOME desktop:

```bash
sudo apt install -y gnome-boxes
```

Then:
1. Open GNOME Boxes
2. Click "+" → "Create a Virtual Machine"
3. Select your ISO file
4. Click "Create"
5. Boot!

## Command Line (Advanced)

```bash
# Create VM
VBoxManage createvm --name PhazeOS-Test --ostype ArchLinux_64 --register
VBoxManage modifyvm PhazeOS-Test --memory 6144 --vram 128
VBoxManage createhd --filename ~/PhazeOS-Test.vdi --size 20480
VBoxManage storagectl PhazeOS-Test --name "SATA" --add sata
VBoxManage storageattach PhazeOS-Test --storagectl "SATA" --port 0 --device 0 --type hdd --medium ~/PhazeOS-Test.vdi
VBoxManage storagectl PhazeOS-Test --name "IDE" --add ide
VBoxManage storageattach PhazeOS-Test --storagectl "IDE" --port 0 --device 0 --type dvddrive --medium phazeos-build/out/archlinux-2025.12.08-x86_64.iso

# Start VM
VBoxManage startvm PhazeOS-Test --type gui
```

## Troubleshooting

**VM won't start:**
- Check virtualization is enabled in BIOS
- Install: `sudo apt install linux-headers-$(uname -r)`
- Rebuild kernel modules: `sudo /sbin/vboxconfig`

**Slow performance:**
- Enable 3D acceleration in Display settings
- Increase video memory to 128MB+
- Enable hardware acceleration (VT-x/AMD-V)

**Mouse/keyboard issues:**
- Install VirtualBox Guest Additions in the VM
- Or use "Insert" key to release mouse
