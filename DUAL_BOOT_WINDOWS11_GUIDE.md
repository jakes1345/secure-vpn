# Dual Boot PhazeOS with Windows 11 - Complete Guide

## 🎯 Overview

This guide helps you install PhazeOS alongside Windows 11 on the same computer.

**Requirements:**
- Windows 11 already installed
- UEFI firmware (modern computers)
- At least 50GB free space for PhazeOS
- USB drive for PhazeOS ISO

---

## 📋 Pre-Installation Steps

### 1. **Disable Windows Fast Startup**
Windows Fast Startup can cause issues with dual boot.

1. Open **Control Panel** → **Power Options**
2. Click **"Choose what the power buttons do"**
3. Click **"Change settings that are currently unavailable"**
4. **Uncheck** "Turn on fast startup"
5. Click **Save changes**

### 2. **Disable Secure Boot** (Temporary)
Secure Boot can prevent Linux from booting.

1. Restart and enter **BIOS/UEFI** (usually F2, F12, or Del)
2. Find **Secure Boot** setting
3. **Disable** Secure Boot
4. Save and exit

**Note:** You can re-enable it after installation if PhazeOS supports it.

### 3. **Shrink Windows Partition**
Make space for PhazeOS.

**Option A: Using Windows Disk Management**
1. Press `Win + X` → **Disk Management**
2. Right-click **C:** drive → **Shrink Volume**
3. Enter amount (e.g., 50000 MB = ~50GB)
4. Click **Shrink**

**Option B: Using PhazeOS Installer**
- The installer can resize Windows partitions during installation

---

## 💿 Installation Steps

### 1. **Boot from PhazeOS USB**
1. Insert PhazeOS USB drive
2. Restart computer
3. Press boot menu key (F12, F8, or Esc)
4. Select USB drive
5. Boot PhazeOS

### 2. **Run PhazeOS Installer**
1. Double-click **"Install PhazeOS"** on desktop
2. Follow installer wizard

### 3. **Partitioning for Dual Boot**

**Recommended Setup:**
```
/dev/sda1  EFI System Partition (Windows) - Keep as is
/dev/sda2  Windows C: Drive - Keep as is
/dev/sda3  PhazeOS Root (/) - 40GB+ ext4
/dev/sda4  PhazeOS Home (/home) - Remaining space ext4
/dev/sda5  Swap - 8GB (optional but recommended)
```

**In Installer:**
1. Select **"Install alongside Windows 11"** (if available)
2. Or **Manual partitioning**:
   - Select free space
   - Create `/` partition (ext4, 40GB+)
   - Create `/home` partition (ext4, remaining space)
   - Create swap (8GB)
   - **DO NOT** format Windows partitions!

### 4. **Bootloader Configuration**

**GRUB Setup:**
- Installer should detect Windows 11 automatically
- GRUB will be installed to EFI partition
- Windows 11 will appear in boot menu

**If Windows doesn't appear:**
```bash
# After installation, run:
sudo os-prober
sudo update-grub
```

### 5. **Complete Installation**
1. Set username/password
2. Select software to install
3. Wait for installation
4. Reboot

---

## 🔄 Post-Installation

### 1. **Boot Menu**
On startup, you'll see GRUB menu:
- **PhazeOS** (default)
- **Windows 11**
- **Advanced options**

Select what you want to boot.

### 2. **Set Default OS** (Optional)
```bash
# Edit GRUB config
sudo nano /etc/default/grub

# Change GRUB_DEFAULT to Windows entry number
# Save and run:
sudo update-grub
```

### 3. **Access Windows Files from PhazeOS**
Windows partitions will be automatically detected:
- Open **Dolphin** file manager
- Windows C: drive appears as **"Windows"**
- You can read files (write requires ntfs-3g)

**Mount manually if needed:**
```bash
# Create mount point
sudo mkdir /mnt/windows

# Mount Windows C: drive
sudo mount -t ntfs-3g /dev/sda2 /mnt/windows

# Access files
cd /mnt/windows/Users/YourName
```

### 4. **Access PhazeOS Files from Windows**
**Option A: Use WSL2** (Windows Subsystem for Linux)
- Install WSL2 in Windows
- Access Linux filesystem

