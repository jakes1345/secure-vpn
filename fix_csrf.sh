#!/bin/bash
#
# Fix CSRF Token Issue
#

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
SSH_OPTS="${SSH_OPTS:--o StrictHostKeyChecking=no -o ConnectTimeout=10}"

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

echo "🔧 Fixing CSRF token issue..."
echo ""

ssh_run $VPS_USER@$VPS_IP << 'EOF'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Setting Flask Secret Key"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Generate a proper secret key
SECRET_KEY=$(openssl rand -hex 32)

# Update systemd service with secret key
cat > /etc/systemd/system/phazevpn-web.service << EOFSERVICE
[Unit]
Description=PhazeVPN Web Portal (Gunicorn)
After=network.target mysql.service
Wants=network-online.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/phazevpn/web-portal
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="VPN_SERVER_IP=phazevpn.com"
Environment="VPN_SERVER_PORT=1194"
Environment="HTTPS_ENABLED=true"
Environment="FLASK_ENV=production"
Environment="FLASK_SECRET_KEY=$SECRET_KEY"
Environment="SECRET_KEY=$SECRET_KEY"
ExecStart=/usr/local/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 --timeout 120 --worker-class gevent --worker-connections 1000 --access-logfile /var/log/phazevpn-portal-access.log --error-logfile /var/log/phazevpn-portal-error.log app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/phazevpn /var/log

# Resource limits
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOFSERVICE

echo "✅ Secret key set: ${SECRET_KEY:0:16}..."

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Restarting Web Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

systemctl daemon-reload
systemctl restart phazevpn-web

sleep 3

if systemctl is-active --quiet phazevpn-web; then
    echo "✅ Web service restarted successfully"
    systemctl status phazevpn-web --no-pager -l | head -10
else
    echo "❌ Web service failed to restart"
    journalctl -u phazevpn-web -n 20 --no-pager
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Testing Website"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sleep 2

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ 2>/dev/null)
echo "Home page: HTTP $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Website responding correctly"
else
    echo "⚠️  Website returned HTTP $HTTP_CODE"
fi

EOF

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   CSRF Fix Complete                                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Try visiting https://phazevpn.com again"
