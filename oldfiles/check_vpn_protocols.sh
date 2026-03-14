#!/bin/bash
#
# Check ALL THREE VPN Protocols + Email Service
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

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   VPN Protocols + Services Verification                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

ssh_run $VPS_USER@$VPS_IP "VPN_PORT=$VPN_PORT bash -s" << 'EOF'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. OPENVPN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if OpenVPN is installed
if command -v openvpn &> /dev/null; then
    echo "✅ OpenVPN: INSTALLED"
    openvpn --version | head -1
    
    # Check if OpenVPN service is running
    if systemctl is-active --quiet openvpn@server 2>/dev/null; then
        echo "✅ OpenVPN service: RUNNING"
    elif pgrep -x openvpn > /dev/null; then
        echo "✅ OpenVPN process: RUNNING (not systemd)"
        ps aux | grep "[o]penvpn" | head -1
    else
        echo "❌ OpenVPN: NOT RUNNING"
    fi
    
    # Check OpenVPN config
    if [ -f /etc/openvpn/server.conf ]; then
        echo "✅ OpenVPN config: EXISTS"
    else
        echo "⚠️  OpenVPN config: NOT FOUND"
    fi
    
    # Check OpenVPN port
    if netstat -tuln 2>/dev/null | grep -q ":1194"; then
        echo "✅ OpenVPN port 1194: LISTENING"
    else
        echo "⚠️  OpenVPN port 1194: NOT LISTENING"
    fi
else
    echo "❌ OpenVPN: NOT INSTALLED"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. WIREGUARD"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if WireGuard is installed
if command -v wg &> /dev/null; then
    echo "✅ WireGuard: INSTALLED"
    wg --version
    
    # Check if WireGuard interface exists
    if wg show 2>/dev/null | grep -q "interface"; then
        echo "✅ WireGuard interface: ACTIVE"
        wg show | head -5
    else
        echo "❌ WireGuard interface: NOT ACTIVE"
    fi
    
    # Check WireGuard config
    if [ -f /etc/wireguard/wg0.conf ]; then
        echo "✅ WireGuard config: EXISTS"
    else
        echo "⚠️  WireGuard config: NOT FOUND"
    fi
    
    # Check WireGuard port
    if netstat -tuln 2>/dev/null | grep -q ":51820"; then
        echo "✅ WireGuard port 51820: LISTENING"
    else
        echo "⚠️  WireGuard port 51820: NOT LISTENING"
    fi
else
    echo "❌ WireGuard: NOT INSTALLED"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. PHAZEVPN (Custom Protocol)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if PhazeVPN server binary exists
if [ -f /opt/phazevpn/phazevpn-server ]; then
    echo "✅ PhazeVPN binary: EXISTS"
    ls -lh /opt/phazevpn/phazevpn-server | awk '{print "   Size:", $5, "Modified:", $6, $7, $8}'
    
    # Check if PhazeVPN is running
    if pgrep -f "phazevpn-server" > /dev/null; then
        echo "✅ PhazeVPN process: RUNNING"
        ps aux | grep "[p]hazevpn-server" | head -1
    else
        echo "❌ PhazeVPN process: NOT RUNNING"
    fi
    
    # Check PhazeVPN port
    if netstat -tuln 2>/dev/null | grep -q ":$VPN_PORT"; then
        echo "✅ PhazeVPN port $VPN_PORT: LISTENING"
    else
        echo "⚠️  PhazeVPN port $VPN_PORT: NOT LISTENING"
    fi
else
    echo "❌ PhazeVPN binary: NOT FOUND"
    echo "   Expected at: /opt/phazevpn/phazevpn-server"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. EMAIL SERVICE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if email service is running
if pgrep -f "email.*app.py" > /dev/null; then
    echo "✅ Email service: RUNNING"
    ps aux | grep "[e]mail.*app.py" | head -1
    
    # Check email service port
    if netstat -tuln 2>/dev/null | grep -q ":5005"; then
        echo "✅ Email service port 5005: LISTENING"
    else
        echo "⚠️  Email service port 5005: NOT LISTENING"
    fi
else
    echo "❌ Email service: NOT RUNNING"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. OLD PROCESSES CLEANUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

OLD_PROCS=$(ps aux | grep "[p]ython3 app.py" | wc -l)
if [ "$OLD_PROCS" -gt 0 ]; then
    echo "⚠️  Found $OLD_PROCS old nohup processes - KILLING THEM NOW"
    pkill -f "python3 app.py"
    sleep 2
    
    # Verify they're gone
    OLD_PROCS_AFTER=$(ps aux | grep "[p]ython3 app.py" | wc -l)
    if [ "$OLD_PROCS_AFTER" -eq 0 ]; then
        echo "✅ Old processes killed successfully"
    else
        echo "⚠️  Still have $OLD_PROCS_AFTER old processes"
    fi
else
    echo "✅ No old nohup processes found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. PORT SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Listening ports:"
netstat -tuln 2>/dev/null | grep LISTEN | grep -E ":(1194|51820|$VPN_PORT|5000|5005|80|443)" | awk '{print "  ", $4}' | sort -u

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL=0
PASSED=0

echo ""
echo "VPN Protocols:"

# OpenVPN
if command -v openvpn &> /dev/null; then
    if pgrep -x openvpn > /dev/null || systemctl is-active --quiet openvpn@server 2>/dev/null; then
        echo "  ✅ OpenVPN: RUNNING"
        ((PASSED++))
    else
        echo "  ⚠️  OpenVPN: INSTALLED but NOT RUNNING"
    fi
else
    echo "  ❌ OpenVPN: NOT INSTALLED"
fi
((TOTAL++))

# WireGuard
if command -v wg &> /dev/null; then
    if wg show 2>/dev/null | grep -q "interface"; then
        echo "  ✅ WireGuard: RUNNING"
        ((PASSED++))
    else
        echo "  ⚠️  WireGuard: INSTALLED but NOT RUNNING"
    fi
else
    echo "  ❌ WireGuard: NOT INSTALLED"
fi
((TOTAL++))

# PhazeVPN
if [ -f /opt/phazevpn/phazevpn-server ]; then
    if pgrep -f "phazevpn-server" > /dev/null; then
        echo "  ✅ PhazeVPN: RUNNING"
        ((PASSED++))
    else
        echo "  ⚠️  PhazeVPN: EXISTS but NOT RUNNING"
    fi
else
    echo "  ❌ PhazeVPN: BINARY NOT FOUND"
fi
((TOTAL++))

echo ""
echo "Other Services:"

# Email
if pgrep -f "email.*app.py" > /dev/null; then
    echo "  ✅ Email service: RUNNING"
    ((PASSED++))
else
    echo "  ❌ Email service: NOT RUNNING"
fi
((TOTAL++))

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Score: $PASSED/$TOTAL services running"
echo ""

if [ "$PASSED" -eq "$TOTAL" ]; then
    echo "🎉 ALL SERVICES RUNNING!"
elif [ "$PASSED" -ge 2 ]; then
    echo "✅ SOME SERVICES RUNNING - Need to start missing ones"
else
    echo "⚠️  MOST SERVICES NOT RUNNING - Need immediate attention"
fi

echo ""

EOF

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Verification Complete                                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
