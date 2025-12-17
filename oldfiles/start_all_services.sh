#!/bin/bash
#
# Start ALL Missing Services (WireGuard, PhazeVPN, Email)
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

echo "🚀 Starting all missing VPN protocols and services..."
echo ""

ssh_run $VPS_USER@$VPS_IP "VPN_PORT=$VPN_PORT bash -s" << 'EOF'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Starting WireGuard"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f /etc/wireguard/wg0.conf ]; then
    echo "Starting WireGuard interface wg0..."
    wg-quick up wg0 2>&1 || echo "  (May already be up or have issues)"
    
    sleep 2
    
    if wg show 2>/dev/null | grep -q "interface"; then
        echo "✅ WireGuard: STARTED"
        wg show | head -5
    else
        echo "⚠️  WireGuard: Failed to start or already running"
    fi
else
    echo "❌ WireGuard config not found at /etc/wireguard/wg0.conf"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Building and Starting PhazeVPN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if Go source exists
if [ -d /opt/phazevpn/phazevpn-protocol-go ]; then
    echo "Found PhazeVPN source, building..."
    cd /opt/phazevpn/phazevpn-protocol-go
    
    # Build the server
    if go build -buildvcs=false -o /opt/phazevpn/phazevpn-server . 2>&1; then
        echo "✅ PhazeVPN: BUILT"
        ls -lh /opt/phazevpn/phazevpn-server
        
        # Start it
        echo "Starting PhazeVPN server..."
        nohup /opt/phazevpn/phazevpn-server -port $VPN_PORT > /var/log/phazevpn.log 2>&1 &
        sleep 2
        
        if pgrep -f "phazevpn-server" > /dev/null; then
            echo "✅ PhazeVPN: STARTED"
            ps aux | grep "[p]hazevpn-server" | head -1
        else
            echo "❌ PhazeVPN: Failed to start"
            echo "Check logs: tail -20 /var/log/phazevpn.log"
        fi
    else
        echo "❌ PhazeVPN: Build failed"
    fi
else
    echo "❌ PhazeVPN source not found at /opt/phazevpn/phazevpn-protocol-go"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Starting Email Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f /opt/phazevpn/email-service/app.py ]; then
    echo "Starting email service..."
    cd /opt/phazevpn/email-service
    nohup python3 app.py > /var/log/phazeemail.log 2>&1 &
    sleep 2
    
    if pgrep -f "email.*app.py" > /dev/null; then
        echo "✅ Email service: STARTED"
        ps aux | grep "[e]mail.*app.py" | head -1
    else
        echo "❌ Email service: Failed to start"
        echo "Check logs: tail -20 /var/log/phazeemail.log"
    fi
else
    echo "❌ Email service not found at /opt/phazevpn/email-service/app.py"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Final Status Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL=0
RUNNING=0

echo ""
echo "VPN Protocols:"

# OpenVPN
if pgrep -x openvpn > /dev/null || systemctl is-active --quiet openvpn@server 2>/dev/null; then
    echo "  ✅ OpenVPN: RUNNING"
    ((RUNNING++))
else
    echo "  ❌ OpenVPN: NOT RUNNING"
fi
((TOTAL++))

# WireGuard
if wg show 2>/dev/null | grep -q "interface"; then
    echo "  ✅ WireGuard: RUNNING"
    ((RUNNING++))
else
    echo "  ❌ WireGuard: NOT RUNNING"
fi
((TOTAL++))

# PhazeVPN
if pgrep -f "phazevpn-server" > /dev/null; then
    echo "  ✅ PhazeVPN: RUNNING"
    ((RUNNING++))
else
    echo "  ❌ PhazeVPN: NOT RUNNING"
fi
((TOTAL++))

echo ""
echo "Other Services:"

# Email
if pgrep -f "email.*app.py" > /dev/null; then
    echo "  ✅ Email service: RUNNING"
    ((RUNNING++))
else
    echo "  ❌ Email service: NOT RUNNING"
fi
((TOTAL++))

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Score: $RUNNING/$TOTAL services running"
echo ""

if [ "$RUNNING" -eq "$TOTAL" ]; then
    echo "🎉 ALL SERVICES RUNNING!"
elif [ "$RUNNING" -ge 3 ]; then
    echo "✅ MOST SERVICES RUNNING!"
else
    echo "⚠️  Some services still not running"
fi

echo ""
echo "Listening ports:"
netstat -tuln 2>/dev/null | grep LISTEN | grep -E ":(1194|51820|51821|5000|5005|80|443)" | awk '{print "  ", $4}' | sort -u

EOF

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Service Startup Complete                                ║"
echo "╚════════════════════════════════════════════════════════════╝"
