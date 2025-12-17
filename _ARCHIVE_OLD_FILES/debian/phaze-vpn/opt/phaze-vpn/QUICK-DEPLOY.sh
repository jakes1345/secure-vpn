#!/bin/bash
# Quick deploy script - Run this on your LOCAL computer

echo "=========================================="
echo "QUICK DEPLOY TO VPS"
echo "=========================================="
echo ""

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_DIR="/opt/secure-vpn"

echo "This script will:"
echo "1. Upload updated web portal files"
echo "2. Apply speed optimizations on VPS"
echo "3. Restart services"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Step 1: Upload web portal files
echo ""
echo "1. Uploading web portal files..."
scp web-portal/app.py "$VPS_USER@$VPS_IP:$VPS_DIR/web-portal/" || {
    echo "✗ Failed to upload app.py"
    exit 1
}

scp -r web-portal/templates/mobile "$VPS_USER@$VPS_IP:$VPS_DIR/web-portal/templates/" || {
    echo "✗ Failed to upload mobile templates"
    exit 1
}

echo "✓ Files uploaded"
echo ""

# Step 2: Apply speed config and restart on VPS
echo "2. Applying speed optimizations on VPS..."
ssh "$VPS_USER@$VPS_IP" << 'ENDSSH'
cd /opt/secure-vpn

# Backup current config
cp config/server.conf config/server.conf.backup 2>/dev/null || true

# Create speed-optimized config
cat > config/server-fast.conf << 'EOFCONFIG'
# Secure VPN - SPEED OPTIMIZED Configuration
port 1194
proto udp
dev tun
topology subnet
server 10.8.0.0 255.255.255.0

# SPEED OPTIMIZATION
data-ciphers CHACHA20-POLY1305:AES-256-GCM
cipher CHACHA20-POLY1305
auth SHA256
tls-version-min 1.2
dh certs/dh.pem
tls-groups secp384r1

# Certificates
ca certs/ca.crt
cert certs/server.crt
key certs/server.key
tls-auth certs/ta.key 0

# Security
persist-key
persist-tun
remote-cert-tls client
verify-client-cert require

# SPEED OPTIMIZATION - Larger buffers
tun-mtu 1500
mssfix 1440
sndbuf 4194304
rcvbuf 4194304
push "sndbuf 4194304"
push "rcvbuf 4194304"

# Faster keepalive
keepalive 10 60

# DNS and Privacy
push "dhcp-option DNS 1.1.1.1"
push "dhcp-option DNS 1.0.0.1"
push "block-outside-dns"
push "redirect-gateway def1 bypass-dhcp"

# PRIVACY - Minimal logging
verb 1
mute 10
status logs/status.log 5
log-append logs/server.log

# Connection Limits
max-clients 200
explicit-exit-notify 1

# Compression disabled for speed
comp-lzo no
push "comp-lzo no"

# Memory Protection
mlock

# Scripts
script-security 2
up scripts/up.sh
down scripts/down.sh

status-version 2
EOFCONFIG

# Copy to main config
cp config/server-fast.conf config/server.conf

# Restart OpenVPN
sudo systemctl restart secure-vpn
sleep 3

# Verify
if systemctl is-active --quiet secure-vpn; then
    echo "✓ OpenVPN restarted successfully"
else
    echo "✗ OpenVPN failed - check logs"
    sudo journalctl -u secure-vpn -n 10
fi
ENDSSH

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test from browser: https://phazevpn.duckdns.org"
echo "2. Test mobile monitor: https://phazevpn.duckdns.org/mobile/monitor"
echo "3. Test VPN connection speed"
echo ""

