#!/bin/bash
# Health Check Script for PhazeVPN
# Checks services, disk space, memory, and sends alerts
# Run hourly via cron: 0 * * * * /opt/phaze-vpn/web-portal/scripts/health-check.sh

set -e

VPN_DIR="/opt/phaze-vpn"
LOG_FILE="$VPN_DIR/logs/health-check.log"
ALERT_EMAIL="${ALERT_EMAIL:-admin@phazevpn.com}"  # Set via environment variable

check_service() {
    local service=$1
    if systemctl is-active --quiet "$service"; then
        echo "✅ $service: RUNNING"
        return 0
    else
        echo "❌ $service: NOT RUNNING"
        return 1
    fi
}

check_disk_space() {
    local usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$usage" -gt 90 ]; then
        echo "⚠️  Disk usage: ${usage}% (CRITICAL)"
        return 1
    elif [ "$usage" -gt 80 ]; then
        echo "⚠️  Disk usage: ${usage}% (WARNING)"
        return 1
    else
        echo "✅ Disk usage: ${usage}%"
        return 0
    fi
}

check_memory() {
    local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$usage" -gt 90 ]; then
        echo "⚠️  Memory usage: ${usage}% (CRITICAL)"
        return 1
    elif [ "$usage" -gt 80 ]; then
        echo "⚠️  Memory usage: ${usage}% (WARNING)"
        return 1
    else
        echo "✅ Memory usage: ${usage}%"
        return 0
    fi
}

check_web_portal() {
    if curl -s -f http://127.0.0.1:5000/ > /dev/null 2>&1; then
        echo "✅ Web portal: RESPONDING"
        return 0
    else
        echo "❌ Web portal: NOT RESPONDING"
        return 1
    fi
}

# Run checks
echo "[$(date)] Health Check Starting..." >> "$LOG_FILE"

ISSUES=0

# Check services
if ! check_service phazevpn-portal.service >> "$LOG_FILE" 2>&1; then
    ISSUES=$((ISSUES + 1))
fi

if ! check_service phaze-vpn.service >> "$LOG_FILE" 2>&1; then
    ISSUES=$((ISSUES + 1))
fi

if ! check_service nginx.service >> "$LOG_FILE" 2>&1; then
    ISSUES=$((ISSUES + 1))
fi

# Check resources
if ! check_disk_space >> "$LOG_FILE" 2>&1; then
    ISSUES=$((ISSUES + 1))
fi

if ! check_memory >> "$LOG_FILE" 2>&1; then
    ISSUES=$((ISSUES + 1))
fi

# Check web portal
if ! check_web_portal >> "$LOG_FILE" 2>&1; then
    ISSUES=$((ISSUES + 1))
fi

# Send alert if issues found
if [ "$ISSUES" -gt 0 ]; then
    echo "[$(date)] ⚠️  Found $ISSUES issues - check $LOG_FILE" >> "$LOG_FILE"
    # Optional: Send email alert
    # echo "PhazeVPN Health Check found $ISSUES issues. Check logs: $LOG_FILE" | mail -s "PhazeVPN Health Alert" "$ALERT_EMAIL"
else
    echo "[$(date)] ✅ All checks passed" >> "$LOG_FILE"
fi

exit 0

