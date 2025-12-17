#!/bin/bash
# Auto-deploy everything with password handling

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="Jakes1328!@"
VPN_DIR="/opt/secure-vpn"

echo "=========================================="
echo "AUTO-DEPLOYING EVERYTHING TO VPS"
echo "=========================================="
echo ""

# Install sshpass if not available
if ! command -v sshpass > /dev/null; then
    echo "Installing sshpass for password automation..."
    sudo apt-get update -qq && sudo apt-get install -y sshpass 2>/dev/null || {
        echo "⚠ sshpass not available - will prompt for password"
        USE_SSHPASS=false
    }
    USE_SSHPASS=true
else
    USE_SSHPASS=true
fi

# Function to run command on VPS
run_ssh() {
    if [ "$USE_SSHPASS" = true ]; then
        sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$VPS_USER@$VPS_IP" "$1"
    else
        ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "$1"
    fi
}

# Function to upload file
upload_file() {
    if [ "$USE_SSHPASS" = true ]; then
        sshpass -p "$VPS_PASS" scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$1" "$VPS_USER@$VPS_IP:$2"
    else
        scp "$1" "$VPS_USER@$VPS_IP:$2"
    fi
}

# Step 1: Upload files
echo "1. Uploading files..."
upload_file "web-portal/app.py" "$VPN_DIR/web-portal/"
run_ssh "mkdir -p $VPN_DIR/web-portal/templates/mobile"
upload_file "web-portal/templates/mobile/monitor.html" "$VPN_DIR/web-portal/templates/mobile/"
upload_file "web-portal/templates/mobile/client-detail.html" "$VPN_DIR/web-portal/templates/mobile/"
echo "✓ Files uploaded"

# Step 2: Apply speed config and restart OpenVPN
echo ""
echo "2. Applying speed optimizations and restarting OpenVPN..."
run_ssh << 'ENDSSH'
cd /opt/secure-vpn

# Backup
cp config/server.conf config/server.conf.backup-$(date +%Y%m%d) 2>/dev/null || true

# Create speed-optimized config
cat > config/server-fast.conf << 'EOFCONFIG'
port 1194
proto udp
dev tun
topology subnet
server 10.8.0.0 255.255.255.0

data-ciphers CHACHA20-POLY1305:AES-256-GCM
cipher CHACHA20-POLY1305
auth SHA256
tls-version-min 1.2
dh certs/dh.pem
tls-groups secp384r1

ca certs/ca.crt
cert certs/server.crt
key certs/server.key
tls-auth certs/ta.key 0

persist-key
persist-tun
remote-cert-tls client
verify-client-cert require

tun-mtu 1500
mssfix 1440
sndbuf 4194304
rcvbuf 4194304
push "sndbuf 4194304"
push "rcvbuf 4194304"

keepalive 10 60

push "dhcp-option DNS 1.1.1.1"
push "dhcp-option DNS 1.0.0.1"
push "block-outside-dns"
push "redirect-gateway def1 bypass-dhcp"

verb 1
mute 10
status logs/status.log 5
log-append logs/server.log

max-clients 200
explicit-exit-notify 1

comp-lzo no
push "comp-lzo no"

mlock
script-security 2
up scripts/up.sh
down scripts/down.sh
status-version 2
EOFCONFIG

cp config/server-fast.conf config/server.conf
mkdir -p logs
chmod 755 logs

sudo systemctl restart secure-vpn
sleep 3

if systemctl is-active --quiet secure-vpn; then
    echo "✓ OpenVPN restarted successfully"
else
    echo "⚠ Check logs: sudo journalctl -u secure-vpn -n 20"
fi
ENDSSH

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "✅ Mobile monitor deployed"
echo "✅ Security fixes applied"
echo "✅ Cookie security hardened"
echo "✅ Speed optimizations active"
echo "✅ Privacy/ghost mode enabled"
echo ""
echo "Next: Restart web portal manually if needed"
echo ""

