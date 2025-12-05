#!/bin/bash
# Daily Cleanup Script for PhazeVPN
# Cleans old data, expired tokens, old backups
# Run daily via cron: 0 3 * * * /opt/phaze-vpn/web-portal/scripts/daily-cleanup.sh

set -e

VPN_DIR="/opt/phaze-vpn"
LOG_FILE="$VPN_DIR/logs/cleanup.log"

echo "[$(date)] Starting daily cleanup..." >> "$LOG_FILE"

# Clean old rate limit entries (older than 30 days)
if [ -f "$VPN_DIR/web-portal/data/rate_limits.json" ]; then
    python3 << 'PYTHON_EOF'
import json
import time
from pathlib import Path

rate_limit_file = Path('/opt/phaze-vpn/web-portal/data/rate_limits.json')
if rate_limit_file.exists():
    with open(rate_limit_file, 'r') as f:
        data = json.load(f)
    
    now = time.time()
    cleaned = {}
    for ip, timestamps in data.items():
        # Keep only entries from last 30 days
        recent = [ts for ts in timestamps if now - float(ts) < (30 * 24 * 3600)]
        if recent:
            cleaned[ip] = recent
    
    with open(rate_limit_file, 'w') as f:
        json.dump(cleaned, f, indent=2)
    
    print(f"Cleaned rate limits: {len(data)} IPs -> {len(cleaned)} IPs")
PYTHON_EOF
fi

# Clean old log files (older than 30 days)
find "$VPN_DIR/logs" -name "*.log" -mtime +30 -delete 2>/dev/null || true

# Clean old backup files (older than 30 days - backup script handles this, but double-check)
find "$VPN_DIR/backups" -name "phazevpn-backup-*.tar.gz" -mtime +30 -delete 2>/dev/null || true

# Clean temporary files
find "$VPN_DIR" -name "*.tmp" -mtime +1 -delete 2>/dev/null || true
find "$VPN_DIR" -name "*.backup.*" -mtime +7 -delete 2>/dev/null || true

# Clean old connection history (keep last 1000 entries)
if [ -f "$VPN_DIR/logs/connection-history.json" ]; then
    python3 << 'PYTHON_EOF'
import json
from pathlib import Path

history_file = Path('/opt/phaze-vpn/logs/connection-history.json')
if history_file.exists():
    with open(history_file, 'r') as f:
        history = json.load(f)
    
    # Keep only last 1000 entries
    if len(history) > 1000:
        history = history[-1000:]
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        print(f"Cleaned connection history: kept last 1000 entries")
PYTHON_EOF
fi

echo "[$(date)] Cleanup complete" >> "$LOG_FILE"

exit 0

