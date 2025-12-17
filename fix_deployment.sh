#!/bin/bash
#
# Fix PhazeVPN Deployment Issues
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

echo "🔧 Fixing PhazeVPN deployment issues..."
echo ""

ssh_run $VPS_USER@$VPS_IP << 'EOF'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Stopping old nohup processes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

pkill -f "python3 app.py" || echo "  No old python processes found"
pkill -f "gunicorn.*app:app" || echo "  No old gunicorn processes found"
sleep 2

echo "✅ Old processes stopped"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Checking systemd service configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "⚠️  Gunicorn not found, installing..."
    pip3 install gunicorn gevent
fi

# Check if www-data user exists
if ! id www-data &> /dev/null; then
    echo "⚠️  www-data user not found, creating..."
    useradd -r -s /bin/false www-data
fi

# Fix permissions
chown -R www-data:www-data /opt/phazevpn/web-portal
chmod -R 755 /opt/phazevpn/web-portal

echo "✅ Permissions fixed"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Starting phazevpn-web service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

systemctl daemon-reload
systemctl enable phazevpn-web
systemctl restart phazevpn-web

sleep 3

if systemctl is-active --quiet phazevpn-web; then
    echo "✅ phazevpn-web service: STARTED"
    systemctl status phazevpn-web --no-pager -l | head -10
else
    echo "❌ phazevpn-web service: FAILED TO START"
    echo "Checking logs..."
    journalctl -u phazevpn-web -n 20 --no-pager
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Starting fail2ban"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

systemctl enable fail2ban
systemctl restart fail2ban

if systemctl is-active --quiet fail2ban; then
    echo "✅ fail2ban: STARTED"
else
    echo "❌ fail2ban: FAILED TO START"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Creating backup script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > /opt/phazevpn/backup.sh << 'EOFBACKUP'
#!/bin/bash
BACKUP_DIR="/opt/phazevpn/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# Backup MySQL database
mysqldump -u phazevpn_user -p'SecureVPN2024!' phazevpn_db > "$BACKUP_DIR/db_$DATE.sql" 2>/dev/null || echo "MySQL backup failed"

# Backup configs
tar -czf "$BACKUP_DIR/configs_$DATE.tar.gz" /opt/phazevpn/web-portal/*.py /opt/phazevpn/web-portal/templates /opt/phazevpn/web-portal/static 2>/dev/null || echo "Config backup failed"

# Keep only last 7 days
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete 2>/dev/null
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>/dev/null

echo "Backup completed: $DATE"
EOFBACKUP

chmod +x /opt/phazevpn/backup.sh

# Add to crontab
(crontab -l 2>/dev/null | grep -v 'backup.sh'; echo '0 2 * * * /opt/phazevpn/backup.sh >> /var/log/phazevpn-backup.log 2>&1') | crontab -

echo "✅ Backup script created and scheduled"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. Final status check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL=0
PASSED=0

echo -n "phazevpn-web: "
if systemctl is-active --quiet phazevpn-web; then
    echo "✅ RUNNING"
    ((PASSED++))
else
    echo "❌ NOT RUNNING"
fi
((TOTAL++))

echo -n "nginx: "
if systemctl is-active --quiet nginx; then
    echo "✅ RUNNING"
    ((PASSED++))
else
    echo "❌ NOT RUNNING"
fi
((TOTAL++))

echo -n "fail2ban: "
if systemctl is-active --quiet fail2ban; then
    echo "✅ RUNNING"
    ((PASSED++))
else
    echo "❌ NOT RUNNING"
fi
((TOTAL++))

echo -n "redis: "
if systemctl is-active --quiet redis-server; then
    echo "✅ RUNNING"
    ((PASSED++))
else
    echo "❌ NOT RUNNING"
fi
((TOTAL++))

echo ""
echo "Status: $PASSED/$TOTAL services running"
echo ""

if [ "$PASSED" -eq "$TOTAL" ]; then
    echo "🎉 ALL SERVICES RUNNING!"
    echo ""
    echo "✅ Visit: https://phazevpn.com"
else
    echo "⚠️  Some services need attention"
fi

EOF

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Fix Complete                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
