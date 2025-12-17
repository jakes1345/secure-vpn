#!/bin/bash
# PhazeOS ISO Builder - The Ultimate All-in-One OS (LOGIC FIX)
# "Gaming. Hacking. AI. Privacy. Everything."

BUILD_DIR="$(pwd)/phazeos-build"
PROFILE_DIR="$BUILD_DIR/phazeos-profile"
OUT_DIR="$BUILD_DIR/out"

echo "========================================"
echo "    PHAZE OS ULTIMATE EDITION"
echo "    Researched. Optimized. Unstoppable."
echo "========================================"

mkdir -p $PROFILE_DIR
mkdir -p $OUT_DIR

# Define The Complete Package List (Clean & Stable)
cat > $BUILD_DIR/packages.x86_64 << 'EOF'
# ============================================
# TIER 1: CORE SYSTEM (CRITICAL)
# ============================================

# Kernel & Base
linux-zen
linux-zen-headers
linux-firmware
base
base-devel

# CPU Microcode
amd-ucode
intel-ucode

# Filesystem & Snapshots
btrfs-progs
timeshift
dosfstools
mtools
rsync

# Boot & System
grub
efibootmgr
os-prober
networkmanager
sudo

# ============================================
# TIER 2: DESKTOP ENVIRONMENT (KDE PLASMA)
# ============================================

# KDE Plasma Full Suite
plasma-meta
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

# Display Server
xorg-server
xorg-xinit
xorg-xinput
mesa-utils
wayland

# Audio (Pipewire)
pipewire
pipewire-pulse
pipewire-alsa
pipewire-jack
wireplumber

# File Manager Extras
kdegraphics-thumbnailers
ffmpegthumbs
taglib

# ============================================
# TIER 3: FIRMWARE (COMPLETE HARDWARE SUPPORT)
# ============================================

# Base Firmware
linux-firmware
linux-firmware-marvell
linux-firmware-qlogic
linux-firmware-bnx2x

# Audio Firmware
sof-firmware
wireless-regdb

# ============================================
# TIER 4: GAMING (PERFORMANCE OPTIMIZED)
# ============================================

# Game Platforms
steam
lutris
wine
wine-staging
winetricks
flatpak

# Gaming Optimization
gamemode
lib32-gamemode
mangohud
lib32-mangohud

# Graphics Drivers (Explicit & Stable)
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
lib32-nvidia-utils
nvidia-settings

# 32-bit Gaming Libraries (CRITICAL)
lib32-openal
lib32-libpulse
lib32-alsa-plugins
lib32-gtk3
lib32-gnutls

# ============================================
# TIER 5: SECURITY & PRIVACY
# ============================================

# Firewall & Security
ufw
apparmor
firewalld
iptables
nftables

# VPN
openvpn
wireguard-tools
openresolv

# Tor
tor
torsocks

# Privacy Tools
veracrypt
mat2
macchanger
proxychains-ng

# ============================================
# TIER 6: HACKING & SECURITY
# ============================================

# Network Scanning
nmap
wireshark-qt
aircrack-ng
tcpdump
ettercap

# Password Cracking
hashcat
john
hydra

# Web Security
nikto

# Reverse Engineering
radare2

# Forensics
sleuthkit
binwalk
foremost

# ============================================
# TIER 7: AI & DEVELOPMENT
# ============================================

# Code Editors
code
neovim
vim

# Development Tools
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

# Compilers
gcc
clang
jdk-openjdk

# Debuggers
gdb
valgrind
strace
ltrace

# Python ML Libraries
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

# ============================================
# TIER 8: CREATIVE & PRODUCTIVITY
# ============================================

# Media
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

# Photo Editing
imagemagick

# Office
libreoffice-fresh
thunderbird

# Password Managers
keepassxc

# ============================================
# TIER 9: BROWSERS
# ============================================

firefox

