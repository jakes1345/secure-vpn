#!/bin/bash

# Quick VPS Fixes - Resolve immediate issues
# This script fixes the bcrypt issue and debugs service crashes

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

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         PhazeVPN VPS Quick Fix                             ║"
echo "║         Fixing: bcrypt, VPN crashes, Shadowsocks           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "🔧 Applying fixes to VPS..."
echo ""

ssh_run $VPS_USER@$VPS_IP << 'FIXES'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Installing Missing Python Packages"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd /opt/phazevpn
source venv/bin/activate

echo "Installing bcrypt..."
pip install bcrypt

echo "Installing other potentially missing packages..."
pip install flask flask-cors mysql-connector-python requests bcrypt werkzeug

echo "✅ Python packages installed"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Checking VPN Server Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

systemctl status phazevpn-go.service --no-pager -l | head -20

echo ""
echo "Checking VPN server logs..."
journalctl -u phazevpn-go.service -n 50 --no-pager

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Checking Shadowsocks Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

systemctl status shadowsocks-phazevpn.service --no-pager -l | head -20

echo ""
echo "Checking Shadowsocks logs..."
journalctl -u shadowsocks-phazevpn.service -n 50 --no-pager

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  Restarting Web Portal"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if there's a systemd service for web portal
if systemctl list-units --type=service | grep -q "phazevpn-web"; then
    echo "Restarting phazevpn-web service..."
    systemctl restart phazevpn-web
    systemctl status phazevpn-web --no-pager -l | head -10
else
    echo "No systemd service found, checking nohup processes..."
    if pgrep -f "app.py.*web-portal" > /dev/null; then
        echo "Killing old web portal process..."
        pkill -f "app.py.*web-portal"
    fi
    
    echo "Starting web portal..."
    cd /opt/phazevpn/web-portal
    source /opt/phazevpn/venv/bin/activate
    nohup python3 app.py > /var/log/phazeweb.log 2>&1 &
    
    sleep 2
    
    if pgrep -f "app.py.*web-portal" > /dev/null; then
        echo "✅ Web portal started"
    else
        echo "❌ Web portal failed to start"
        echo "Last 20 lines of log:"
        tail -20 /var/log/phazeweb.log
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  Testing Web Portal"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sleep 2

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>&1)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✅ Web Portal responding (HTTP $HTTP_CODE)"
else
    echo "❌ Web Portal not responding (HTTP $HTTP_CODE)"
    echo "Checking logs..."
    tail -30 /var/log/phazeweb.log
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Service Status:"
systemctl is-active phazevpn-go.service && echo "  ✅ VPN Server: Running" || echo "  ❌ VPN Server: Not Running"
systemctl is-active shadowsocks-phazevpn.service && echo "  ✅ Shadowsocks: Running" || echo "  ⚠️  Shadowsocks: Not Running"
systemctl is-active phazevpn-email-api.service && echo "  ✅ Email API: Running" || echo "  ❌ Email API: Not Running"
pgrep -f "app.py.*web-portal" > /dev/null && echo "  ✅ Web Portal: Running" || echo "  ❌ Web Portal: Not Running"

echo ""
echo "Next Steps:"
echo "  1. If VPN server still crashing, check: journalctl -u phazevpn-go.service -f"
echo "  2. If Shadowsocks still crashing, check: journalctl -u shadowsocks-phazevpn.service -f"
echo "  3. Test web portal: http://phazevpn.com"
echo ""

FIXES

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  Fixes Applied                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 What was fixed:"
echo "   ✅ Installed bcrypt and missing Python packages"
echo "   ✅ Restarted web portal"
echo "   📊 Checked VPN server and Shadowsocks logs"
echo ""
echo "🔍 To monitor services:"
echo "   ssh root@phazevpn.com"
echo "   journalctl -u phazevpn-go.service -f"
echo ""
