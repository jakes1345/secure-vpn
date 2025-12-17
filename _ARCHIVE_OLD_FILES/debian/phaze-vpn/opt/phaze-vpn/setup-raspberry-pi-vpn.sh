#!/bin/bash
# Complete Raspberry Pi 5 VPN Setup Script
# Sets up OpenVPN + WireGuard + Web Dashboard

set -e

echo "=========================================="
echo "🍓 RASPBERRY PI 5 VPN SETUP"
echo "=========================================="
echo ""
echo "This will install:"
echo "  ✅ OpenVPN server"
echo "  ✅ WireGuard server (faster!)"
echo "  ✅ Web management dashboard"
echo "  ✅ Dynamic DNS (DDNS) support"
echo ""

# Check if running on Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Warning: This doesn't look like a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system..."
sudo apt update
sudo apt upgrade -y

# Install dependencies
echo ""
echo "📦 Installing VPN software..."
sudo apt install -y \
    openvpn \
    wireguard \
    wireguard-tools \
    iptables \
    ufw \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    certbot \
    python3-certbot-nginx

# Install WireGuard
if ! command -v wg &> /dev/null; then
    echo "📦 Installing WireGuard..."
    sudo apt install -y wireguard wireguard-tools
fi

# Enable IP forwarding
echo ""
echo "🔧 Enabling IP forwarding..."
sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sudo sysctl -p

# Configure firewall
echo ""
echo "🔒 Configuring firewall..."
sudo ufw allow 1194/udp  # OpenVPN
sudo ufw allow 51820/udp # WireGuard
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable

# Create directories
VPN_DIR="/opt/phazevpn-pi"
sudo mkdir -p "$VPN_DIR"/{certs,configs,wireguard,logs}

echo ""
echo "✅ Base system configured!"
echo ""
echo "Next steps:"
echo "  1. Generate certificates"
echo "  2. Setup OpenVPN config"
echo "  3. Setup WireGuard config"
echo "  4. Configure web dashboard"
echo ""

