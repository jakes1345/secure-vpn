#!/bin/bash

# Final Automated Setup with New Password
# This script completes the full PhazeVPN setup

VPS_IP="15.204.11.19"
VPS_USER="ubuntu"
NEW_PASS="eRkkDQTUsjt2"
LOCAL_DIR="/opt/phaze-vpn"
REMOTE_DIR="/opt/phaze-vpn"

echo "=========================================="
echo "🚀 Automated PhazeVPN VPS Setup"
echo "=========================================="
echo ""
echo "VPS: $VPS_USER@$VPS_IP"
echo ""

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    sudo apt-get install -y sshpass 2>/dev/null || {
        echo "Please install sshpass: sudo apt install sshpass"
        exit 1
    }
fi

# Function to run remote command with sudo
run_sudo() {
    sshpass -p "$NEW_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$VPS_USER@$VPS_IP" "echo '$NEW_PASS' | sudo -S $1"
}

# Function to run remote command without sudo
run_remote() {
    sshpass -p "$NEW_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$VPS_USER@$VPS_IP" "$1"
}

# Function to copy file
copy_file() {
    sshpass -p "$NEW_PASS" scp -o StrictHostKeyChecking=no "$1" "$VPS_USER@$VPS_IP:$2"
}

echo "✅ Step 1/10: Testing connection..."
if ! run_remote "echo 'Connection test successful'"; then
    echo "❌ Failed to connect. Check password."
    exit 1
fi
echo "✅ Connected!\n"

echo "✅ Step 2/10: Updating system packages..."
run_sudo "apt-get update -qq"
run_sudo "apt-get upgrade -y -qq"
echo "✅ System updated\n"

echo "✅ Step 3/10: Installing dependencies..."
deps="python3 python3-pip python3-tk openssl openvpn easy-rsa iptables ufw net-tools curl wget git build-essential debhelper devscripts"
run_sudo "apt-get install -y $deps"
echo "✅ Dependencies installed\n"

echo "✅ Step 4/10: Creating PhazeVPN directory..."
run_sudo "mkdir -p $REMOTE_DIR/{config,certs,client-configs,logs,scripts,backups}"
run_sudo "chmod 755 $REMOTE_DIR"
echo "✅ Directory created\n"

echo "✅ Step 5/10: Transferring PhazeVPN files..."
cd "$LOCAL_DIR"

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
copy_file "/tmp/phaze-vpn-setup.tar.gz" "/tmp/phaze-vpn-setup.tar.gz"

# Extract on remote
run_sudo "cd /tmp && tar -xzf phaze-vpn-setup.tar.gz && cp -r * $REMOTE_DIR/ 2>/dev/null || true && cp -r config/* $REMOTE_DIR/config/ 2>/dev/null || true && cp phaze-vpn.service phaze-vpn-download.service /etc/systemd/system/ 2>/dev/null || true"
run_sudo "chmod +x $REMOTE_DIR/*.sh $REMOTE_DIR/*.py 2>/dev/null || true"
run_sudo "chown -R root:root $REMOTE_DIR"

rm -f /tmp/phaze-vpn-setup.tar.gz
echo "✅ Files transferred\n"

echo "✅ Step 6/10: Installing systemd services..."
# Ensure services exist with correct content
phaze_vpn_service="[Unit]
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
WantedBy=multi-user.target"

phaze_download_service="[Unit]
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
WantedBy=multi-user.target"

echo "$phaze_vpn_service" | run_sudo "tee /etc/systemd/system/phaze-vpn.service > /dev/null"
echo "$phaze_download_service" | run_sudo "tee /etc/systemd/system/phaze-vpn-download.service > /dev/null"
run_sudo "systemctl daemon-reload"
echo "✅ Services installed\n"

echo "✅ Step 7/10: Configuring firewall..."
run_sudo "ufw --force enable"
run_sudo "ufw allow 22/tcp"
run_sudo "ufw allow 1194/udp"
run_sudo "ufw allow 8081/tcp"
echo "✅ Firewall configured\n"

echo "✅ Step 8/10: Setting server IP and initializing VPN..."
run_sudo "cd $REMOTE_DIR && python3 vpn-manager.py set-server-ip $VPS_IP"
run_sudo "cd $REMOTE_DIR && python3 vpn-manager.py init"
echo "✅ VPN initialized\n"

echo "✅ Step 9/10: Setting up routing..."
run_sudo "cd $REMOTE_DIR && bash setup-routing.sh"
echo "✅ Routing configured\n"

echo "✅ Step 10/10: Starting services..."
run_sudo "systemctl enable phaze-vpn phaze-vpn-download"
run_sudo "systemctl start phaze-vpn phaze-vpn-download"
sleep 3
echo "✅ Services started\n"

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Checking service status..."
status1=$(run_remote "systemctl is-active phaze-vpn")
status2=$(run_remote "systemctl is-active phaze-vpn-download")
echo "   VPN Server: $status1"
echo "   Download Server: $status2"
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
echo "🎉 PhazeVPN is now running on your OVH VPS!"


