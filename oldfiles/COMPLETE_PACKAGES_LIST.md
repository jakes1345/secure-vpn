# PhazeOS Complete Package List
# This is the FULL package list with ALL missing components added

## TIER 1: CORE SYSTEM (CRITICAL)

### Kernel & Base
linux-zen
linux-zen-headers
linux-firmware
base
base-devel

### CPU Microcode
amd-ucode
intel-ucode

### Filesystem & Snapshots
btrfs-progs
timeshift
dosfstools
mtools
rsync

### Boot & System
grub
efibootmgr
os-prober
networkmanager
sudo

## TIER 2: DESKTOP ENVIRONMENT (KDE PLASMA)

### KDE Plasma Full Suite
plasma-meta
plasma-wayland-session
plasma-nm
plasma-pa
kscreen
powerdevil
kinfocenter
kdeplasma-addons
konsole
dolphin
dolphin-plugins
ark
spectacle
gwenview
okular
kate
kcalc
kwrite
plasma-systemmonitor
kwalletmanager

### Display Server
xorg-server
xorg-xinit
xorg-xinput
mesa-utils
wayland

### Audio (Pipewire)
pipewire
pipewire-pulse
pipewire-alsa
pipewire-jack
wireplumber

## TIER 3: FIRMWARE (HARDWARE SUPPORT)

### Base Firmware
linux-firmware
linux-firmware-marvell

### Network Firmware
linux-firmware-qlogic
linux-firmware-bnx2x
linux-firmware-liquidio
linux-firmware-mellanox
linux-firmware-nfp

### Wireless Firmware
# Note: Most wireless firmware is in linux-firmware package
# These are for specific chipsets if needed

### Bluetooth Firmware
# Included in linux-firmware

### Audio Firmware
sof-firmware
wireless-regdb

## TIER 4: GAMING (PERFORMANCE OPTIMIZED)

### Game Platforms
steam
lutris
wine
wine-staging
winetricks
flatpak

### Gaming Optimization
gamemode
lib32-gamemode
mangohud
lib32-mangohud

### Graphics Drivers
mesa
lib32-mesa
xf86-video-amdgpu
xf86-video-intel
intel-media-driver
libva-intel-driver
intel-gpu-tools
xf86-video-vesa
mesa-demos
vulkan-radeon
lib32-vulkan-radeon
vulkan-intel
lib32-vulkan-intel
vulkan-icd-loader
lib32-vulkan-icd-loader
nvidia
nvidia-utils
nvidia-settings
lib32-nvidia-utils

### 32-bit Gaming Libraries
lib32-openal
lib32-libpulse
lib32-alsa-plugins
lib32-gtk3
lib32-gnutls

### Game Controllers
# xboxdrv (AUR)
# antimicrox (AUR)

### Performance Tools
# corectrl (AUR)
# goverlay (AUR)

## TIER 5: SECURITY & PRIVACY

### Firewall & Security
ufw
apparmor
firewalld
iptables
nftables

### VPN
openvpn
wireguard-tools
openresolv
resolvconf

### Tor
tor
torsocks

### Privacy Tools
veracrypt
mat2
macchanger
proxychains-ng

## TIER 6: HACKING & SECURITY

### Network Scanning
nmap
wireshark-qt
aircrack-ng
tcpdump
ettercap
# bettercap (AUR)

### Password Cracking
hashcat
john
hydra

### Web Security
# burpsuite (AUR)
# sqlmap (AUR)
nikto
dirb
# gobuster (AUR)
# ffuf (AUR)

### Reverse Engineering
radare2
# rizin (AUR)
# cutter (AUR)
# ghidra (AUR)

### Forensics
# autopsy (AUR)
sleuthkit
binwalk
foremost

### Exploitation
# metasploit (AUR)

## TIER 7: AI & DEVELOPMENT

### Code Editors
code
neovim
vim

### Development Tools
docker
docker-compose
git
git-lfs
github-cli
nodejs
npm
python
python-pip
go
rust
cmake
ninja
meson
extra-cmake-modules

### Compilers
gcc
clang
jdk-openjdk

### Debuggers
gdb
valgrind
strace
ltrace

### Python ML Libraries
python-pytorch
python-numpy
python-pandas
python-scikit-learn
python-matplotlib
python-seaborn
jupyter-notebook
jupyterlab
python-ipykernel
python-ipywidgets

