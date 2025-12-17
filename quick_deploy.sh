#!/bin/bash

# Quick Deploy - No System Updates
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

echo "🚀 Quick Deploy (No Updates)"

# Upload files
echo "Uploading..."
scp_run -r phazevpn-protocol-go $VPS_USER@$VPS_IP:$REMOTE_DIR/
scp_run -r web-portal/* $VPS_USER@$VPS_IP:$REMOTE_DIR/web-portal/
scp_run -r email-service-api/* $VPS_USER@$VPS_IP:$REMOTE_DIR/email-service/

# Build and restart
echo "Building on VPS..."
ssh_run $VPS_USER@$VPS_IP "VPN_PORT=$VPN_PORT bash -s" << 'EOF'
    cd /opt/phazevpn/phazevpn-protocol-go
    go build -buildvcs=false -o phazevpn-server .
    
    # Restart services
    pkill -f phazevpn-server
    pkill -f "python3 app.py"
    
    # Start VPN Server
    nohup ./phazevpn-server -port $VPN_PORT > /var/log/phazevpn.log 2>&1 &
    
    # Start Web Portal
    cd /opt/phazevpn/web-portal
    nohup ../venv/bin/python3 app.py > /var/log/phazeweb.log 2>&1 &
    
    # Start Email Service
    cd /opt/phazevpn/email-service
    nohup ../venv/bin/python3 app.py > /var/log/phazeemail.log 2>&1 &
    
    echo "✅ Services restarted"
EOF

echo "✅ Deployment Complete!"