# PhazeBrowser Dependencies
qt6-base
qt6-webengine
qt6-declarative
qt6-svg
qt6-multimedia
qt6-webchannel
qt6-positioning
qt6-translations

# ============================================
# TIER 10: SYSTEM UTILITIES
# ============================================

# Monitoring
btop
htop
fastfetch
lshw
dmidecode
inxi

# System Management
bleachbit
gparted
baobab

# Disk Tools
smartmontools
hdparm
nvme-cli
ddrescue
testdisk

# Backup
rclone
duplicity

# Compression
p7zip
unrar
unzip
zip

# Fonts (Complete)
ttf-dejavu
ttf-liberation
noto-fonts
noto-fonts-emoji
noto-fonts-cjk
ttf-jetbrains-mono
ttf-jetbrains-mono-nerd
ttf-fira-code
ttf-hack
ttf-roboto
ttf-ubuntu-font-family

# Networking
qbittorrent
discord
telegram-desktop
net-tools
inetutils
bind
traceroute
whois
wget
curl

# Printing
cups
hplip
system-config-printer

# Bluetooth
bluez
bluez-utils
bluedevil

# Package Management
reflector
pacman-contrib

# ============================================
# TIER 11: TERMINAL ENHANCEMENTS
# ============================================

fish
bash-completion
tmux
fzf
bat
ripgrep
eza
fd

# ============================================
# TIER 12: THEMES & APPEARANCE
# ============================================

papirus-icon-theme
breeze-gtk

# ============================================
# TIER 13: UTILITIES
# ============================================

flameshot

# ============================================
# TIER 14: DIAGNOSTICS
# ============================================

pciutils
usbutils
lm_sensors
stress

# ============================================
# TIER 15: FYNE/GO GUI DEPENDENCIES
# ============================================

libgl
libxcursor
libxrandr
libxinerama
libxi
libxxf86vm
libx11

EOF

# Create the Build Script (runs INSIDE Docker)
cat > $BUILD_DIR/entrypoint.sh << 'BUILDSCRIPT'
#!/bin/bash
echo "🐧 Inside Arch Container..."

# Enable Multilib
echo "🔓 Enabling Multilib..."
cat >> /etc/pacman.conf << PACMANEOF
[multilib]
Include = /etc/pacman.d/mirrorlist
PACMANEOF

# Update references
pacman -Syy

# Install archiso
pacman -S --noconfirm archiso

