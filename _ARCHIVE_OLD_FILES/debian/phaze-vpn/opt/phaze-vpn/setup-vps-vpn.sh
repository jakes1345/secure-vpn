#!/bin/bash
# Automated VPN Setup for OVH VPS
# This script will connect to the VPS and set up everything

set -e

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="Jakes1328!@"
VPN_DIR="/opt/secure-vpn"
LOCAL_DIR="/opt/phaze-vpn"

echo "=========================================="
echo "🚀 Automated VPN Setup for OVH VPS"
echo "=========================================="
echo ""

# Test connection first
echo "📡 Testing connection to VPS..."
if ! sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$VPS_USER@$VPS_IP" "echo 'Connected!'" 2>/dev/null; then
    echo "❌ Connection failed. Check password or VPS status."
    exit 1
fi
echo "✅ Connected to VPS!"
echo ""

# Step 1: Update system
echo "✅ Step 1/9: Updating system packages..."
sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "apt-get update -qq && apt-get upgrade -y -qq"
echo "✅ System updated"
echo ""

# Step 2: Install dependencies
echo "✅ Step 2/9: Installing dependencies..."
sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "apt-get install -y python3 python3-pip python3-tk openssl openvpn easy-rsa iptables ufw net-tools curl wget git build-essential debhelper devscripts sshpass 2>&1 | tail -5"
echo "✅ Dependencies installed"
echo ""

# Step 3: Create directories
echo "✅ Step 3/9: Creating VPN directories..."
sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "mkdir -p $VPN_DIR/{config,certs,client-configs,logs,scripts,backups} && chmod 755 $VPN_DIR"
echo "✅ Directories created"
echo ""

# Step 4: Transfer files
echo "✅ Step 4/9: Transferring VPN files..."
cd "$LOCAL_DIR"

# Create tarball with essential files
tar -czf /tmp/vpn-setup.tar.gz \
    vpn-manager.py \
    vpn-gui.py \
    client-download-server.py \
    subscription-manager.py \
    setup-routing.sh \
    open-download-port.sh \
    start-download-server-robust.sh \
    generate-certs.sh \
    manage-vpn.sh \
    templates/ \
    config/ 2>/dev/null || true

# Transfer to VPS
sshpass -p "$VPS_PASS" scp -o StrictHostKeyChecking=no /tmp/vpn-setup.tar.gz "$VPS_USER@$VPS_IP:/tmp/"

# Extract on VPS
sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "cd /tmp && tar -xzf vpn-setup.tar.gz && cp -r * $VPN_DIR/ 2>/dev/null || true && cp -r config/* $VPN_DIR/config/ 2>/dev/null || true && chmod +x $VPN_DIR/*.sh $VPN_DIR/*.py 2>/dev/null || true && rm -f /tmp/vpn-setup.tar.gz"

rm -f /tmp/vpn-setup.tar.gz
echo "✅ Files transferred"
echo ""

# Step 5: Install systemd services
echo "✅ Step 5/9: Installing systemd services..."
sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" << 'ENDSSH'
cat > /etc/systemd/system/secure-vpn.service << 'EOF'
[Unit]
Description=SecureVPN Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/secure-vpn
ExecStart=/usr/bin/python3 /opt/secure-vpn/vpn-manager.py start
ExecStop=/usr/bin/python3 /opt/secure-vpn/vpn-manager.py stop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/secure-vpn-download.service << 'EOF'
[Unit]
Description=SecureVPN Client Download Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/secure-vpn
ExecStart=/usr/bin/python3 /opt/secure-vpn/client-download-server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
ENDSSH
echo "✅ Services installed"
echo ""

# Step 6: Configure firewall
echo "✅ Step 6/9: Configuring firewall..."
sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "ufw --force enable && ufw allow 22/tcp && ufw allow 1194/udp && ufw allow 8081/tcp && ufw status | head -10"
echo "✅ Firewall configured"
echo ""

# Step 7: Generate certificates
echo "✅ Step 7/9: Generating certificates (this may take a few minutes)..."
sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "cd $VPN_DIR && bash generate-certs.sh 2>&1 | tail -20"
echo "✅ Certificates generated"
echo ""

# Step 8: Setup routing and configure VPN
echo "✅ Step 8/9: Configuring VPN and routing..."
sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "cd $VPN_DIR && python3 vpn-manager.py set-server-ip $VPS_IP && python3 vpn-manager.py init && bash setup-routing.sh 2>&1 | tail -10"
echo "✅ VPN configured"
echo ""

# Step 9: Start services
echo "✅ Step 9/9: Starting VPN services..."
sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "systemctl enable secure-vpn secure-vpn-download && systemctl start secure-vpn secure-vpn-download && sleep 3 && systemctl status secure-vpn --no-pager | head -15"
echo "✅ Services started"
echo ""

# Verify everything is running
echo "=========================================="
echo "🔍 Verifying setup..."
echo "=========================================="
sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" << 'ENDSSH'
echo "VPN Service Status:"
systemctl is-active secure-vpn && echo "✅ VPN service is running" || echo "❌ VPN service not running"

echo ""
echo "Download Service Status:"
systemctl is-active secure-vpn-download && echo "✅ Download service is running" || echo "❌ Download service not running"

echo ""
echo "OpenVPN Port (1194):"
netstat -tulpn | grep 1194 || echo "⚠️  Port 1194 not listening"

echo ""
echo "Download Server Port (8081):"
netstat -tulpn | grep 8081 || echo "⚠️  Port 8081 not listening"

echo ""
echo "IP Forwarding:"
cat /proc/sys/net/ipv4/ip_forward | grep -q 1 && echo "✅ IP forwarding enabled" || echo "❌ IP forwarding disabled"
ENDSSH

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "🌐 Your VPN Server is ready!"
echo "   Server IP: $VPS_IP"
echo "   VPN Port: 1194/udp"
echo "   Download Server: http://$VPS_IP:8081"
echo ""
echo "📝 Next Steps:"
echo "   1. Create a client:"
echo "      ssh $VPS_USER@$VPS_IP"
echo "      cd $VPN_DIR"
echo "      python3 vpn-manager.py add-client test-client"
echo ""
echo "   2. Download client config:"
echo "      http://$VPS_IP:8081/download?name=test-client"
echo ""
echo "   3. Launch GUI (if X11 forwarding enabled):"
echo "      ssh -X $VPS_USER@$VPS_IP"
echo "      cd $VPN_DIR && python3 vpn-gui.py"
echo ""

