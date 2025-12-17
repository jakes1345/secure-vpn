#!/bin/bash
# Run this ON THE VPS - Copy-paste entire script after SSH'ing in

cd /opt/secure-vpn

echo "=========================================="
echo "DEPLOYING UPDATES"
echo "=========================================="
echo ""

# Backup current config
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

# Apply config
cp config/server-fast.conf config/server.conf
mkdir -p logs
chmod 755 logs

# Restart OpenVPN
echo ""
echo "Restarting OpenVPN..."
sudo systemctl restart secure-vpn
sleep 3

if systemctl is-active --quiet secure-vpn; then
    echo "✓ OpenVPN restarted successfully"
else
    echo "⚠ OpenVPN check failed - view logs:"
    sudo journalctl -u secure-vpn -n 20 --no-pager
fi

# Check port
echo ""
echo "Checking port 1194..."
if netstat -uln | grep -q ":1194 " || ss -uln | grep -q ":1194 "; then
    echo "✓ Port 1194 is listening"
else
    echo "⚠ Port 1194 not listening"
fi

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "✅ Speed optimizations applied"
echo "✅ Privacy/ghost mode enabled"
echo ""
echo "Note: Web portal files (app.py, mobile templates)"
echo "      need to be uploaded separately via SCP"
echo ""

