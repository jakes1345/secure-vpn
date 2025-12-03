#!/bin/bash
# VPN Disconnect Security Script
# Restores system when VPN disconnects
# Ensures no leaks occur during disconnection

set -e

VPN_DEVICE="$1"
LOG_FILE="/opt/secure-vpn/logs/security.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "=== VPN Disconnect - Security Cleanup ==="

# Stop monitoring
if [ -f /tmp/vpn-monitor.pid ]; then
    MONITOR_PID=$(cat /tmp/vpn-monitor.pid)
    kill "$MONITOR_PID" 2>/dev/null || true
    rm -f /tmp/vpn-monitor.pid
    log "Stopped connection monitoring"
fi

# Restore DNS
if [ -f /etc/resolv.conf.backup ]; then
    cp /etc/resolv.conf.backup /etc/resolv.conf 2>/dev/null || true
    rm -f /etc/resolv.conf.backup
    log "DNS restored"
fi

# Clean up iptables rules (be careful - don't break system)
# Note: In production, use iptables-save/restore or use rule comments
# For now, we'll leave rules (they won't affect disconnected state)

# Re-enable IPv6 (optional - user may want it disabled)
# sysctl -w net.ipv6.conf.all.disable_ipv6=0 2>/dev/null || true

log "=== VPN Disconnect Complete ==="

exit 0

