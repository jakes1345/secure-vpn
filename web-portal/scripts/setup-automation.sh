#!/bin/bash
# Setup Automation Script
# Installs all automation scripts and cron jobs
# Run once: sudo bash /opt/phaze-vpn/web-portal/scripts/setup-automation.sh

set -e

SCRIPT_DIR="/opt/phaze-vpn/web-portal/scripts"
VPN_DIR="/opt/phaze-vpn"

echo "=========================================="
echo "Setting Up PhazeVPN Automation"
echo "=========================================="
echo ""

# Create scripts directory
mkdir -p "$SCRIPT_DIR"
chmod 755 "$SCRIPT_DIR"

# Make scripts executable
chmod +x "$SCRIPT_DIR"/*.sh

# Create log directory
mkdir -p "$VPN_DIR/logs"
chmod 755 "$VPN_DIR/logs"

# Create backup directory
mkdir -p "$VPN_DIR/backups"
chmod 755 "$VPN_DIR/backups"

# Create data directory
mkdir -p "$VPN_DIR/web-portal/data"
chmod 755 "$VPN_DIR/web-portal/data"

# Set up cron jobs
echo "Setting up cron jobs..."

# Backup existing crontab
crontab -l > /tmp/crontab.backup 2>/dev/null || true

# Add new cron jobs
(crontab -l 2>/dev/null || true; cat << 'CRON_JOBS'
# PhazeVPN Daily Backup (2 AM)
0 2 * * * /opt/phaze-vpn/web-portal/scripts/daily-backup.sh >> /opt/phaze-vpn/logs/backup.log 2>&1

# PhazeVPN Daily Cleanup (3 AM)
0 3 * * * /opt/phaze-vpn/web-portal/scripts/daily-cleanup.sh >> /opt/phaze-vpn/logs/cleanup.log 2>&1

# PhazeVPN Health Check (Every Hour)
0 * * * * /opt/phaze-vpn/web-portal/scripts/health-check.sh >> /opt/phaze-vpn/logs/health-check.log 2>&1
CRON_JOBS
) | crontab -

echo "✅ Cron jobs installed"
echo ""
echo "Current cron jobs:"
crontab -l | grep phazevpn || echo "  (none found)"

# Set up logrotate
echo ""
echo "Setting up log rotation..."

cat > /etc/logrotate.d/phazevpn << 'LOGROTATE'
/opt/phaze-vpn/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
    sharedscripts
    postrotate
        systemctl reload phazevpn-portal.service > /dev/null 2>&1 || true
    endscript
}

/var/log/phazevpn-portal-*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
}
LOGROTATE

echo "✅ Log rotation configured"

# Verify certbot auto-renewal
echo ""
echo "Verifying SSL certificate auto-renewal..."
if systemctl is-enabled certbot.timer > /dev/null 2>&1; then
    echo "✅ Certbot timer is enabled"
else
    echo "⚠️  Certbot timer not enabled - enabling now..."
    systemctl enable certbot.timer
    systemctl start certbot.timer
fi

echo ""
echo "=========================================="
echo "✅ Automation Setup Complete!"
echo "=========================================="
echo ""
echo "Installed:"
echo "  ✅ Daily backup script (runs at 2 AM)"
echo "  ✅ Daily cleanup script (runs at 3 AM)"
echo "  ✅ Health check script (runs hourly)"
echo "  ✅ Log rotation (daily, keeps 30 days)"
echo "  ✅ SSL certificate auto-renewal"
echo ""
echo "To verify:"
echo "  crontab -l"
echo "  systemctl status certbot.timer"
echo "  ls -la /opt/phaze-vpn/web-portal/scripts/"
echo ""

exit 0

