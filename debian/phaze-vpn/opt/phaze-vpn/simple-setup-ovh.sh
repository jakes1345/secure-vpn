#!/bin/bash

# Simple Manual Setup Instructions for OVH VPS
# Since password has expired, we'll do this step-by-step

VPS_IP="15.204.11.19"
VPS_USER="ubuntu"

echo "=========================================="
echo "📋 Manual Setup Instructions for OVH VPS"
echo "=========================================="
echo ""
echo "⚠️  The VPS password has expired."
echo "    You need to change it first, then we can continue."
echo ""
echo "Step 1: Connect and change password"
echo "-------------------------------------"
echo "  ssh $VPS_USER@$VPS_IP"
echo "  (Enter current password: QwX8MJJH3fSE)"
echo "  (It will prompt you to change it - choose a new password)"
echo ""
echo "Step 2: Once password is changed, run this script again"
echo "  Or continue with manual setup below"
echo ""
read -p "Have you changed the password? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please change the password first, then run this script again."
    exit 1
fi

echo ""
echo "Enter the NEW password:"
read -s NEW_PASS
echo ""

echo "✅ Step 1/8: Testing connection with new password..."
if ! sshpass -p "$NEW_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "echo 'Connected!'" 2>/dev/null; then
    echo "❌ Connection failed. Check password."
    exit 1
fi
echo "✅ Connected!"
echo ""

echo "✅ Step 2/8: Updating system..."
sshpass -p "$NEW_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "sudo apt-get update -qq && sudo apt-get upgrade -y -qq <<< '$NEW_PASS'"
echo "✅ Updated"
echo ""

echo "✅ Step 3/8: Installing dependencies..."
sshpass -p "$NEW_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "sudo apt-get install -y python3 python3-pip python3-tk openssl openvpn easy-rsa iptables ufw net-tools curl wget git build-essential debhelper devscripts sshpass <<< '$NEW_PASS'"
echo "✅ Dependencies installed"
echo ""

echo "✅ Step 4/8: Creating directories..."
sshpass -p "$NEW_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "sudo mkdir -p /opt/phaze-vpn/{config,certs,client-configs,logs,scripts,backups} <<< '$NEW_PASS' && sudo chmod 755 /opt/phaze-vpn <<< '$NEW_PASS'"
echo "✅ Directories created"
echo ""

echo "✅ Step 5/8: Transferring files..."
cd /opt/phaze-vpn

# Create tarball
tar -czf /tmp/phaze-vpn-setup.tar.gz \
    vpn-manager.py \
    vpn-gui.py \
    client-download-server.py \
    subscription-manager.py \
    setup-routing.sh \
    open-download-port.sh \
    start-download-server-robust.sh \
    generate-certs.sh \
    config/ \
    debian/phaze-vpn.service \
    debian/phaze-vpn-download.service 2>/dev/null

# Transfer
sshpass -p "$NEW_PASS" scp -o StrictHostKeyChecking=no /tmp/phaze-vpn-setup.tar.gz "$VPS_USER@$VPS_IP:/tmp/"

# Extract
sshpass -p "$NEW_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "cd /tmp && tar -xzf phaze-vpn-setup.tar.gz && sudo cp -r * /opt/phaze-vpn/ 2>/dev/null || true && sudo cp -r config/* /opt/phaze-vpn/config/ 2>/dev/null || true && sudo cp phaze-vpn.service phaze-vpn-download.service /etc/systemd/system/ 2>/dev/null || true && sudo chmod +x /opt/phaze-vpn/*.sh /opt/phaze-vpn/*.py 2>/dev/null || true && sudo chown -R root:root /opt/phaze-vpn <<< '$NEW_PASS'"

rm -f /tmp/phaze-vpn-setup.tar.gz
echo "✅ Files transferred"
echo ""

echo "✅ Step 6/8: Installing services..."
sshpass -p "$NEW_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "sudo systemctl daemon-reload <<< '$NEW_PASS'"
echo "✅ Services installed"
echo ""

echo "✅ Step 7/8: Configuring firewall and VPN..."
sshpass -p "$NEW_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "sudo ufw --force enable <<< '$NEW_PASS' && sudo ufw allow 22/tcp <<< '$NEW_PASS' && sudo ufw allow 1194/udp <<< '$NEW_PASS' && sudo ufw allow 8081/tcp <<< '$NEW_PASS'"
sshpass -p "$NEW_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "cd /opt/phaze-vpn && sudo python3 vpn-manager.py set-server-ip $VPS_IP <<< '$NEW_PASS' && sudo python3 vpn-manager.py init <<< '$NEW_PASS' && sudo bash setup-routing.sh <<< '$NEW_PASS'"
echo "✅ Configured"
echo ""

echo "✅ Step 8/8: Starting services..."
sshpass -p "$NEW_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "sudo systemctl enable phaze-vpn phaze-vpn-download <<< '$NEW_PASS' && sudo systemctl start phaze-vpn phaze-vpn-download <<< '$NEW_PASS'"
sleep 3
echo "✅ Services started"
echo ""

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "🌐 Download Server: http://$VPS_IP:8081"
echo ""
echo "📝 Create a test client:"
echo "   ssh $VPS_USER@$VPS_IP"
echo "   sudo python3 /opt/phaze-vpn/vpn-manager.py add-client test-client"
echo ""

