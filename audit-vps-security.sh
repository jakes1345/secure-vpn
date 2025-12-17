#!/bin/bash
# Comprehensive Security Audit of PhazeVPN VPS Infrastructure
# Tests: VPN, Website, Email, and all services

VPS="15.204.11.19"
DOMAIN="phazevpn.com"

echo "=========================================="
echo "🔒 PhazeVPN VPS Security Audit"
echo "=========================================="
echo "Target: $VPS ($DOMAIN)"
echo "Started: $(date)"
echo ""

# 1. Port Scan
echo "=== 1. PORT SCAN ==="
echo "Scanning open ports..."
nmap -sV -p- $VPS -oN vps-portscan.txt
echo ""

# 2. SSL/TLS Check
echo "=== 2. SSL/TLS SECURITY ==="
echo "Checking HTTPS configuration..."
sslscan $DOMAIN 2>/dev/null || echo "sslscan not installed, skipping"
testssl.sh --quiet $DOMAIN 2>/dev/null || echo "testssl.sh not installed, skipping"
echo ""

# 3. Web Application Security
echo "=== 3. WEB APPLICATION TESTS ==="
echo "Testing web portal..."

# Check for common vulnerabilities
echo "- Testing for SQL injection..."
sqlmap -u "https://$DOMAIN/login" --batch --risk=1 --level=1 2>/dev/null || echo "sqlmap not installed"

echo "- Testing for XSS..."
curl -s "https://$DOMAIN/?test=<script>alert(1)</script>" | grep -i "script" && echo "⚠️  Possible XSS" || echo "✅ No obvious XSS"

echo "- Checking security headers..."
curl -sI "https://$DOMAIN" | grep -E "(X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security|Content-Security-Policy)"

echo ""

# 4. VPN Server Security
echo "=== 4. VPN SERVER TESTS ==="
echo "Checking VPN service..."
nc -zv $VPS 1194 2>&1 | grep -q "succeeded" && echo "✅ VPN port 1194 open" || echo "⚠️  VPN port 1194 closed"
nc -zv $VPS 51820 2>&1 | grep -q "succeeded" && echo "✅ WireGuard port 51820 open" || echo "⚠️  WireGuard port closed"
echo ""

# 5. Email Security
echo "=== 5. EMAIL SERVER TESTS ==="
echo "Checking email configuration..."
dig MX $DOMAIN +short
dig TXT $DOMAIN +short | grep -i "spf\|dmarc\|dkim"
nc -zv $VPS 25 2>&1 | grep -q "succeeded" && echo "✅ SMTP port 25 open" || echo "⚠️  SMTP closed"
nc -zv $VPS 587 2>&1 | grep -q "succeeded" && echo "✅ Submission port 587 open" || echo "⚠️  Submission closed"
nc -zv $VPS 465 2>&1 | grep -q "succeeded" && echo "✅ SMTPS port 465 open" || echo "⚠️  SMTPS closed"
echo ""

# 6. SSH Security
echo "=== 6. SSH SECURITY ==="
echo "Checking SSH configuration..."
ssh-audit $VPS 2>/dev/null || echo "ssh-audit not installed"
echo ""

# 7. Service Enumeration
echo "=== 7. RUNNING SERVICES ==="
echo "Connecting to VPS to check services..."
sshpass -p 'PhazeVPN_57dd69f3ec20_2025' ssh -o StrictHostKeyChecking=no root@$VPS << 'EOFREMOTE'
echo "Active services:"
systemctl list-units --type=service --state=running | grep -E "(phazevpn|nginx|mysql|email|mail)"

echo ""
echo "Listening ports:"
netstat -tlnp | grep LISTEN

echo ""
echo "Recent failed login attempts:"
grep "Failed password" /var/log/auth.log | tail -10 2>/dev/null || echo "No auth.log access"

echo ""
echo "Firewall status:"
ufw status 2>/dev/null || iptables -L -n 2>/dev/null || echo "No firewall detected"
EOFREMOTE

echo ""

# 8. DNS Security
echo "=== 8. DNS SECURITY ==="
echo "Checking DNS configuration..."
dig $DOMAIN +short
dig www.$DOMAIN +short
dig mail.$DOMAIN +short
echo ""

# 9. Web Server Security
echo "=== 9. WEB SERVER TESTS ==="
echo "Checking for common misconfigurations..."
curl -s "https://$DOMAIN/admin" -o /dev/null -w "Admin page: %{http_code}\n"
curl -s "https://$DOMAIN/.git/config" -o /dev/null -w ".git exposure: %{http_code}\n"
curl -s "https://$DOMAIN/.env" -o /dev/null -w ".env exposure: %{http_code}\n"
curl -s "https://$DOMAIN/phpinfo.php" -o /dev/null -w "phpinfo: %{http_code}\n"
echo ""

# 10. API Security
echo "=== 10. API ENDPOINT TESTS ==="
echo "Testing API endpoints..."
curl -s "https://$DOMAIN/api/users" -o /dev/null -w "Users API: %{http_code}\n"
curl -s "https://$DOMAIN/api/vpn" -o /dev/null -w "VPN API: %{http_code}\n"
curl -s "https://$DOMAIN/api/admin" -o /dev/null -w "Admin API: %{http_code}\n"
echo ""

echo "=========================================="
echo "✅ Security Audit Complete"
echo "=========================================="
echo "Results saved to:"
echo "  - vps-portscan.txt"
echo "  - Full output above"
echo ""
echo "⚠️  CRITICAL FINDINGS TO REVIEW:"
echo "  1. Check for any exposed admin panels"
echo "  2. Verify firewall is active"
echo "  3. Review failed login attempts"
echo "  4. Ensure all services use HTTPS"
echo "  5. Check for exposed sensitive files (.git, .env)"
echo ""