**Option B: Use Ext2Fsd** (Third-party tool)
- Install Ext2Fsd in Windows
- Mount PhazeOS partitions
- **Warning:** Can corrupt Linux filesystem if not careful

**Option C: Use Network Share**
- Share files over network
- Access from Windows

---

## ⚙️ Configuration

### 1. **Time Sync Issue** (Common Problem)
Windows and Linux handle time differently.

**Fix in PhazeOS:**
```bash
# Set Linux to use local time (like Windows)
sudo timedatectl set-local-rtc 1
```

**Or fix in Windows:**
```powershell
# Run in PowerShell as admin
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\TimeZoneInformation" /v RealTimeIsUniversal /d 1 /t REG_DWORD /f
```

### 2. **Windows Updates**
Windows updates can overwrite bootloader.

**If Windows overwrites GRUB:**
1. Boot from PhazeOS USB
2. Chroot into installed system
3. Reinstall GRUB:
```bash
sudo mount /dev/sda3 /mnt
sudo mount /dev/sda1 /mnt/boot/efi
sudo arch-chroot /mnt
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=PhazeOS
update-grub
exit
```

### 3. **Secure Boot** (Optional)
If you want Secure Boot enabled:

1. Install **shim** and **PreLoader**
2. Sign GRUB with your key
3. Add key to UEFI firmware
4. Enable Secure Boot

**Note:** This is advanced and not required.

---

## 🛠️ Troubleshooting

### Problem: Windows doesn't appear in boot menu
**Solution:**
```bash
sudo os-prober
sudo update-grub
```

### Problem: Can't boot Windows after PhazeOS install
**Solution:**
- Boot from Windows recovery USB
- Run: `bootrec /fixmbr` and `bootrec /fixboot`
- Or use Windows Startup Repair

### Problem: Time is wrong in one OS
**Solution:**
- See "Time Sync Issue" above

### Problem: Can't access Windows files
**Solution:**
```bash
# Install NTFS support (should be included)
sudo pacman -S ntfs-3g

# Mount Windows drive
sudo mount -t ntfs-3g /dev/sda2 /mnt/windows
```

### Problem: GRUB menu doesn't appear
**Solution:**
- Check UEFI boot order
- Ensure GRUB is first in boot order
- Disable Windows Fast Startup

---

## ✅ What PhazeOS Includes for Dual Boot

### Already Included:
- ✅ **GRUB bootloader** - Detects Windows automatically
- ✅ **NTFS-3G** - Read Windows files
- ✅ **os-prober** - Auto-detect Windows
- ✅ **EFI support** - UEFI boot support

### What You Get:
- ✅ Boot menu with both OSs
- ✅ Access Windows files from PhazeOS
- ✅ Time sync fixes
- ✅ Proper partitioning tools

---

## 🎯 Recommended Setup

### Partition Layout:
```
EFI:     512MB  (shared with Windows)
Windows: 200GB+ (keep Windows C: drive)
PhazeOS: 50GB+  (/)
Home:    100GB+ (/home)
Swap:    8GB    (swap)
```

### Boot Order:
1. **GRUB** (PhazeOS bootloader)
2. Choose OS from menu

### Default OS:
- Set PhazeOS as default (faster boot)
- Or Windows if you use it more

---

## 📝 Quick Reference

### Boot into Windows from PhazeOS:
```bash
# Reboot and select Windows from GRUB menu
# Or set Windows as default in GRUB config
```

### Boot into PhazeOS from Windows:
- Restart and select PhazeOS from boot menu
- Or set PhazeOS as default boot option in UEFI

### Access Windows Files:
- Open Dolphin → Windows drive appears automatically
- Or mount manually: `sudo mount -t ntfs-3g /dev/sda2 /mnt/windows`

---

## ⚠️ Important Notes

1. **Backup Windows** before installing PhazeOS
2. **Don't delete Windows partitions** during installation
3. **Keep EFI partition** - both OSs need it
4. **Windows updates** can break GRUB (easy to fix)
5. **Time sync** - configure one OS to use local time

---

## 🚀 That's It!

You now have:
- ✅ Windows 11 (for Windows apps/games)
- ✅ PhazeOS (for privacy, hacking, gaming, dev)
- ✅ Boot menu to choose
- ✅ Access files from both OSs

**Enjoy dual booting!**
