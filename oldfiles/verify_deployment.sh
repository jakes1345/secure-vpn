#!/bin/bash
#
# Verify PhazeVPN Production Deployment (with sshpass)
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
SSH_OPTS="${SSH_OPTS:--o StrictHostKeyChecking=accept-new -o ConnectTimeout=10}"

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

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   PhazeVPN Deployment Verification                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "🔍 Checking deployment status on VPS..."
echo ""

ssh_run $VPS_USER@$VPS_IP << 'EOF'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. SYSTEMD SERVICES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check phazevpn-web service
if systemctl is-active --quiet phazevpn-web; then
    echo "✅ phazevpn-web.service: RUNNING"
    systemctl status phazevpn-web --no-pager -l | grep -E "(Active|Main PID|Memory)" | head -3
else
    echo "❌ phazevpn-web.service: NOT RUNNING"
    echo "   Checking why..."
    systemctl status phazevpn-web --no-pager -l | head -15
fi

echo ""

# Check if VPN server exists
if [ -f /opt/phazevpn/phazevpn-server ]; then
    if systemctl is-active --quiet phazevpn-server; then
        echo "✅ phazevpn-server.service: RUNNING"
    else
        echo "⚠️  phazevpn-server.service: EXISTS but not running"
    fi
else
    echo "ℹ️  phazevpn-server: Binary not found (expected)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. NGINX"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx: RUNNING"
    
    # Test Nginx config
    if nginx -t 2>&1 | grep -q "successful"; then
        echo "✅ Nginx config: VALID"
    else
        echo "❌ Nginx config: INVALID"
        nginx -t 2>&1 | tail -5
    fi
    
    # Check if our config is enabled
    if [ -L /etc/nginx/sites-enabled/phazevpn ]; then
        echo "✅ PhazeVPN site: ENABLED"
    else
        echo "❌ PhazeVPN site: NOT ENABLED"
    fi
else
    echo "❌ Nginx: NOT RUNNING"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. FAIL2BAN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if systemctl is-active --quiet fail2ban; then
    echo "✅ fail2ban: RUNNING"
    
    # Check jails
    if fail2ban-client status 2>/dev/null | grep -q "phazevpn-auth"; then
        echo "✅ phazevpn-auth jail: ACTIVE"
    else
        echo "⚠️  phazevpn-auth jail: NOT ACTIVE (may need restart)"
    fi
else
    echo "❌ fail2ban: NOT RUNNING"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. REDIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if systemctl is-active --quiet redis-server; then
    echo "✅ Redis: RUNNING"
    
    # Test Redis connection
    if redis-cli ping 2>/dev/null | grep -q "PONG"; then
        echo "✅ Redis connection: OK"
    else
        echo "⚠️  Redis connection: FAILED"
    fi
else
    echo "❌ Redis: NOT RUNNING"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. BACKUPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f /opt/phazevpn/backup.sh ]; then
    echo "✅ Backup script: EXISTS"
    
    # Check crontab
    if crontab -l 2>/dev/null | grep -q "backup.sh"; then
        echo "✅ Backup cron job: CONFIGURED"
        crontab -l | grep backup.sh
    else
        echo "❌ Backup cron job: NOT CONFIGURED"
    fi
else
    echo "❌ Backup script: NOT FOUND"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. SSL CERTIFICATES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f /etc/letsencrypt/live/phazevpn.com/fullchain.pem ]; then
    echo "✅ SSL certificate: EXISTS"
    
    # Check expiry
    EXPIRY=$(openssl x509 -enddate -noout -in /etc/letsencrypt/live/phazevpn.com/fullchain.pem | cut -d= -f2)
    echo "   Expires: $EXPIRY"
else
    echo "❌ SSL certificate: NOT FOUND"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. WEB APPLICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if app is responding
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" =~ ^(200|301|302)$ ]]; then
    echo "✅ Web app: RESPONDING on port 5000 (HTTP $HTTP_CODE)"
else
    echo "⚠️  Web app: NOT RESPONDING on port 5000 (HTTP $HTTP_CODE)"
fi

# Check gunicorn processes
GUNICORN_COUNT=$(ps aux | grep -c "[g]unicorn.*app:app" || echo "0")
if [ "$GUNICORN_COUNT" -gt 0 ]; then
    echo "✅ Gunicorn workers: $GUNICORN_COUNT running"
else
    echo "❌ Gunicorn workers: NONE running"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8. RECENT LOGS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Last 10 lines from phazevpn-web:"
journalctl -u phazevpn-web -n 10 --no-pager 2>/dev/null || echo "  (no logs yet)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL=0
PASSED=0

# Count checks
systemctl is-active --quiet phazevpn-web && ((PASSED++)); ((TOTAL++))
systemctl is-active --quiet nginx && ((PASSED++)); ((TOTAL++))
systemctl is-active --quiet fail2ban && ((PASSED++)); ((TOTAL++))
systemctl is-active --quiet redis-server && ((PASSED++)); ((TOTAL++))
[ -f /opt/phazevpn/backup.sh ] && ((PASSED++)); ((TOTAL++))
[ -f /etc/letsencrypt/live/phazevpn.com/fullchain.pem ] && ((PASSED++)); ((TOTAL++))

echo ""
echo "Status: $PASSED/$TOTAL checks passed"
echo ""

if [ "$PASSED" -eq "$TOTAL" ]; then
    echo "🎉 DEPLOYMENT SUCCESSFUL! All systems operational!"
    echo ""
    echo "✅ Visit: https://phazevpn.com"
elif [ "$PASSED" -ge 4 ]; then
    echo "✅ MOSTLY SUCCESSFUL! Core systems running, some optional components need attention"
    echo ""
    echo "✅ Visit: https://phazevpn.com"
else
    echo "⚠️  Some critical components need attention (see above)"
fi

echo ""

EOF

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Verification Complete                                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
