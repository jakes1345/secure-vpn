#!/bin/bash
# 🚀 VPS Deployment Script using CMake
# Builds and deploys all PhazeVPN services to VPS
# Run this ON THE VPS after uploading source files

set -e

VPS_INSTALL_DIR="/opt/phaze-vpn"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "🚀 PhazeVPN VPS Deployment (CMake)"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Error: This script must be run as root (use sudo)"
    exit 1
fi

# Check for CMake
if ! command -v cmake &> /dev/null; then
    echo "📦 Installing CMake..."
    apt-get update
    apt-get install -y cmake build-essential
fi

# Check for Go (if building protocol server)
if ! command -v go &> /dev/null; then
    echo "📦 Installing Go..."
    apt-get install -y golang-go
fi

# Check for Python dependencies
echo "📦 Installing Python dependencies..."
apt-get install -y python3 python3-pip python3-venv python3-dev
apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1 || true

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get install -y \
    openvpn \
    openssl \
    nginx \
    certbot \
    python3-certbot-nginx \
    gunicorn \
    git \
    curl \
    wget \
    ufw \
    iptables-persistent

# Create build directory
BUILD_DIR="${SCRIPT_DIR}/build-vps"
echo "🔨 Creating build directory: ${BUILD_DIR}"
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# Configure CMake for VPS installation
echo ""
echo "⚙️  Configuring CMake for VPS..."
cmake "${SCRIPT_DIR}" \
    -DCMAKE_BUILD_TYPE=Release \
    -DINSTALL_TO_SYSTEM=ON \
    -DCMAKE_INSTALL_PREFIX="${VPS_INSTALL_DIR}" \
    -DBUILD_PROTOCOL_GO=ON \
    -DBUILD_WEB_PORTAL=ON \
    -DBUILD_PROTOCOL_PYTHON=ON \
    -DBUILD_BROWSER=ON \
    -DINSTALL_SYSTEMD_SERVICES=ON

# Build all services
echo ""
echo "🔨 Building all services..."
cmake --build . --config Release -j$(nproc)

# Install to system
echo ""
echo "📦 Installing to ${VPS_INSTALL_DIR}..."
cmake --install .

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p "${VPS_INSTALL_DIR}"/{logs,data,backups,uploads}
mkdir -p "${VPS_INSTALL_DIR}"/web-portal/{logs,data,uploads}
mkdir -p "${VPS_INSTALL_DIR}"/phazevpn-protocol/{logs,data}

# Set permissions
echo "🔐 Setting permissions..."
chown -R root:root "${VPS_INSTALL_DIR}"
chmod 755 "${VPS_INSTALL_DIR}"
chmod 600 "${VPS_INSTALL_DIR}"/certs/*.key 2>/dev/null || true
chown -R www-data:www-data "${VPS_INSTALL_DIR}"/web-portal 2>/dev/null || true

# Install Python dependencies for services
echo ""
echo "📦 Installing Python dependencies..."
if [ -f "${VPS_INSTALL_DIR}/web-portal/requirements.txt" ]; then
    pip3 install -r "${VPS_INSTALL_DIR}/web-portal/requirements.txt"
fi
if [ -f "${VPS_INSTALL_DIR}/phazevpn-protocol/requirements.txt" ]; then
    pip3 install -r "${VPS_INSTALL_DIR}/phazevpn-protocol/requirements.txt"
fi

# Setup systemd services
echo ""
echo "🔧 Setting up systemd services..."
systemctl daemon-reload

# Enable services (but don't start yet - let user configure first)
if [ -f "/etc/systemd/system/phazevpn-portal.service" ]; then
    echo "✅ phazevpn-portal.service installed"
fi
if [ -f "/etc/systemd/system/phazevpn-protocol.service" ]; then
    echo "✅ phazevpn-protocol.service installed"
fi
if [ -f "/etc/systemd/system/phazevpn-protocol-go.service" ]; then
    echo "✅ phazevpn-protocol-go.service installed"
fi

# Setup firewall
echo ""
echo "🔥 Configuring firewall..."
ufw --force enable || true
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 1194/udp  # OpenVPN
ufw allow 51820/udp # PhazeVPN Protocol
ufw allow 5000/tcp  # Web Portal (internal)
echo "✅ Firewall configured"

# Setup IP forwarding for VPN
echo ""
echo "🌐 Setting up IP forwarding..."
if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
fi
sysctl -p

# Setup NAT for VPN
if ! command -v iptables-persistent &> /dev/null; then
    apt-get install -y iptables-persistent
fi

# Add NAT rules if not present
if ! iptables -t nat -C POSTROUTING -s 10.8.0.0/24 -j MASQUERADE 2>/dev/null; then
    iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -j MASQUERADE
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || iptables-save > /etc/iptables.rules
fi
echo "✅ IP forwarding configured"

# Create Nginx configuration for web portal
echo ""
echo "🌐 Configuring Nginx..."
if [ ! -f /etc/nginx/sites-available/phazevpn ]; then
    cat > /etc/nginx/sites-available/phazevpn << 'NGINX_EOF'
server {
    listen 80;
    server_name _;
    
    # Web Portal
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Static files
    location /static/ {
        alias /opt/phaze-vpn/web-portal/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_EOF
    
    ln -sf /etc/nginx/sites-available/phazevpn /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl restart nginx
    echo "✅ Nginx configured"
else
    echo "⚠️  Nginx config already exists, skipping..."
fi

# Summary
echo ""
echo "=========================================="
echo "✅ VPS Deployment Complete!"
echo "=========================================="
echo ""
echo "Installation directory: ${VPS_INSTALL_DIR}"
echo ""
echo "Services installed:"
ls -1 /etc/systemd/system/phazevpn-*.service 2>/dev/null | sed 's|.*/||' | sed 's/^/  - /' || echo "  (none found)"
echo ""
echo "Next steps:"
echo "1. Configure certificates: cd ${VPS_INSTALL_DIR} && ./generate-certs.sh"
echo "2. Configure web portal: Edit ${VPS_INSTALL_DIR}/web-portal/app.py"
echo "3. Start services:"
echo "   sudo systemctl enable phazevpn-portal"
echo "   sudo systemctl enable phazevpn-protocol"
echo "   sudo systemctl start phazevpn-portal"
echo "   sudo systemctl start phazevpn-protocol"
echo ""
echo "4. Setup SSL (if domain configured):"
echo "   sudo certbot --nginx -d yourdomain.com"
echo ""

