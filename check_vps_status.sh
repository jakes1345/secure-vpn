#!/bin/bash

# PhazeVPN VPS Status Checker
# This script checks what's actually running on the VPS

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
echo "║         PhazeVPN VPS Diagnostic Report                     ║"
echo "║         Target: $VPS_IP                                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "🔍 Connecting to VPS..."
echo ""

# Run comprehensive diagnostic
ssh_run $VPS_USER@$VPS_IP << 'DIAGNOSTIC'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  SYSTEM INFORMATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Hostname: $(hostname)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Kernel: $(uname -r)"
echo "Uptime: $(uptime -p)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  RUNNING PROCESSES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check VPN Server
if pgrep -f "phazevpn-server" > /dev/null; then
    echo "✅ VPN Server: RUNNING"
    ps aux | grep phazevpn-server | grep -v grep | awk '{print "   PID:", $2, "| CPU:", $3"%", "| MEM:", $4"%", "| CMD:", $11, $12, $13}'
else
    echo "❌ VPN Server: NOT RUNNING"
fi

# Check Web Portal
if pgrep -f "app.py.*web-portal" > /dev/null; then
    echo "✅ Web Portal: RUNNING"
    ps aux | grep "app.py" | grep web-portal | grep -v grep | awk '{print "   PID:", $2, "| CPU:", $3"%", "| MEM:", $4"%"}'
else
    echo "❌ Web Portal: NOT RUNNING"
fi

# Check Email Service
if pgrep -f "app.py.*email" > /dev/null; then
    echo "✅ Email Service: RUNNING"
    ps aux | grep "app.py" | grep email | grep -v grep | awk '{print "   PID:", $2, "| CPU:", $3"%", "| MEM:", $4"%"}'
else
    echo "❌ Email Service: NOT RUNNING"
fi

# Check MySQL
if pgrep -f "mysqld" > /dev/null; then
    echo "✅ MySQL: RUNNING"
else
    echo "❌ MySQL: NOT RUNNING"
fi

# Check Nginx
if pgrep -f "nginx" > /dev/null; then
    echo "✅ Nginx: RUNNING"
else
    echo "⚠️  Nginx: NOT RUNNING (not critical, but recommended)"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  NETWORK & PORTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check listening ports
echo "Listening Ports:"
if command -v ss &> /dev/null; then
    ss -tlnp | grep -E ":(80|443|5000|5005|51820|51821|3306)" | awk '{print "   ", $0}'
else
    netstat -tlnp | grep -E ":(80|443|5000|5005|51820|51821|3306)" | awk '{print "   ", $0}'
fi

echo ""
echo "Firewall Status:"
if command -v ufw &> /dev/null; then
    ufw status | head -20
else
    echo "   UFW not installed"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  INSTALLED FILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "/opt/phazevpn" ]; then
    echo "✅ /opt/phazevpn exists"
    ls -lh /opt/phazevpn/ | awk '{print "   ", $0}'
    
    echo ""
    echo "VPN Server Binary:"
    if [ -f "/opt/phazevpn/phazevpn-protocol-go/phazevpn-server" ]; then
        echo "   ✅ Found: $(ls -lh /opt/phazevpn/phazevpn-protocol-go/phazevpn-server | awk '{print $9, "("$5")"}')"
    else
        echo "   ❌ NOT FOUND"
    fi
    
    echo ""
    echo "Web Portal:"
    if [ -f "/opt/phazevpn/web-portal/app.py" ]; then
        echo "   ✅ Found: app.py"
        echo "   Files: $(ls /opt/phazevpn/web-portal/ | wc -l) files"
    else
        echo "   ❌ NOT FOUND"
    fi
    
    echo ""
    echo "Email Service:"
    if [ -f "/opt/phazevpn/email-service/app.py" ]; then
        echo "   ✅ Found: app.py"
    else
        echo "   ❌ NOT FOUND"
    fi
else
    echo "❌ /opt/phazevpn does NOT exist!"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  SERVICE LOGS (Last 10 lines)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "VPN Server Log:"
if [ -f "/var/log/phazevpn.log" ]; then
    tail -10 /var/log/phazevpn.log | sed 's/^/   /'
else
    echo "   ❌ Log file not found"
fi

echo ""
echo "Web Portal Log:"
if [ -f "/var/log/phazeweb.log" ]; then
    tail -10 /var/log/phazeweb.log | sed 's/^/   /'
else
    echo "   ❌ Log file not found"
fi

echo ""
echo "Email Service Log:"
if [ -f "/var/log/phazeemail.log" ]; then
    tail -10 /var/log/phazeemail.log | sed 's/^/   /'
else
    echo "   ❌ Log file not found"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  WEB PORTAL TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Testing http://localhost:5000..."
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>&1)
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
        echo "   ✅ Web Portal responding (HTTP $HTTP_CODE)"
    else
        echo "   ❌ Web Portal not responding (HTTP $HTTP_CODE)"
    fi
else
    echo "   ⚠️  curl not installed, cannot test"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  DISK & MEMORY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Disk Usage:"
df -h / | tail -1 | awk '{print "   Root: "$3" used / "$2" total ("$5" used)"}'

echo ""
echo "Memory Usage:"
free -h | grep Mem | awk '{print "   RAM: "$3" used / "$2" total"}'

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8️⃣  SYSTEMD SERVICES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if systemctl list-units --type=service | grep -q phazevpn; then
    echo "✅ Found PhazeVPN systemd services:"
    systemctl list-units --type=service | grep phazevpn | sed 's/^/   /'
else
    echo "⚠️  No PhazeVPN systemd services found (using nohup instead)"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9️⃣  SUMMARY & RECOMMENDATIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Count issues
ISSUES=0

if ! pgrep -f "phazevpn-server" > /dev/null; then
    echo "❌ VPN Server not running"
    ((ISSUES++))
fi

if ! pgrep -f "app.py.*web-portal" > /dev/null; then
    echo "❌ Web Portal not running"
    ((ISSUES++))
fi

if ! pgrep -f "mysqld" > /dev/null; then
    echo "⚠️  MySQL not running (may be needed for web portal)"
    ((ISSUES++))
fi

if ! pgrep -f "nginx" > /dev/null; then
    echo "⚠️  Nginx not running (recommended for production)"
fi

if ! systemctl list-units --type=service | grep -q phazevpn; then
    echo "⚠️  No systemd services (using nohup - not production-ready)"
fi

echo ""
if [ $ISSUES -eq 0 ]; then
    echo "✅ All critical services appear to be running!"
    echo "   Next steps: Setup Nginx + SSL for production"
else
    echo "⚠️  Found $ISSUES critical issue(s)"
    echo "   Recommended: Run deploy_all_to_vps.sh to fix"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DIAGNOSTIC

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  Diagnostic Complete                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 Next Steps:"
echo "   1. Review the report above"
echo "   2. If services are down, run: ./deploy_all_to_vps.sh"
echo "   3. For production setup, see: DEPLOYMENT_STRATEGY.md"
echo ""
