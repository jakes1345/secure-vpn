#!/bin/bash

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
echo "    PhazeVPN Universal Deployer"
echo "    Target: $VPS_IP"
echo "============================================"

echo "1. Preparing files..."
chmod +x phazevpn-protocol-go/scripts/*.sh 2>/dev/null

echo "2. Uploading Components to VPS..."

# Helper for SSH/SCP commands
echo "   - Create remote directories..."
ssh_run $VPS_USER@$VPS_IP "mkdir -p $REMOTE_DIR/web-portal $REMOTE_DIR/email-service"

# Upload Protocol Server (Go)
echo "   - Uploading VPN Server (Go)..."
scp_run -r phazevpn-protocol-go $VPS_USER@$VPS_IP:$REMOTE_DIR/

# Upload Web Portal (Flask)
echo "   - Uploading Web Portal..."
scp_run -r web-portal/* $VPS_USER@$VPS_IP:$REMOTE_DIR/web-portal/

# Upload Email Service (Flask/Postfix)
echo "   - Uploading Email Service..."
scp_run -r email-service-api/* $VPS_USER@$VPS_IP:$REMOTE_DIR/email-service/

# Upload VPN Client
echo "   - Uploading VPN Client..."
scp_run -r phazevpn-client $VPS_USER@$VPS_IP:$REMOTE_DIR/

echo "3. Executing Remote Setup..."
ssh_run $VPS_USER@$VPS_IP "VPN_PORT=$VPN_PORT bash -s" << 'EOF'
    echo "--- Connected to VPS ---"
    
    export DEBIAN_FRONTEND=noninteractive

    
    # 1. System Dependencies
    echo "Updating system..."
    apt update
    apt install -y golang-go python3-pip python3-venv postfix dovecot-imapd dovecot-pop3d ufw

    # 2. Build VPN Server
    echo "Building PhazeVPN Server..."
    cd /opt/phazevpn/phazevpn-protocol-go
    go mod tidy
    go build -buildvcs=false -o phazevpn-server .

    # 3. Setup Python Virtual Env for Web & Email
    echo "Setting up Python Environment..."
    cd /opt/phazevpn
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install flask flask-cors mysql-connector-python requests

    # 4. Configure Firewall
    echo "Configuring Firewall..."
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 5000/tcp  # Web Portal
    ufw allow 5005/tcp  # Email API
    ufw allow $VPN_PORT/udp # PhazeVPN
    ufw allow 51820/udp # WireGuard
    ufw allow 1194/udp  # OpenVPN
    ufw allow 25/tcp    # SMTP
    ufw allow 993/tcp   # IMAPS
    # Enable UFW if not already enabled (be careful not to lock out SSH)
    ufw allow ssh
    ufw --force enable

    # 5. Start Services (Simple background execution for demo - recommend Systemd for production)
    echo "Starting Services..."
    
    # Kill existing to restart
    pkill -f phazevpn-server
    pkill -f "python3 app.py"

    # Start VPN Server
    cd /opt/phazevpn/phazevpn-protocol-go
    nohup ./phazevpn-server -port $VPN_PORT > /var/log/phazevpn.log 2>&1 &
    
    # Setup Email Service Password (if not already set)
    if [ ! -f /opt/phazevpn/.env ] || ! grep -q "EMAIL_SERVICE_PASSWORD" /opt/phazevpn/.env; then
        echo "Setting up EMAIL_SERVICE_PASSWORD..."
        EMAIL_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
        cat > /opt/phazevpn/.env << ENVFILE
export EMAIL_SERVICE_PASSWORD='$EMAIL_PASS'
export EMAIL_SERVICE_URL='http://localhost:5005/api/v1/email'
export EMAIL_SERVICE_USER='noreply@mail.phazevpn.com'
export FROM_EMAIL='noreply@phazevpn.com'
ENVFILE
        echo "✅ EMAIL_SERVICE_PASSWORD generated and saved"
        echo "   Password: \$EMAIL_PASS (save this!)"
    fi
    
    # Start Web Portal
    cd /opt/phazevpn/web-portal
    source /opt/phazevpn/.env
    # Ensure database is configured (skipping complex DB setup for this script, assuming 'app.py' can run with defaults or sqlite fallback if implemented)
    nohup ../venv/bin/python3 app.py > /var/log/phazeweb.log 2>&1 &

    # Start Email Service
    cd /opt/phazevpn/email-service
    nohup ../venv/bin/python3 app.py > /var/log/phazeemail.log 2>&1 &

    echo "--- Setup Complete on VPS ---"
EOF

echo "============================================"
echo "✅ Deployment Finished!"
echo "Server is running at: $VPS_IP"
echo "Web Portal: http://$VPS_IP:5000"
echo "Email API: http://$VPS_IP:5005"
echo "VPN Port: ${VPN_PORT}/udp"
echo "============================================"
