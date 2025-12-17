#!/bin/bash
# PhazeOS Post-Install Customization Script
# Run this after installing PhazeOS to your system

echo "=========================================="
echo "    PHAZEOS CUSTOMIZATION WIZARD"
echo "    Making your system legendary..."
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs root privileges."
    echo "Please run: sudo $0"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$ACTUAL_USER)

echo "👤 Configuring for user: $ACTUAL_USER"
echo ""

# ============================================
# STEP 1: SYSTEM SERVICES
# ============================================
echo "🔧 [1/6] Enabling system services..."

systemctl enable NetworkManager
systemctl enable bluetooth
systemctl enable docker
systemctl enable cronie  # For timeshift auto-snapshots

echo "✅ Services enabled"
echo ""

# ============================================
# STEP 2: FISH SHELL (DEFAULT)
# ============================================
echo "🐟 [2/6] Setting Fish as default shell..."

chsh -s /usr/bin/fish $ACTUAL_USER

# Create Fish config
mkdir -p "$USER_HOME/.config/fish"
cat > "$USER_HOME/.config/fish/config.fish" << 'FISHEOF'
# PhazeOS Fish Configuration

# Greeting
function fish_greeting
    echo ""
    echo "  ██████╗ ██╗  ██╗ █████╗ ███████╗███████╗ ██████╗ ███████╗"
    echo "  ██╔══██╗██║  ██║██╔══██╗╚══███╔╝██╔════╝██╔═══██╗██╔════╝"
    echo "  ██████╔╝███████║███████║  ███╔╝ █████╗  ██║   ██║███████╗"
    echo "  ██╔═══╝ ██╔══██║██╔══██║ ███╔╝  ██╔══╝  ██║   ██║╚════██║"
    echo "  ██║     ██║  ██║██║  ██║███████╗███████╗╚██████╔╝███████║"
    echo "  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚══════╝"
    echo ""
    echo "  🔥 The Ultimate All-in-One Operating System"
    echo ""
end

# Aliases
alias ls='eza --icons'
alias ll='eza -la --icons'
alias cat='bat'
alias grep='rg'
alias find='fd'
alias top='btop'

# PhazeVPN Quick Launch
alias vpn='phazevpn-gui'
FISHEOF

chown -R $ACTUAL_USER:$ACTUAL_USER "$USER_HOME/.config/fish"

echo "✅ Fish shell configured"
echo ""

# ============================================
# STEP 3: KDE PLASMA THEME (CYBERPUNK)
# ============================================
echo "🎨 [3/6] Installing cyberpunk theme..."

# Install Layan theme (dark, modern)
sudo -u $ACTUAL_USER git clone https://github.com/vinceliuice/Layan-kde.git /tmp/layan-theme 2>/dev/null
if [ -d /tmp/layan-theme ]; then
    cd /tmp/layan-theme
    ./install.sh
    cd -
    rm -rf /tmp/layan-theme
fi

# Set Kvantum theme
mkdir -p "$USER_HOME/.config/Kvantum"
cat > "$USER_HOME/.config/Kvantum/kvantum.kvconfig" << 'KVANTUMEOF'
[General]
theme=KvArcDark
KVANTUMEOF

chown -R $ACTUAL_USER:$ACTUAL_USER "$USER_HOME/.config/Kvantum"

# Set Papirus icons (already installed)
kwriteconfig5 --file "$USER_HOME/.config/kdeglobals" --group Icons --key Theme Papirus-Dark

echo "✅ Theme installed (Layan Dark + Papirus Icons)"
echo ""

# ============================================
# STEP 4: GAMING OPTIMIZATIONS
# ============================================
echo "🎮 [4/6] Configuring gaming optimizations..."

# Enable GameMode
systemctl --user enable gamemoded

# Create MangoHUD config
mkdir -p "$USER_HOME/.config/MangoHud"
cat > "$USER_HOME/.config/MangoHud/MangoHud.conf" << 'MANGOEOF'
# PhazeOS MangoHUD Configuration
fps
gpu_stats
cpu_stats
ram
vram
frame_timing=1
position=top-left
background_alpha=0.5
font_size=24
MANGOEOF

chown -R $ACTUAL_USER:$ACTUAL_USER "$USER_HOME/.config/MangoHud"

# Add user to gamemode group
usermod -aG gamemode $ACTUAL_USER

echo "✅ Gaming optimizations enabled"
echo ""

# ============================================
# STEP 5: PHAZEVPN INTEGRATION
# ============================================
echo "🔐 [5/6] Setting up PhazeVPN..."

# Create PhazeVPN config directory
mkdir -p "$USER_HOME/.config/phazevpn"

cat > "$USER_HOME/.config/phazevpn/config.json" << 'VPNEOF'
{
  "auto_connect": false,
  "server": "phazevpn.com",
  "protocol": "wireguard",
  "dns_leak_protection": true,
  "kill_switch": true
}
VPNEOF

chown -R $ACTUAL_USER:$ACTUAL_USER "$USER_HOME/.config/phazevpn"

echo "✅ PhazeVPN configured (visit phazevpn.com to get credentials)"
echo ""

# ============================================
# STEP 6: PRIVACY HARDENING
# ============================================
echo "🛡️  [6/6] Applying privacy hardening..."

# Disable telemetry
systemctl disable systemd-resolved 2>/dev/null || true

# Configure PhazeBrowser as Default
# (PhazeBrowser is already hardened via enterprise policies in /opt/phazebrowser/distribution)

if [ -f /usr/local/bin/phazebrowser ]; then
    xdg-settings set default-web-browser phazebrowser.desktop 2>/dev/null || true
    echo "✅ PhazeBrowser set as default"
else
    echo "⚠️  PhazeBrowser not found"
fi

chown -R $ACTUAL_USER:$ACTUAL_USER "$USER_HOME/.librewolf"

# Enable MAC address randomization
cat > /etc/NetworkManager/conf.d/wifi-random-mac.conf << 'MACEOF'
[device]
wifi.scan-rand-mac-address=yes

[connection]
wifi.cloned-mac-address=random
ethernet.cloned-mac-address=random
MACEOF

echo "✅ Privacy hardening complete"
echo ""

# ============================================
# FINAL MESSAGE
# ============================================
echo "=========================================="
echo "    ✅ PHAZEOS SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "🎉 Your system is now fully configured!"
echo ""
echo "Next Steps:"
echo "  1. Reboot your system"
echo "  2. Visit https://phazevpn.com to get VPN credentials"
echo "  3. Enjoy your legendary operating system!"
echo ""
echo "Useful Commands:"
echo "  vpn          - Launch PhazeVPN GUI"
echo "  btop         - System monitor"
echo "  fastfetch    - System info"
echo ""
echo "Need help? Visit: https://phazevpn.com/support"
echo "=========================================="
