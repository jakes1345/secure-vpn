#!/bin/bash
# Daily Backup Script for PhazeVPN
# Backs up all critical data files
# Keeps 30 days of backups
# Run daily via cron: 0 2 * * * /opt/phaze-vpn/web-portal/scripts/daily-backup.sh

set -e

BACKUP_DIR="/opt/phaze-vpn/backups"
VPN_DIR="/opt/phaze-vpn"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/phazevpn-backup-$DATE.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting daily backup..."

# Create backup
tar -czf "$BACKUP_FILE" \
    "$VPN_DIR/users.json" \
    "$VPN_DIR/logs/tickets.json" \
    "$VPN_DIR/logs/payment-requests.json" \
    "$VPN_DIR/logs/connection-history.json" \
    "$VPN_DIR/web-portal/data/rate_limits.json" \
    "$VPN_DIR/client-configs/" \
    "$VPN_DIR/config/" \
    2>/dev/null || true

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "phazevpn-backup-*.tar.gz" -mtime +30 -delete

echo "[$(date)] Backup complete: $BACKUP_FILE"
echo "[$(date)] Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Optional: Upload to remote storage
# scp "$BACKUP_FILE" user@backup-server:/backups/phazevpn/

exit 0

