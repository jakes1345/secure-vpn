#!/bin/bash
# Quick VPS Security Check - No special tools required

VPS="15.204.11.19"
DOMAIN="phazevpn.com"
PASS="<VPS_PASSWORD_REMOVED>"

echo "=========================================="
echo "🔒 PhazeVPN VPS Quick Security Check"
echo "=========================================="
echo ""

# 1. Check what's running on VPS
echo "=== SERVICES ON VPS ==="
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@$VPS << 'EOFVPS'
echo "📊 Running Services:"
systemctl list-units --type=service --state=running | grep -E "(phazevpn|nginx|mysql|apache|email|postfix|dovecot)" || echo "No PhazeVPN services found"

echo ""
echo "🔌 Open Ports:"
ss -tlnp | grep LISTEN | awk '{print $4, $NF}' | column -t

echo ""
echo "🔥 Firewall Status:"
ufw status verbose 2>/dev/null || iptables -L -n | head -20

echo ""
echo "👤 Recent Login Attempts:"
lastlog | head -10

echo ""
echo "🚨 Failed SSH Attempts (last 24h):"
grep "Failed password" /var/log/auth.log 2>/dev/null | tail -5 || echo "No recent failures"

echo ""
echo "💾 Disk Usage:"
df -h / | tail -1

echo ""
echo "🧠 Memory Usage:"
free -h | grep Mem

echo ""
echo "🌐 Active Network Connections:"
ss -tn | grep ESTAB | wc -l
echo "active connections"
EOFVPS

echo ""
echo "=== WEBSITE CHECKS ==="
echo "Testing https://$DOMAIN..."

# Check if site is up
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN" 2>/dev/null)
echo "Homepage status: $HTTP_CODE"

# Check security headers
echo ""
echo "Security Headers:"
curl -sI "https://$DOMAIN" 2>/dev/null | grep -E "(X-Frame|X-Content|Strict-Transport|Content-Security)" || echo "⚠️  Missing security headers"

# Check for exposed files
echo ""
echo "Checking for exposed files..."
for path in "/.git/config" "/.env" "/config.php" "/phpinfo.php" "/.htaccess"; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN$path" 2>/dev/null)
    if [ "$CODE" = "200" ]; then
        echo "⚠️  EXPOSED: $path (HTTP $CODE)"
    fi
done

# Check API endpoints
echo ""
echo "API Endpoint Status:"
curl -s -o /dev/null -w "GET /api/users: %{http_code}\n" "https://$DOMAIN/api/users" 2>/dev/null
curl -s -o /dev/null -w "GET /api/vpn: %{http_code}\n" "https://$DOMAIN/api/vpn" 2>/dev/null
curl -s -o /dev/null -w "GET /api/admin: %{http_code}\n" "https://$DOMAIN/api/admin" 2>/dev/null

echo ""
echo "=== DNS CHECKS ==="
echo "Domain: $DOMAIN"
dig $DOMAIN +short | head -1
echo ""
echo "MX Records:"
dig MX $DOMAIN +short
echo ""
echo "SPF/DMARC:"
dig TXT $DOMAIN +short | grep -i "spf\|dmarc" || echo "⚠️  No SPF/DMARC found"

echo ""
echo "=== VPN SERVICE CHECK ==="
echo "Testing VPN ports..."
timeout 2 bash -c "echo > /dev/tcp/$VPS/1194" 2>/dev/null && echo "✅ OpenVPN (1194) responding" || echo "⚠️  OpenVPN (1194) not responding"
timeout 2 bash -c "echo > /dev/tcp/$VPS/51820" 2>/dev/null && echo "✅ WireGuard (51820) responding" || echo "⚠️  WireGuard (51820) not responding"

echo ""
echo "=== EMAIL SERVICE CHECK ==="
timeout 2 bash -c "echo > /dev/tcp/$VPS/25" 2>/dev/null && echo "✅ SMTP (25) responding" || echo "⚠️  SMTP (25) not responding"
timeout 2 bash -c "echo > /dev/tcp/$VPS/587" 2>/dev/null && echo "✅ Submission (587) responding" || echo "⚠️  Submission (587) not responding"
timeout 2 bash -c "echo > /dev/tcp/$VPS/465" 2>/dev/null && echo "✅ SMTPS (465) responding" || echo "⚠️  SMTPS (465) not responding"

echo ""
echo "=========================================="
echo "✅ Quick Security Check Complete"
echo "=========================================="
echo ""
echo "📋 SUMMARY OF FINDINGS:"
echo "  Check the output above for:"
echo "  - ⚠️  warnings (need attention)"
echo "  - ✅ confirmations (working correctly)"
echo ""
echo "🔐 SECURITY RECOMMENDATIONS:"
echo "  1. Enable firewall if not active"
echo "  2. Add security headers to web server"
echo "  3. Ensure no sensitive files are exposed"
echo "  4. Review failed login attempts"
echo "  5. Keep all services updated"
echo ""