# Setup Profile
mkdir -p /work/profile
cp -r /usr/share/archiso/configs/releng/* /work/profile/

# Modify archiso mkinitcpio configuration to reduce firmware warnings
# The warnings are for enterprise/server hardware modules (ast, liquidio, qed, etc.)
# These are harmless but noisy. We'll modify the archiso.conf to be less verbose
if [ -f /work/profile/airootfs/etc/mkinitcpio.conf.d/archiso.conf ]; then
    # The archiso.conf file controls what modules are included
    # We can't easily exclude specific modules, but we can note that warnings are normal
    echo "# Note: Firmware warnings for enterprise modules are normal and harmless" >> /work/profile/airootfs/etc/mkinitcpio.conf.d/archiso.conf
fi

# Enable Multilib in the ISO's pacman.conf
cat >> /work/profile/pacman.conf << PACMANEOF
[multilib]
Include = /etc/pacman.d/mirrorlist
PACMANEOF

# Inject Packages
cat /build/phazeos-build/packages.x86_64 >> /work/profile/packages.x86_64

# Copy setup scripts to ISO (with existence checks)
mkdir -p /work/profile/airootfs/usr/local/bin/
mkdir -p /work/profile/airootfs/root/

# Copy the main customization wizard
if [ -f /build/phazeos_customize.sh ]; then
    cp /build/phazeos_customize.sh /work/profile/airootfs/usr/local/bin/phazeos-wizard
    chmod +x /work/profile/airootfs/usr/local/bin/phazeos-wizard
else
    echo "⚠️  Warning: phazeos_customize.sh not found, skipping..."
fi

# Copy AI Pod setup
if [ -f /build/setup-ai-pod.sh ]; then
    cp /build/setup-ai-pod.sh /work/profile/airootfs/usr/local/bin/phazeos-setup-ai
    chmod +x /work/profile/airootfs/usr/local/bin/phazeos-setup-ai
else
    echo "⚠️  Warning: setup-ai-pod.sh not found, skipping..."
fi

# Create post-install message (MOTD)
mkdir -p /work/profile/airootfs/etc/
cat > /work/profile/airootfs/etc/motd << 'MOTDEOF'
================================================================
   WELCOME TO PHAZEOS - THE ULTIMATE STEALTH WORKSTATION
================================================================

To finish setting up your environment, run:
  > sudo phazeos-wizard    (System, Theme, Gaming)
  > sudo phazeos-setup-ai  (AI Models, Ollama)
  > sudo phazeos-features  (Panic Button, Unique Tools)

================================================================
MOTDEOF

# Customization: PhazeOS Branding
echo 'PhazeOS' > /work/profile/airootfs/etc/hostname

# Set default shell to Fish
echo '/usr/bin/fish' > /work/profile/airootfs/etc/shells

# Create profiledef.sh (ISO Configuration) - Fixed deprecated boot modes
cat > /work/profile/profiledef.sh << PROFILEDEFEOF
iso_name="phazeos"
iso_label="PHAZEOS_$(date +%Y%m)"
iso_publisher="PhazeOS <https://phazeos.org>"
iso_application="PhazeOS Live/Install Media"
iso_version="$(date +%Y.%m.%d)"
install_dir="arch"
buildmodes=('iso')
bootmodes=('bios.syslinux' 'uefi.grub')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '9' '-b' '1M')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/root"]="0:0:750"
  ["/root/.automated_script.sh"]="0:0:755"
  ["/usr/local/bin/choose-mirror"]="0:0:755"
  ["/usr/local/bin/Installation_guide"]="0:0:755"
  ["/usr/local/bin/phazeos-wizard"]="0:0:755"
  ["/usr/local/bin/phazeos-setup-ai"]="0:0:755"
  ["/usr/local/bin/phazeos-construct/installer"]="0:0:755"
  ["/usr/local/bin/panic"]="0:0:755"
  ["/usr/local/bin/phaze-mode"]="0:0:755"
  ["/usr/local/bin/ghost-mode"]="0:0:755"
  ["/usr/local/bin/gaming-mode"]="0:0:755"
  ["/usr/local/bin/dev-mode"]="0:0:755"
  ["/usr/local/bin/phazeos-features"]="0:0:755"
  ["/usr/local/bin/phazeos-install-ollama"]="0:0:755"
  ["/usr/local/bin/phazevpn-cli"]="0:0:755"
  ["/opt/phazeos/first-boot-wizard/first_boot_wizard.sh"]="0:0:755"
  ["/opt/phazeos/first-boot-wizard/autostart.sh"]="0:0:755"
)
PROFILEDEFEOF

# ==================================================================
# LOGIC FIX: EXECUTE SETUP COMMANDS DIRECTLY (NO MORE WRAPPER SCRIPT)
# ==================================================================

echo "🎨 Setting up PhazeOS Components..."

# 1. Build and Copy The Construct (Go Installer)
if [ -d /build/phazeos-construct ]; then
    echo "🔨 Building phazeos-construct..."
    cd /build/phazeos-construct
    if [ -f go.mod ]; then
        go mod tidy
        go build -buildvcs=false -o phazeos-construct . || echo "⚠️  Warning: Failed to build phazeos-construct"
    fi
    
    mkdir -p /work/profile/airootfs/usr/local/bin/phazeos-construct
    mkdir -p /work/profile/airootfs/usr/local/bin/phazeos-construct/assets
    
    if [ -f /build/phazeos-construct/phazeos-construct ]; then
        cp /build/phazeos-construct/phazeos-construct /work/profile/airootfs/usr/local/bin/phazeos-construct/installer
        chmod +x /work/profile/airootfs/usr/local/bin/phazeos-construct/installer
    fi

    if [ -f /build/phazeos-construct/phazeos-install-backend.sh ]; then
        cp /build/phazeos-construct/phazeos-install-backend.sh /work/profile/airootfs/usr/local/bin/phazeos-install-backend
        chmod +x /work/profile/airootfs/usr/local/bin/phazeos-install-backend
    fi
    
    # Copy assets if they exist
    if [ -d /build/phazeos-construct/assets ]; then
        cp -r /build/phazeos-construct/assets/* /work/profile/airootfs/usr/local/bin/phazeos-construct/assets/ 2>/dev/null || true
    fi
else
    echo "⚠️  Warning: phazeos-construct directory not found, skipping..."
fi

# 2. Configure SDDM for Live Session (Real Desktop Experience)
# Add sddm to package list first (injecting here or ensuring it's in list)
# Add sddm to package list first
echo "sddm" >> /work/profile/packages.x86_64
# plasma-meta includes necessary configuration modules


# Enable SDDM Service
# systemctl enable sddm --root=/work/profile/airootfs

# Configure Autologin for liveuser
mkdir -p /work/profile/airootfs/etc/sddm.conf.d
cat > /work/profile/airootfs/etc/sddm.conf.d/autologin.conf << 'SDDMEOF'
[Autologin]
User=liveuser
Session=plasma
SDDMEOF

# Create 'Install PhazeOS' Desktop Shortcut
mkdir -p /work/profile/airootfs/home/liveuser/Desktop
cat > /work/profile/airootfs/home/liveuser/Desktop/install-phazeos.desktop << 'DESKTOPEOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Install PhazeOS
Comment=Launch The Construct Installer
Exec=sudo /usr/local/bin/phazeos-construct/installer
Icon=system-os-installer
Terminal=false
Categories=System;
DESKTOPEOF

chmod +x /work/profile/airootfs/home/liveuser/Desktop/install-phazeos.desktop
chown -R 1000:1000 /work/profile/airootfs/home/liveuser/Desktop

# 3. Create Panic Button Service (Super+Delete -> Wipe)
cat > /work/profile/airootfs/etc/systemd/system/phaze-panic.service << 'PANICEOF'
[Unit]
Description=PhazeOS Panic Protocol
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'shred -vn 1 /home/*; reboot'
PANICEOF

# 4. Panic Trigger script
mkdir -p /work/profile/airootfs/usr/local/bin
echo "systemctl start phaze-panic.service" > /work/profile/airootfs/usr/local/bin/panic
chmod +x /work/profile/airootfs/usr/local/bin/panic

# 5. Build and Copy First Boot Wizard (Graphical Version)
if [ -d /build/phazeos-setup-gui ]; then
    echo "🔨 Building phazeos-setup-gui..."
    cd /build/phazeos-setup-gui
    if [ -f go.mod ]; then
        go mod tidy # Fetch raylib dependencies
        go build -buildvcs=false -o phazeos-setup . || echo "⚠️  Warning: Failed to build phazeos-setup"
    fi

    mkdir -p /work/profile/airootfs/opt/phazeos/first-boot-wizard
    
    if [ -f phazeos-setup ]; then
        cp phazeos-setup /work/profile/airootfs/opt/phazeos/first-boot-wizard/phazeos-setup-wizard
        chmod +x /work/profile/airootfs/opt/phazeos/first-boot-wizard/phazeos-setup-wizard
    fi
    
    # Copy autostart script (needs update to launch binary)
    if [ -f /build/phazeos-first-boot-wizard/autostart.sh ]; then
        cp /build/phazeos-first-boot-wizard/autostart.sh /work/profile/airootfs/opt/phazeos/first-boot-wizard/
    fi
    chmod +x /work/profile/airootfs/opt/phazeos/first-boot-wizard/*.sh 2>/dev/null || true
else
    echo "⚠️  Warning: phazeos-setup-gui directory not found, skipping..."
fi

# 7. Install Pre-Built Native PhazeBrowser (From Artifact)
if [ -f /build/PhazeBrowser-v1.0-Linux.tar.xz ]; then
    echo "📦 installing PhazeBrowser from artifact..."
    
    # Extract directly to a temporary location
    mkdir -p /tmp/phazebrowser_extract
    tar xJf /build/PhazeBrowser-v1.0-Linux.tar.xz -C /tmp/phazebrowser_extract
    
    # Move binary and resources
    # Depending on how we packed it, it might be in a 'phazebrowser' subdir
    if [ -d /tmp/phazebrowser_extract/phazebrowser ]; then
        # Install to opt
        mkdir -p /work/profile/airootfs/opt/phazebrowser
        cp -r /tmp/phazebrowser_extract/phazebrowser/* /work/profile/airootfs/opt/phazebrowser/
        
        # Symlink executable
        mkdir -p /work/profile/airootfs/usr/local/bin
        ln -sf /opt/phazebrowser/phazebrowser /work/profile/airootfs/usr/local/bin/phazebrowser
        
        # Create Desktop Entry
        mkdir -p /work/profile/airootfs/usr/share/applications/
        cat > /work/profile/airootfs/usr/share/applications/phazebrowser.desktop << 'DESKTOPEOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=PhazeBrowser
Comment=Native Privacy Browser
Exec=/usr/local/bin/phazebrowser
Icon=web-browser
Terminal=false
Categories=Network;WebBrowser;
DESKTOPEOF
        
        echo "✅ PhazeBrowser Native installed from artifact!"
    else
        echo "⚠️  Warning: PhazeBrowser artifact structure invalid."
        ls -F /tmp/phazebrowser_extract
    fi
    
    # Cleanup
    rm -rf /tmp/phazebrowser_extract
else
    echo "⚠️  Warning: PhazeBrowser artifact (/build/PhazeBrowser-v1.0-Linux.tar.xz) not found!"
fi

# 8. Build and Copy Native Go VPN Client
if [ -d /build/phazevpn-protocol-go ]; then
    echo "🔨 Building Native Go VPN Client..."
    cd /build/phazevpn-protocol-go
    if [ -f go.mod ]; then
        go mod tidy # Ensure deps
        # Build the GUI client
        if go build -o phazevpn-gui ./cmd/phazevpn-gui; then
            # Install Binary
            cp phazevpn-gui /work/profile/airootfs/usr/local/bin/phazevpn-gui
            chmod +x /work/profile/airootfs/usr/local/bin/phazevpn-gui
            
            # Create Desktop Entry
            mkdir -p /work/profile/airootfs/usr/share/applications/
            cat > /work/profile/airootfs/usr/share/applications/phazevpn-gui.desktop << 'DESKTOPEOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=PhazeVPN
Comment=Native Go VPN Client
Exec=phazevpn-gui
Icon=utilities-terminal
Terminal=false
Categories=Network;
DESKTOPEOF
            
            echo "✅ Native Go VPN Client installed!"
        else
            echo "⚠️  Warning: Failed to build phazevpn-gui"
        fi
    fi
else
    echo "⚠️  Warning: phazevpn-protocol-go directory not found, skipping..."
fi

# 6. Note: Fish shell will be set as default after packages are installed (already in /etc/shells)
# Note: cronie service will be enabled after packages are installed via customization script

# 7. Install PhazeOS Unique Feature Scripts
if [ -d /build/phazeos-scripts ]; then
    echo "🎯 Installing PhazeOS unique features..."
    
    # Copy all scripts
    cp /build/phazeos-scripts/phaze-mode /work/profile/airootfs/usr/local/bin/
    cp /build/phazeos-scripts/ghost-mode /work/profile/airootfs/usr/local/bin/
    cp /build/phazeos-scripts/gaming-mode /work/profile/airootfs/usr/local/bin/
    cp /build/phazeos-scripts/dev-mode /work/profile/airootfs/usr/local/bin/
    cp /build/phazeos-scripts/phazeos-features /work/profile/airootfs/usr/local/bin/
    cp /build/phazeos-scripts/phazeos-install-ollama /work/profile/airootfs/usr/local/bin/
    cp /build/phazeos-scripts/phazevpn-cli /work/profile/airootfs/usr/local/bin/
    
    # Make executable
    chmod +x /work/profile/airootfs/usr/local/bin/phaze-mode
    chmod +x /work/profile/airootfs/usr/local/bin/ghost-mode
    chmod +x /work/profile/airootfs/usr/local/bin/gaming-mode
    chmod +x /work/profile/airootfs/usr/local/bin/dev-mode
    chmod +x /work/profile/airootfs/usr/local/bin/phazeos-features
    chmod +x /work/profile/airootfs/usr/local/bin/phazeos-install-ollama
    chmod +x /work/profile/airootfs/usr/local/bin/phazevpn-cli
    
    # Create desktop shortcuts for unique features
    mkdir -p /work/profile/airootfs/home/liveuser/Desktop
    
    # PhazeOS Features launcher
    cat > /work/profile/airootfs/home/liveuser/Desktop/phazeos-features.desktop << 'DESKTOPEOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=PhazeOS Features
Comment=Access unique PhazeOS modes
Exec=konsole -e /usr/local/bin/phazeos-features
Icon=preferences-system
Terminal=false
Categories=System;
DESKTOPEOF
    chmod +x /work/profile/airootfs/home/liveuser/Desktop/phazeos-features.desktop
    
    # Install AI Assistant shortcut
    cat > /work/profile/airootfs/home/liveuser/Desktop/install-ai.desktop << 'DESKTOPEOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Install AI Assistant
Comment=Install Ollama and Llama 3.2
Exec=konsole -e sudo /usr/local/bin/phazeos-install-ollama
Icon=applications-science
Terminal=false
Categories=System;
DESKTOPEOF
    chmod +x /work/profile/airootfs/home/liveuser/Desktop/install-ai.desktop
    
    chown -R 1000:1000 /work/profile/airootfs/home/liveuser/Desktop
    
    echo "✅ PhazeOS unique features installed"
else
    echo "⚠️  Warning: phazeos-scripts directory not found, skipping..."
fi

# 9. Configure mkinitcpio (Modules & Hooks)
# CRITICAL: Include 'firmware' hook for early boot firmware loading
# This ensures firmware is available in initramfs for hardware initialization
cat > /work/profile/airootfs/etc/mkinitcpio.conf << MKINITCPIOEOF
# Graphics modules for desktop hardware
MODULES=(i915 amdgpu radeon nouveau)
BINARIES=()
FILES=()
HOOKS=(base udev autodetect modconf block filesystems keyboard firmware)
COMPRESSION="zstd"
MKINITCPIOEOF

# FIRMWARE WARNINGS EXPLANATION:
# The firmware warnings during build are NORMAL and HARMLESS
# They're for enterprise/server hardware modules that desktop users don't need:
# - ast (ASpeed graphics - server BMC)
# - liquidio, qed, bna, nfp (enterprise network adapters)  
# - mlxsw_spectrum (Mellanox switches)
# - bfa, qla1280, qla2xxx (Fibre Channel adapters)
# - aic94xx, wd719x (SCSI controllers)
# - xhci_pci_renesas (Renesas USB controllers)
# - softing_cs, adf7242 (specialized industrial hardware)
# 
# These modules are included by archiso's 'kms' hook for maximum compatibility
# but most desktop/gaming systems don't need them. The warnings can be safely ignored.
# Your ISO will work perfectly fine - these are just informational messages.

# The firmware hook includes firmware from /usr/lib/firmware into initramfs
# This is important for a live ISO where hardware detection happens early
# linux-firmware package (already in packages.x86_64) provides the firmware files

# 10. Regenerate initramfs (only after packages are installed)
# This will be done by mkarchiso automatically, but we can prepare the config

# 11. Build Reliability Fix: Licenses directory
mkdir -p /work/profile/airootfs/usr/share/licenses

# 12. Live User Creation (will be done after packages are installed)
# Create a custom script that runs after package installation
cat > /work/profile/airootfs/root/.automated_script.sh << 'AUTOEOF'
#!/bin/bash
# Post-install script that runs after packages are installed

# Create live user with fish shell (fish will be installed by then)
useradd -m -G wheel,video,audio,optical,storage -s /usr/bin/fish liveuser 2>/dev/null || true
echo "liveuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Enable cronie for timeshift snapshots (after it's installed)
systemctl enable cronie 2>/dev/null || true

# Set fish as default shell for root (after it's installed)
if [ -f /usr/bin/fish ]; then
    chsh -s /usr/bin/fish root 2>/dev/null || true
fi

# Enable SDDM (Display Manager)
systemctl enable sddm 2>/dev/null || true
AUTOEOF
chmod +x /work/profile/airootfs/root/.automated_script.sh

echo "✅ PhazeOS Setup Complete!"

# Build ISO
echo "🔥 Starting Build..."
echo ""
echo "ℹ️  NOTE: You may see firmware warnings for enterprise hardware modules during build."
echo "   These warnings are NORMAL and HARMLESS - they're for server hardware most"
echo "   desktop users don't have. Your ISO will work perfectly fine. Ignore them."
echo ""
# Note: mkarchiso will handle package installation and chroot setup automatically
# It will also run .automated_script.sh after packages are installed
mkarchiso -v -w /work/work -o /build/phazeos-build/out /work/profile

# List final output
echo "📦 Build Output:"
ls -lh /build/phazeos-build/out/ 2>/dev/null || echo "Output directory not found"
BUILDSCRIPT

chmod +x $BUILD_DIR/entrypoint.sh

# Run the Builder
echo "🐳 Launching Docker Builder..."
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker not running. Start Docker and try again."
    exit 1
fi

# Build Docker image
docker build -t phazeos-builder - <<DOCKERFILE
FROM archlinux:latest
RUN pacman -Scc --noconfirm && pacman-key --init && pacman -Syyu --noconfirm
# FIX: Explicitly install necessary tools for mkarchiso and Go
RUN pacman -S --noconfirm archiso git make grub libisoburn dosfstools mtools go cmake qt6-base qt6-webengine
WORKDIR /build
DOCKERFILE

# Run build - CRITICAL FIX: Mount project root, not just BUILD_DIR
# This allows access to phazeos_customize.sh, setup-ai-pod.sh, phazeos-construct, etc.
PROJECT_ROOT="$(pwd)"
docker run --privileged --rm --cap-add=ALL \
    -v /dev:/dev \
    -v "$PROJECT_ROOT:/build" \
    -v "$BUILD_DIR:/build/phazeos-build" \
    phazeos-builder /build/phazeos-build/entrypoint.sh

echo "========================================"
# Find the latest ISO file (handling multiple files correctly)
ISO_FILE=$(ls -t "$OUT_DIR"/*.iso 2>/dev/null | head -n1)

if [ -n "$ISO_FILE" ]; then
    ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)
    echo "✅ SUCCESS! PhazeOS ISO Created!"
    echo "📦 File: $ISO_FILE"
    echo "💾 Size: $ISO_SIZE"
    echo ""
    echo "Next Steps:"
    echo "1. Burn to USB: sudo dd if=$ISO_FILE of=/dev/sdX bs=4M status=progress"
    echo "2. Boot your machine from the USB to enter 'The Construct'"
else
    echo "❌ Build failed. Check logs above."
fi
echo "========================================"
