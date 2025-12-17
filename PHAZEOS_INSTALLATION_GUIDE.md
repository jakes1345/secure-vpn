# PhazeOS Installation Guide

## 🔥 Welcome to PhazeOS
The ultimate all-in-one operating system for gaming, hacking, AI/ML, and privacy.

---

## 📋 System Requirements

- **CPU:** 64-bit dual-core or better
- **RAM:** 4GB minimum (8GB recommended)
- **Storage:** 20GB minimum (50GB+ recommended)
- **GPU:** NVIDIA, AMD, or Intel (any modern GPU)
- **UEFI:** Required (Legacy BIOS not supported)

---

## 💿 Creating a Bootable USB

### On Linux:
```bash
sudo dd if=phazeos-latest.iso of=/dev/sdX bs=4M status=progress
sync
```
Replace `/dev/sdX` with your USB device (check with `lsblk`)

### On Windows:
1. Download [Rufus](https://rufus.ie/)
2. Select the PhazeOS ISO
3. Choose "GPT" partition scheme
4. Click "Start"

### On macOS:
```bash
sudo dd if=phazeos-latest.iso of=/dev/diskX bs=4m
```
Replace `/dev/diskX` with your USB device (check with `diskutil list`)

---

## 🚀 Installation Steps

### 1. Boot from USB
- Insert USB drive
- Restart computer
- Press F12/F2/DEL (depends on your motherboard) to enter boot menu
- Select USB drive

### 2. Live Environment
You'll boot into a live KDE Plasma environment. You can test PhazeOS before installing!

### 3. Install to Disk
1. Open the installer (should auto-launch)
2. Select your language and timezone
3. **Partition your disk:**
   - **Automatic:** Let the installer handle everything (recommended)
   - **Manual:** Create partitions yourself
     - `/boot/efi` - 512MB (FAT32)
     - `/` - Rest of disk (BTRFS recommended)
     - `swap` - Optional (if you have <8GB RAM)

4. Create your user account
5. Click "Install"
6. Wait 10-15 minutes
7. Reboot

### 4. Post-Install Customization
After rebooting into your new system:

```bash
sudo bash /root/phazeos_customize.sh
```

This will:
- Enable system services
- Set up Fish shell
- Apply cyberpunk theme
- Configure gaming optimizations
- Set up PhazeVPN integration
- Apply privacy hardening

---

## 🎮 Gaming Setup

### Steam
Already installed! Just launch and log in.

### Lutris (Epic, GOG, etc.)
```bash
lutris
```
Add your game accounts and start playing!

### Heroic Games Launcher
For Epic and GOG games:
```bash
heroic
```

### Performance Tweaks
- **GameMode:** Automatically enabled for Steam games
- **MangoHUD:** Press `Shift+F12` in-game to toggle FPS overlay
- **CoreCtrl:** Launch from app menu for GPU/CPU overclocking

---

## 🔐 PhazeVPN Setup

1. Visit [https://phazevpn.com](https://phazevpn.com)
2. Create an account or log in
3. Download your VPN config files
4. Place them in `~/.config/phazevpn/`
5. Launch PhazeVPN from the app menu

**Quick Connect:**
```bash
vpn
```

---

## ⚔️ Hacking Tools

All tools are pre-installed and ready to use:

### Network Scanning
```bash
nmap -sV target.com
```

### WiFi Hacking
```bash
sudo airmon-ng start wlan0
sudo airodump-ng wlan0mon
```

### Password Cracking
```bash
hashcat -m 0 -a 0 hashes.txt wordlist.txt
john --wordlist=wordlist.txt hashes.txt
```

### Packet Analysis
```bash
wireshark
```

### Reverse Engineering
```bash
radare2 binary
```

---

## 🤖 AI/ML Development

### Jupyter Notebook
```bash
jupyter notebook
```

### PyTorch
```python
import torch
print(torch.cuda.is_available())  # Check GPU support
```

### TensorFlow
```python
import tensorflow as tf
print(tf.config.list_physical_devices('GPU'))
```

---

## 🛠️ Development Tools

### VSCodium (VS Code without telemetry)
Launch from app menu or:
```bash
codium
```

### Docker
```bash
sudo systemctl start docker
docker run hello-world
```

### Git
Already configured! Just set your identity:
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

## 🎨 Customization

### Change Theme
System Settings → Appearance → Global Theme

### Install More Software
```bash
sudo pacman -S package-name
```

### AUR (Arch User Repository)
```bash
yay -S package-name
```

---

## 📸 Snapshots (Timeshift)

PhazeOS uses BTRFS with automatic snapshots:

### Create Manual Snapshot
```bash
sudo timeshift --create --comments "Before big change"
```

### Restore from Snapshot
```bash
sudo timeshift --list
sudo timeshift --restore
```

---

## 🔧 Troubleshooting

### WiFi Not Working
```bash
sudo systemctl start NetworkManager
nmtui  # Text-based network manager
```

### Graphics Issues (NVIDIA)
```bash
sudo pacman -S nvidia nvidia-utils
sudo reboot
```

### Sound Not Working
```bash
systemctl --user restart pipewire
```

### Update System
```bash
sudo pacman -Syu
```

---

## 📚 Useful Commands

| Command | Description |
|---------|-------------|
| `btop` | System monitor |
| `neofetch` | System info |
| `ll` | List files (with icons) |
| `vpn` | Launch PhazeVPN |
| `cat file.txt` | View file (with syntax highlighting) |

---

## 🆘 Support

- **Website:** [https://phazevpn.com](https://phazevpn.com)
- **Email:** support@phazevpn.com
- **Documentation:** [https://phazevpn.com/docs](https://phazevpn.com/docs)

---

## ⚠️ Legal Disclaimer

PhazeOS includes security testing tools for **educational and authorized testing purposes only**. 

**You are responsible for:**
- Obtaining proper authorization before testing any systems
- Complying with all applicable laws and regulations
- Using these tools ethically and legally

**Unauthorized access to computer systems is illegal.** The developers of PhazeOS are not responsible for misuse of these tools.

---

## 🎉 Enjoy PhazeOS!

You're now running the most powerful all-in-one operating system ever created. 

**Game hard. Hack smart. Stay private.**

---

*PhazeOS - Built with ❤️ by the PhazeVPN Team*
