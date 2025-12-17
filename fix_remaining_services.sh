#!/bin/bash
#
# Fix WireGuard and Email Service
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

echo "🔧 Fixing WireGuard and Email Service..."
echo ""

ssh_run $VPS_USER@$VPS_IP "VPN_PORT=$VPN_PORT bash -s" << 'EOF'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Fixing WireGuard"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if wg0 interface exists
if ip link show wg0 &>/dev/null; then
    echo "WireGuard interface wg0 already exists, checking status..."
    
    if wg show wg0 &>/dev/null; then
        echo "✅ WireGuard: ALREADY RUNNING"
        wg show wg0 | head -5
    else
        echo "Interface exists but not configured, restarting..."
        wg-quick down wg0 2>&1 || true
        sleep 1
        wg-quick up wg0 2>&1
    fi
else
    echo "Creating WireGuard interface..."
    wg-quick up wg0 2>&1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Fixing Email Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check what's wrong with email service
if [ -f /var/log/phazeemail.log ]; then
    echo "Email service logs:"
    tail -10 /var/log/phazeemail.log
fi

echo ""
echo "Checking if email service is actually running..."
if pgrep -f "email.*app.py" > /dev/null; then
    echo "✅ Email service: ALREADY RUNNING"
    ps aux | grep "[e]mail.*app.py"
elif [ -f /opt/phazevpn/email-service/app.py ]; then
    echo "Starting email service with proper environment..."
    cd /opt/phazevpn/email-service
    
    # Source environment if exists
    if [ -f /opt/phazevpn/.env ]; then
        source /opt/phazevpn/.env
    fi
    
    # Start email service
    nohup python3 app.py > /var/log/phazeemail.log 2>&1 &
    sleep 3
    
    if pgrep -f "email.*app.py" > /dev/null; then
        echo "✅ Email service: STARTED"
    else
        echo "❌ Email service: Still failed, checking logs..."
        tail -20 /var/log/phazeemail.log
    fi
else
    echo "❌ Email service app.py not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Final Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL=4
RUNNING=0

echo ""
echo "All Services:"

# OpenVPN
if pgrep -x openvpn > /dev/null || systemctl is-active --quiet openvpn@server 2>/dev/null; then
    echo "  ✅ OpenVPN (port 1194)"
    ((RUNNING++))
else
    echo "  ❌ OpenVPN"
fi

# WireGuard
if wg show wg0 &>/dev/null; then
    echo "  ✅ WireGuard (port 51820)"
    ((RUNNING++))
else
    echo "  ❌ WireGuard"
fi

# PhazeVPN
if pgrep -f "phazevpn-server" > /dev/null; then
    echo "  ✅ PhazeVPN (port $VPN_PORT)"
    ((RUNNING++))
else
    echo "  ❌ PhazeVPN"
fi

# Email
if pgrep -f "email.*app.py" > /dev/null; then
    echo "  ✅ Email Service (port 5005)"
    ((RUNNING++))
else
    echo "  ❌ Email Service"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Score: $RUNNING/$TOTAL services running"
echo ""

if [ "$RUNNING" -eq "$TOTAL" ]; then
    echo "🎉 ALL 4 SERVICES RUNNING!"
    echo ""
    echo "VPN Protocols:"
    echo "  ✅ OpenVPN (1194/udp)"
    echo "  ✅ WireGuard (51820/udp)"
    echo "  ✅ PhazeVPN (51821/udp)"
    echo ""
    echo "Other Services:"
    echo "  ✅ Email Service (5005/tcp)"
elif [ "$RUNNING" -eq 3 ]; then
    echo "✅ 3/4 SERVICES RUNNING - Almost there!"
else
    echo "⚠️  Only $RUNNING/4 services running"
fi

echo ""
echo "Active ports:"
netstat -tuln 2>/dev/null | grep LISTEN | grep -E ":(1194|51820|$VPN_PORT|5000|5005)" | awk '{print "  ", $4}' | sort -u

EOF

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Fix Complete                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
