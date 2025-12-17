#!/bin/bash
#
# Sync ALL Latest Files to VPS (Templates, Static, Python)
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

scp_run() {
    if [ -n "${VPS_PASS:-}" ]; then
        require_sshpass_if_needed
        SSHPASS="$VPS_PASS" sshpass -e scp $SSH_OPTS "$@"
    else
        scp $SSH_OPTS "$@"
    fi
}

rsync_run() {
    if [ -n "${VPS_PASS:-}" ]; then
        require_sshpass_if_needed
        SSHPASS="$VPS_PASS" sshpass -e rsync -e "ssh $SSH_OPTS" "$@"
    else
        rsync -e "ssh $SSH_OPTS" "$@"
    fi
}

echo "🔄 Syncing ALL latest files to VPS..."
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Uploading Templates"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Upload all templates
rsync_run -avz --progress web-portal/templates/ $VPS_USER@$VPS_IP:/opt/phazevpn/web-portal/templates/

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Uploading Static Files (CSS, JS, Images)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Upload static files
rsync_run -avz --progress web-portal/static/ $VPS_USER@$VPS_IP:/opt/phazevpn/web-portal/static/

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Uploading Python Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Upload Python files
scp_run web-portal/*.py $VPS_USER@$VPS_IP:/opt/phazevpn/web-portal/

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Fixing Permissions"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ssh_run $VPS_USER@$VPS_IP << 'EOF'
chown -R www-data:www-data /opt/phazevpn/web-portal
chmod -R 755 /opt/phazevpn/web-portal
echo "✅ Permissions fixed"
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Clearing Browser Cache (Nginx)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ssh_run $VPS_USER@$VPS_IP << 'EOF'
# Clear Nginx cache if it exists
if [ -d /var/cache/nginx ]; then
    rm -rf /var/cache/nginx/*
    echo "✅ Nginx cache cleared"
fi

# Reload Nginx
systemctl reload nginx
echo "✅ Nginx reloaded"
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. Restarting Web Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ssh_run $VPS_USER@$VPS_IP << 'EOF'
systemctl restart phazevpn-web
sleep 3

if systemctl is-active --quiet phazevpn-web; then
    echo "✅ Web service restarted"
else
    echo "❌ Web service failed"
    journalctl -u phazevpn-web -n 10 --no-pager
fi
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ssh_run $VPS_USER@$VPS_IP << 'EOF'
echo "Latest template files:"
ls -lht /opt/phazevpn/web-portal/templates/*.html | head -5

echo ""
echo "Latest CSS files:"
ls -lht /opt/phazevpn/web-portal/static/css/*.css | head -3

echo ""
echo "Latest JS files:"
ls -lht /opt/phazevpn/web-portal/static/js/*.js | head -3
EOF

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   ✅ ALL FILES SYNCED!                                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Visit https://phazevpn.com and do a HARD REFRESH:"
echo "   - Chrome/Firefox: Ctrl+Shift+R"
echo "   - Or clear browser cache"
echo ""
echo "All latest files are now on the VPS!"
