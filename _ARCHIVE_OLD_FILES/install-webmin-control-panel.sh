#!/bin/bash
# Install Webmin + Virtualmin Control Panel
# Get that control panel back!

set -e

echo "=========================================="
echo "🎛️  INSTALLING WEBMIN + VIRTUALMIN"
echo "   Getting your control panel back!"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Error: This script must be run as root (use sudo)"
    exit 1
fi

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "📡 Server IP: $SERVER_IP"
echo ""

# Update system
echo "📦 Updating system..."
apt update && apt upgrade -y

# Install dependencies
echo "📦 Installing dependencies..."
apt install -y wget curl perl libnet-ssleay-perl openssl libauthen-pam-perl libpam-runtime libio-pty-perl apt-show-versions python3 python3-pip unzip

# Download Webmin + Virtualmin installer
echo "📥 Downloading Webmin + Virtualmin installer..."
cd /tmp
wget https://software.virtualmin.com/gpl/scripts/virtualmin-install.sh

# Make executable
chmod +x virtualmin-install.sh

echo ""
echo "🚀 Starting installation..."
echo "   This will take 5-15 minutes..."
echo "   (The installer will ask some questions)"
echo ""

# Run installer
# Use --minimal flag for faster install (no full Virtualmin, just Webmin)
if [ "$1" == "--minimal" ]; then
    echo "📦 Installing Webmin only (minimal install)..."
    ./virtualmin-install.sh --minimal
else
    echo "📦 Installing Webmin + Virtualmin (full install)..."
    echo "   Press Enter to accept defaults when prompted"
    ./virtualmin-install.sh
fi

# Wait for installation
echo ""
echo "⏳ Installation in progress..."
echo "   Please wait..."

# Configure firewall
echo ""
echo "🔥 Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 10000/tcp comment "Webmin Control Panel"
    echo "✅ Firewall rule added for port 10000"
elif command -v iptables &> /dev/null; then
    iptables -A INPUT -p tcp --dport 10000 -j ACCEPT
    echo "✅ Firewall rule added for port 10000"
fi

# Get final status
echo ""
echo "=========================================="
echo "✅ INSTALLATION COMPLETE!"
echo "=========================================="
echo ""
echo "🎉 Your control panel is ready!"
echo ""
echo "📋 Access Information:"
echo "   URL: https://$SERVER_IP:10000"
echo "   Username: root"
echo "   Password: (your root password)"
echo ""
echo "🔐 Security Notes:"
echo "   - First login will show SSL warning (normal for self-signed cert)"
echo "   - You can setup Let's Encrypt SSL later in Webmin"
echo "   - Change the port in Webmin → Webmin Configuration → Ports and Addresses"
echo ""
echo "🛠️  What You Can Do Now:"
echo "   - View server stats (CPU, RAM, disk)"
echo "   - Manage files (upload/download/edit)"
echo "   - Start/stop services (VPN, etc.)"
echo "   - Manage users and permissions"
echo "   - View logs"
echo "   - Manage databases"
echo ""
echo "📖 Documentation:"
echo "   - Webmin: https://www.webmin.com/documentation.html"
echo "   - Virtualmin: https://www.virtualmin.com/documentation"
echo ""
echo "✅ Done! Access your control panel at:"
echo "   https://$SERVER_IP:10000"
echo ""