### AI Tools
# ollama (install script)

## TIER 8: CREATIVE & PRODUCTIVITY

### Media
obs-studio
kdenlive
audacity
vlc
mpv
ffmpeg
handbrake
gimp
krita
blender
inkscape

### Audio Production
# ardour (AUR)
# lmms (AUR)

### Photo Editing
# darktable (AUR)
# rawtherapee (AUR)
imagemagick

### Office
libreoffice-fresh
thunderbird

### Note-taking
# obsidian (AUR)
# joplin (AUR)

### Password Managers
# bitwarden (AUR)
keepassxc

### PDF Tools
# pdfarranger (AUR)
# xournalpp (AUR)

## TIER 9: BROWSERS

### Firefox
firefox

### PhazeBrowser Dependencies
qt6-base
qt6-webengine
qt6-declarative
qt6-svg
qt6-multimedia
qt6-webchannel
qt6-positioning
qt6-translations

## TIER 10: SYSTEM UTILITIES

### Monitoring
btop
htop
lm_sensors
neofetch
fastfetch
lshw
dmidecode
inxi

### System Management
bleachbit
gparted
baobab

### Disk Tools
smartmontools
hdparm
nvme-cli
# clonezilla (live ISO)
ddrescue
testdisk
photorec

### Backup
rclone
duplicity
# borg (AUR)

### Compression
p7zip
unrar
unzip
zip

### Network Tools
net-tools
inetutils
bind
traceroute
whois
wget
curl
qbittorrent

### Communication
discord
telegram-desktop

### Printing
cups
hplip
system-config-printer

### Bluetooth
bluez
bluez-utils
bluedevil

## TIER 11: FONTS

### Programming Fonts
ttf-dejavu
ttf-liberation
ttf-jetbrains-mono
ttf-jetbrains-mono-nerd
ttf-fira-code
ttf-hack

### System Fonts
noto-fonts
noto-fonts-emoji
noto-fonts-cjk
ttf-roboto
ttf-ubuntu-font-family

## TIER 12: TERMINAL ENHANCEMENTS

### Shell
fish
bash-completion

### Tools
tmux
fzf
bat
ripgrep
eza
fd

## TIER 13: THEMES

### Icon Themes
papirus-icon-theme

### GTK Themes
breeze-gtk

### Screenshot
flameshot

## TIER 14: PACKAGE MANAGEMENT

### Helpers
reflector
pacman-contrib

### AUR Helpers (install after base system)
# yay (install script)
# paru (install script)

## TIER 15: FYNE/GO GUI DEPENDENCIES

### X11 Libraries
libgl
libxcursor
libxrandr
libxinerama
libxi
libxxf86vm
libx11

## TIER 16: DIAGNOSTICS

### Hardware
pciutils
usbutils
stress

---

## AUR PACKAGES (Install via yay/paru after base install)

```bash
# AUR Helper
yay

# Gaming
heroic-games-launcher-bin
bottles
corectrl
goverlay
xboxdrv
antimicrox

# Security
burpsuite
metasploit
ghidra
rizin
cutter
sqlmap
gobuster
ffuf
bettercap

# Productivity
obsidian
joplin-desktop
bitwarden
pdfarranger
xournalpp
typora

# Creative
ardour
lmms
darktable
rawtherapee

# System
borg
```

---

## FLATPAK PACKAGES (Install via flatpak)

```bash
# Gaming
com.heroicgameslauncher.hgl
com.usebottles.bottles
org.prismlauncher.PrismLauncher

# Communication
com.discordapp.Discord
org.telegram.desktop

# Productivity
md.obsidian.Obsidian
net.cozic.joplin_desktop
com.bitwarden.desktop
```

---

## POST-INSTALL SCRIPTS

### Install Ollama (AI)
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
```

### Install AUR Helper (yay)
```bash
cd /tmp
git clone https://aur.archlinux.org/yay.git
cd yay
makepkg -si --noconfirm
```

---

## TOTAL PACKAGE COUNT

- **Official Repos:** ~180 packages
- **AUR:** ~30 packages
- **Flatpak:** ~10 packages
- **Custom Scripts:** 5+ scripts

**TOTAL:** ~225 packages + custom components
