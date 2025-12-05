#!/bin/bash

# Automated OVH VPS Setup Script for PhazeVPN
# This script does EVERYTHING automatically

set -e

VPS_IP="15.204.11.19"
VPS_USER="ubuntu"
VPS_PASS="QwX8MJJH3fSE"
LOCAL_DIR="/opt/phaze-vpn"
REMOTE_DIR="/opt/phaze-vpn"

echo "=========================================="
echo "🚀 Automated PhazeVPN VPS Setup"
echo "=========================================="
echo ""
echo "VPS: $VPS_USER@$VPS_IP"
echo ""

# Check if sshpass is available
if ! command -v sshpass &> /dev/null; then
    echo "⚠️  sshpass not found. Installing..."
    sudo apt-get install -y sshpass || {
        echo "❌ Failed to install sshpass. Please install manually:"
        echo "   sudo apt install sshpass"
        exit 1
    }
fi

# Function to run remote command
run_remote() {
    sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$VPS_USER@$VPS_IP" "$@"
}

# Function to copy file to remote
copy_to_remote() {
    sshpass -p "$VPS_PASS" scp -o StrictHostKeyChecking=no "$1" "$VPS_USER@$VPS_IP:$2"
}

# Function to copy directory to remote
copy_dir_to_remote() {
    sshpass -p "$VPS_PASS" scp -r -o StrictHostKeyChecking=no "$1" "$VPS_USER@$VPS_IP:$2"
}

echo "✅ Step 1/10: Testing connection..."
if ! run_remote "echo 'Connection test successful'"; then
    echo "❌ Failed to connect to VPS. Check credentials."
    exit 1
fi
echo ""

echo "✅ Step 2/10: Updating system packages..."
run_remote "sudo apt-get update -qq && sudo apt-get upgrade -y -qq"
echo ""

echo "✅ Step 3/10: Installing dependencies..."
run_remote "sudo apt-get install -y python3 python3-pip python3-tk openssl openvpn easy-rsa iptables ufw net-tools curl wget git build-essential debhelper devscripts 2>&1 | tail -3"
echo ""

echo "✅ Step 4/10: Creating PhazeVPN directory..."
run_remote "sudo mkdir -p $REMOTE_DIR/{config,certs,client-configs,logs,scripts,backups}"
run_remote "sudo chmod 755 $REMOTE_DIR"
echo ""

echo "✅ Step 5/10: Transferring PhazeVPN files..."
# Create a temporary directory for files
TMP_DIR=$(mktemp -d)
cd "$LOCAL_DIR"

# Copy essential files
cp vpn-manager.py vpn-gui.py client-download-server.py subscription-manager.py "$TMP_DIR/" 2>/dev/null || true
cp setup-routing.sh open-download-port.sh start-download-server-robust.sh "$TMP_DIR/" 2>/dev/null || true
cp generate-certs.sh "$TMP_DIR/" 2>/dev/null || true
mkdir -p "$TMP_DIR/config"
cp -r config/* "$TMP_DIR/config/" 2>/dev/null || true

# Copy service files
mkdir -p "$TMP_DIR/services"
cp debian/phaze-vpn.service "$TMP_DIR/services/" 2>/dev/null || true
cp debian/phaze-vpn-download.service "$TMP_DIR/services/" 2>/dev/null || true

# Create tarball
cd "$TMP_DIR"
tar -czf /tmp/phaze-vpn-files.tar.gz . 2>/dev/null || true

# Copy tarball to VPS
copy_to_remote "/tmp/phaze-vpn-files.tar.gz" "/tmp/phaze-vpn-files.tar.gz"

# Extract on VPS
run_remote "cd /tmp && mkdir -p phaze-extract && cd phaze-extract && tar -xzf ../phaze-vpn-files.tar.gz && sudo cp -r * $REMOTE_DIR/ 2>/dev/null || true && sudo cp -r config/* $REMOTE_DIR/config/ 2>/dev/null || true && sudo cp services/* /etc/systemd/system/ 2>/dev/null || true"

# Set permissions
run_remote "sudo chmod +x $REMOTE_DIR/*.sh $REMOTE_DIR/*.py 2>/dev/null || true"
run_remote "sudo chown -R root:root $REMOTE_DIR"

# Cleanup local temp
rm -rf "$TMP_DIR"
echo ""

echo "✅ Step 6/10: Installing systemd services..."
# Services should already be copied, but ensure they exist
run_remote "if [ ! -f /etc/systemd/system/phaze-vpn.service ]; then
    echo '[Unit]
Description=PhazeVPN Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$REMOTE_DIR
ExecStart=/usr/bin/python3 $REMOTE_DIR/vpn-manager.py start
ExecStop=/usr/bin/python3 $REMOTE_DIR/vpn-manager.py stop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target' | sudo tee /etc/systemd/system/phaze-vpn.service > /dev/null
fi"

run_remote "if [ ! -f /etc/systemd/system/phaze-vpn-download.service ]; then
    echo '[Unit]
Description=PhazeVPN Client Download Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$REMOTE_DIR
ExecStart=/usr/bin/python3 $REMOTE_DIR/client-download-server.py
Restart=always
RestartSec=5
StartLimitInterval=0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target' | sudo tee /etc/systemd/system/phaze-vpn-download.service > /dev/null
fi"

run_remote "sudo systemctl daemon-reload"
echo ""

echo "✅ Step 7/10: Configuring firewall..."
run_remote "sudo ufw --force enable || true"
run_remote "sudo ufw allow 22/tcp"
run_remote "sudo ufw allow 1194/udp"
run_remote "sudo ufw allow 8081/tcp"
echo ""

echo "✅ Step 8/10: Setting server IP and initializing VPN..."
run_remote "cd $REMOTE_DIR && sudo python3 vpn-manager.py set-server-ip $VPS_IP || true"
run_remote "cd $REMOTE_DIR && sudo python3 vpn-manager.py init || echo 'VPN already initialized'"
echo ""

echo "✅ Step 9/10: Setting up routing..."
run_remote "cd $REMOTE_DIR && sudo bash setup-routing.sh || echo 'Routing already configured'"
echo ""

echo "✅ Step 10/10: Starting services..."
run_remote "sudo systemctl enable phaze-vpn phaze-vpn-download"
run_remote "sudo systemctl start phaze-vpn phaze-vpn-download"
sleep 3
echo ""

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Service Status:"
run_remote "sudo systemctl status phaze-vpn --no-pager | head -5"
echo ""
run_remote "sudo systemctl status phaze-vpn-download --no-pager | head -5"
echo ""

echo "🌐 Download Server:"
echo "   http://$VPS_IP:8081"
echo ""

echo "📝 Next Steps:"
echo "   1. Create a test client:"
echo "      ssh $VPS_USER@$VPS_IP"
echo "      sudo python3 /opt/phaze-vpn/vpn-manager.py add-client test-client"
echo ""
echo "   2. Download config:"
echo "      http://$VPS_IP:8081/download?name=test-client"
echo ""

# Cleanup
rm -f /tmp/phaze-vpn-files.tar.gz
run_remote "rm -f /tmp/phaze-vpn-files.tar.gz"

echo "🎉 PhazeVPN is now running on your OVH VPS!"

