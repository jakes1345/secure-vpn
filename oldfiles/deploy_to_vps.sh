#!/bin/bash

# VPS Configuration
set -euo pipefail

VPS_ENV_FILE="${VPS_ENV_FILE:-.vps.env}"
if [ -f "$VPS_ENV_FILE" ]; then
    set -a
    source "$VPS_ENV_FILE"
    set +a
fi

VPS_HOST="${VPS_HOST:-phazevpn.com}"
VPS_IP="${VPS_IP:-$VPS_HOST}"
VPS_USER="${VPS_USER:-root}"
REMOTE_DIR="${REMOTE_DIR:-/opt/phazevpn}"
SSH_OPTS="${SSH_OPTS:--o StrictHostKeyChecking=no -o ConnectTimeout=10}"
VPN_PORT="${VPN_PORT:-51821}"

require_sshpass_if_needed() {
    if [ -n "${VPS_PASS:-}" ] && ! command -v sshpass &> /dev/null; then
        echo "❌ VPS_PASS is set but sshpass is not installed."
        echo "Install sshpass or use SSH keys (recommended)."
        exit 1
    fi
}

ssh_run() {
    if [ -n "${VPS_PASS:-}" ]; then
        require_sshpass_if_needed
        SSHPASS="$VPS_PASS" sshpass -e ssh $SSH_OPTS "$@"
    else
        ssh $SSH_OPTS "$@"
    fi
}

scp_run() {
    if [ -n "${VPS_PASS:-}" ]; then
        require_sshpass_if_needed
        SSHPASS="$VPS_PASS" sshpass -e scp $SSH_OPTS "$@"
    else
        scp $SSH_OPTS "$@"
    fi
}

echo "============================================"
echo "    PhazeVPN Deployer"
echo "    Target: $VPS_IP"
echo "============================================"

echo "1. Preparing files..."
# Ensure permissions are correct locally
chmod +x phazevpn-protocol-go/scripts/*.sh 2>/dev/null

echo "2. Uploading Server Code to VPS..."
echo "   (This uploads the FIXED server code with real crypto)"
scp_run -r phazevpn-protocol-go $VPS_USER@$VPS_IP:$REMOTE_DIR

echo "3. Uploading Web Portal Updates..."
scp_run web-portal/app.py $VPS_USER@$VPS_IP:$REMOTE_DIR/web-portal/
scp_run web-portal/generate_all_protocols.py $VPS_USER@$VPS_IP:$REMOTE_DIR/web-portal/

echo "4. Running Setup on VPS..."
ssh_run $VPS_USER@$VPS_IP "VPN_PORT=$VPN_PORT bash -s" << 'EOF'
    echo "--- Connected to VPS ---"
    
    # 1. Install Go if missing
    if ! command -v go &> /dev/null; then
        echo "Installing Go..."
        apt update && apt install -y golang-go
    fi

    # 2. Build Server
    echo "Building PhazeVPN Server..."
    cd /opt/phazevpn/phazevpn-protocol-go
    go mod tidy
    go build -buildvcs=false -o phazevpn-server .

    # 3. Setup Firewall
    echo "Configuring Firewall..."
    ufw allow $VPN_PORT/udp
    ufw allow 51820/udp
    ufw allow 1194/udp

    # 4. Restart Services (assuming systemd service exists, otherwise start manually)
    if systemctl list-units --full -all | grep -Fq "phazevpn-server.service"; then
        systemctl restart phazevpn-server
        echo "Server service restarted."
    else
        echo "Server service not found. You may need to run it manually:"
        echo "cd /opt/phazevpn/phazevpn-protocol-go && ./phazevpn-server"
    fi

    echo "--- Setup Complete ---"
EOF

echo "============================================"
echo "✅ Deployment Finished!"
echo "You can now connect using the Python Client locally."
echo "============================================"
