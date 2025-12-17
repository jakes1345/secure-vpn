#!/bin/bash

# PhazeVPN Complete Deployment - Fixed Version
# Builds VPN server locally, then deploys everything

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

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         PhazeVPN Complete Deployment (Fixed)               ║"
echo "║         Target: $VPS_IP                                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Building VPN Server Locally"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd phazevpn-protocol-go

# Check Go version
GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
echo "Local Go version: $GO_VERSION"

# Build the server
echo "Building phazevpn-server..."
if go build -buildvcs=false -o phazevpn-server .; then
    echo "✅ VPN server built successfully"
    ls -lh phazevpn-server
else
    echo "❌ Failed to build VPN server"
    echo ""
    echo "Trying alternative build method..."
    # Try building from cmd/server if it exists
    if [ -d "cmd/server" ]; then
        cd cmd/server
        go build -o ../../phazevpn-server .
        cd ../..
    else
        echo "⚠️  Build failed. Will deploy source code and let VPS try to build."
    fi
fi

cd ..

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Uploading Components to VPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create remote directories
echo "Creating remote directories..."
ssh_run $VPS_USER@$VPS_IP "mkdir -p $REMOTE_DIR/{web-portal,email-service,phazevpn-protocol-go}"

# Upload VPN Server
echo "Uploading VPN Server..."
scp_run -r phazevpn-protocol-go/* $VPS_USER@$VPS_IP:$REMOTE_DIR/phazevpn-protocol-go/

# Upload Web Portal
echo "Uploading Web Portal..."
scp_run -r web-portal/* $VPS_USER@$VPS_IP:$REMOTE_DIR/web-portal/

# Upload Email Service
echo "Uploading Email Service..."
if [ -d "email-service-api" ]; then
    scp_run -r email-service-api/* $VPS_USER@$VPS_IP:$REMOTE_DIR/email-service/
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Setting Up Services on VPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ssh_run $VPS_USER@$VPS_IP "VPN_PORT=$VPN_PORT bash -s" << 'SETUP'

echo "Setting up Python environment..."
cd /opt/phazevpn

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate and install packages
source venv/bin/activate
pip install --upgrade pip
pip install flask flask-cors mysql-connector-python requests bcrypt werkzeug

echo "✅ Python packages installed"
echo ""

echo "Configuring firewall..."
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5000/tcp  # Web Portal
ufw allow 5005/tcp  # Email API
ufw allow 51821/udp # PhazeVPN
ufw allow 51820/udp # WireGuard
ufw allow 1194/udp  # OpenVPN
ufw allow 25/tcp    # SMTP
ufw allow 993/tcp   # IMAPS
ufw allow ssh
ufw --force enable

echo "✅ Firewall configured"
echo ""

echo "Stopping old services..."
pkill -f phazevpn-server
pkill -f "python3 app.py"

echo ""
echo "Starting services..."

# Start VPN Server (if binary exists)
cd /opt/phazevpn/phazevpn-protocol-go
if [ -f "phazevpn-server" ]; then
    chmod +x phazevpn-server
    nohup ./phazevpn-server -port $VPN_PORT > /var/log/phazevpn.log 2>&1 &
    echo "✅ VPN server started"
else
    echo "⚠️  VPN server binary not found, skipping"
fi

# Start Web Portal
cd /opt/phazevpn/web-portal
if [ -f "app.py" ]; then
    source /opt/phazevpn/venv/bin/activate
    nohup python3 app.py > /var/log/phazeweb.log 2>&1 &
    echo "✅ Web portal started"
else
    echo "⚠️  Web portal app.py not found"
fi

# Start Email Service
cd /opt/phazevpn/email-service
if [ -f "app.py" ]; then
    source /opt/phazevpn/venv/bin/activate
    nohup python3 app.py > /var/log/phazeemail.log 2>&1 &
    echo "✅ Email service started"
else
    echo "⚠️  Email service app.py not found"
fi

echo ""
echo "Waiting for services to start..."
sleep 3

echo ""
echo "Service Status:"
pgrep -f phazevpn-server > /dev/null && echo "  ✅ VPN Server: Running" || echo "  ❌ VPN Server: Not Running"
pgrep -f "app.py.*web-portal" > /dev/null && echo "  ✅ Web Portal: Running" || echo "  ❌ Web Portal: Not Running"
pgrep -f "app.py.*email" > /dev/null && echo "  ✅ Email Service: Running" || echo "  ❌ Email Service: Not Running"

echo ""
echo "Testing web portal..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>&1)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "  ✅ Web Portal responding (HTTP $HTTP_CODE)"
else
    echo "  ⚠️  Web Portal not responding (HTTP $HTTP_CODE)"
fi

SETUP

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  Deployment Complete!                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Service URLs:"
echo "   🌐 Web Portal:  http://phazevpn.com:5000"
echo "   📧 Email API:   http://phazevpn.com:5005"
echo "   🔐 VPN Server:  phazevpn.com:51821 (UDP)"
echo ""
echo "📝 Next Steps:"
echo "   1. Test web portal: http://phazevpn.com"
echo "   2. Check logs: ssh root@phazevpn.com 'tail -f /var/log/phazeweb.log'"
echo "   3. Run diagnostics: ./check_vps_status.sh"
echo ""
