# PhazeOS ISO Contents Analysis

## What's Currently in the Built ISO

### ✅ Packages Included:
```
CORE & DESKTOP:
- base, linux-hardened, linux-firmware
- plasma-meta (KDE Plasma)
- hyprland (tiling WM)
- konsole, dolphin, ark, spectacle, gwenview
- kitty, waybar, wofi
- networkmanager, neovim, firefox, git, base-devel, docker

CREATIVE & GAME DEV:
- godot, blender, gimp, obs-studio, vlc, audacity

GAMING:
- steam, gamemode, wine, winetricks

HACKING:
- nmap, wireshark-qt, aircrack-ng, hashcat, john, hydra, radare2

PRIVACY:
- bleachbit, mat2, veracrypt, tor, proxychains, wireguard-tools, openvpn
```

### ❌ NOT Included (But Mentioned in Manifest):
- **AI Tools:** Ollama, PyTorch, TensorFlow (mentioned but not in packages)
- **NVIDIA Drivers:** Not explicitly included
- **NVIDIA Container Toolkit:** Not included
- **Metasploit:** Commented out (needs BlackArch)
- **Bettercap, Burp Suite, SQLMap:** Commented out

### ✅ Custom Additions:
- First Boot Wizard (if directory exists)
- PhazeVPN Client (if .deb exists)
- PhazeOS branding (hostname)

---

## What's Missing for AI Pod

The manifest mentions an "AI Pod" but packages aren't included:
- ❌ Ollama (local LLMs)
- ❌ PyTorch
- ❌ TensorFlow
- ❌ NVIDIA drivers
- ❌ NVIDIA Container Toolkit

**These need to be added to packages.x86_64**
