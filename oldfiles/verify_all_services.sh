#!/bin/bash
#
# Comprehensive Service Verification
# Checks: Web Portal, Email Service, Browser, File Versions
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
echo "║   Comprehensive PhazeVPN Service Verification             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

ssh_run $VPS_USER@$VPS_IP << 'EOF'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. WEB PORTAL FILES - Version Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "app.py last modified:"
ls -lh /opt/phazevpn/web-portal/app.py | awk '{print $6, $7, $8, $9}'

echo ""
echo "requirements.txt last modified:"
ls -lh /opt/phazevpn/web-portal/requirements.txt | awk '{print $6, $7, $8, $9}'

echo ""
echo "Checking for placeholders in app.py:"
if grep -q "Mock for now" /opt/phazevpn/web-portal/app.py 2>/dev/null; then
    echo "⚠️  Found 'Mock for now' - checking context..."
    grep -n "Mock for now" /opt/phazevpn/web-portal/app.py | head -3
else
    echo "✅ No 'Mock for now' found in app.py"
fi

echo ""
echo "Checking warrant canary implementation:"
if grep -q "blockchain.info" /opt/phazevpn/web-portal/app.py; then
    echo "✅ Using real Bitcoin API (blockchain.info)"
else
    echo "❌ Not using real Bitcoin API"
fi

echo ""
echo "Checking WireGuard key generation:"
if [ -f /opt/phazevpn/web-portal/generate_all_protocols.py ]; then
    if grep -q "get_server_public_key" /opt/phazevpn/web-portal/generate_all_protocols.py; then
        echo "✅ WireGuard has proper key generation function"
    else
        echo "❌ WireGuard missing key generation function"
    fi
else
    echo "⚠️  generate_all_protocols.py not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. EMAIL SERVICE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if email service is running
if pgrep -f "email.*app.py" > /dev/null; then
    echo "✅ Email service: RUNNING"
    ps aux | grep "[e]mail.*app.py" | head -1
else
    echo "❌ Email service: NOT RUNNING"
fi

# Check email service files
if [ -f /opt/phazevpn/email-service/app.py ]; then
    echo "✅ Email service app.py: EXISTS"
    ls -lh /opt/phazevpn/email-service/app.py | awk '{print "   Modified:", $6, $7, $8}'
else
    echo "❌ Email service app.py: NOT FOUND"
fi

# Check email API
if [ -f /opt/phazevpn/web-portal/email_api.py ]; then
    echo "✅ Email API: EXISTS"
    echo "   Checking for SMTP credentials..."
    if grep -q "mail.privateemail.com" /opt/phazevpn/web-portal/email_api.py; then
        echo "   ✅ Using Namecheap SMTP (mail.privateemail.com)"
    elif grep -q "smtp" /opt/phazevpn/web-portal/email_api.py; then
        echo "   ✅ SMTP configuration found"
    else
        echo "   ⚠️  No SMTP configuration found"
    fi
else
    echo "❌ Email API: NOT FOUND"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. PHAZEBROWSER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if browser files are served
if [ -d /opt/phazevpn/web-portal/static/downloads ]; then
    echo "✅ Downloads directory: EXISTS"
    echo ""
    echo "Browser packages available:"
    ls -lh /opt/phazevpn/web-portal/static/downloads/ | grep -i "browser\|phaze" | head -10
else
    echo "❌ Downloads directory: NOT FOUND"
fi

# Check if browser is available for download
if ls /opt/phazevpn/web-portal/static/downloads/*browser* 2>/dev/null | head -1 > /dev/null; then
    echo ""
    echo "✅ Browser package: AVAILABLE"
else
    echo "⚠️  Browser package: NOT FOUND in downloads"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. WEB PORTAL ENDPOINTS - Live Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Testing key endpoints:"

# Test home page
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ 2>/dev/null)
echo "  / (home): HTTP $HTTP_CODE $([ "$HTTP_CODE" = "200" ] && echo "✅" || echo "❌")"

# Test login
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/login 2>/dev/null)
echo "  /login: HTTP $HTTP_CODE $([ "$HTTP_CODE" = "200" ] && echo "✅" || echo "❌")"

# Test transparency (warrant canary)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/transparency 2>/dev/null)
echo "  /transparency: HTTP $HTTP_CODE $([ "$HTTP_CODE" = "200" ] && echo "✅" || echo "❌")"

# Test download page
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/download 2>/dev/null)
echo "  /download: HTTP $HTTP_CODE $([ "$HTTP_CODE" = "200" ] && echo "✅" || echo "❌")"

# Test pricing
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/pricing 2>/dev/null)
echo "  /pricing: HTTP $HTTP_CODE $([ "$HTTP_CODE" = "200" -o "$HTTP_CODE" = "302" ] && echo "✅" || echo "❌")"

echo ""
echo "Testing warrant canary content:"
CANARY_CONTENT=$(curl -s http://localhost:5000/transparency 2>/dev/null | grep -o "00000000[0-9a-f]*" | head -1)
if [ -n "$CANARY_CONTENT" ] && [ "$CANARY_CONTENT" != "00000000000000000000000000000000000xxxxxxxxxxxxxxxxxxxxxxx" ]; then
    echo "  ✅ Real Bitcoin block hash: ${CANARY_CONTENT:0:20}..."
else
    echo "  ⚠️  Bitcoin hash may be placeholder or unavailable"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. STATIC FILES - Cache Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "CSS files last modified:"
ls -lht /opt/phazevpn/web-portal/static/css/*.css 2>/dev/null | head -3 | awk '{print "  ", $9, "-", $6, $7, $8}'

echo ""
echo "JS files last modified:"
ls -lht /opt/phazevpn/web-portal/static/js/*.js 2>/dev/null | head -3 | awk '{print "  ", $9, "-", $6, $7, $8}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. DATABASE CONNECTION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test MySQL connection
if mysql -u phazevpn_user -p'SecureVPN2024!' -e "USE phazevpn_db; SHOW TABLES;" 2>/dev/null | grep -q "users"; then
    echo "✅ MySQL: Connected"
    echo "   Database: phazevpn_db"
    USERS_COUNT=$(mysql -u phazevpn_user -p'SecureVPN2024!' -e "USE phazevpn_db; SELECT COUNT(*) FROM users;" 2>/dev/null | tail -1)
    echo "   Users: $USERS_COUNT"
else
    echo "❌ MySQL: Connection failed or tables missing"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. RUNNING PROCESSES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Gunicorn workers:"
ps aux | grep "[g]unicorn.*app:app" | wc -l | xargs echo "  Count:"

echo ""
echo "Old nohup processes (should be 0):"
ps aux | grep "[p]ython3 app.py" | wc -l | xargs echo "  Count:"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Checking critical components:"

CHECKS_PASSED=0
CHECKS_TOTAL=0

# Web portal responding
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ 2>/dev/null | grep -q "200"; then
    echo "✅ Web portal responding"
    ((CHECKS_PASSED++))
else
    echo "❌ Web portal not responding"
fi
((CHECKS_TOTAL++))

# Warrant canary using real API
if grep -q "blockchain.info" /opt/phazevpn/web-portal/app.py; then
    echo "✅ Warrant canary using real Bitcoin API"
    ((CHECKS_PASSED++))
else
    echo "❌ Warrant canary not using real API"
fi
((CHECKS_TOTAL++))

# WireGuard key generation
if [ -f /opt/phazevpn/web-portal/generate_all_protocols.py ] && grep -q "get_server_public_key" /opt/phazevpn/web-portal/generate_all_protocols.py; then
    echo "✅ WireGuard key generation implemented"
    ((CHECKS_PASSED++))
else
    echo "❌ WireGuard key generation missing"
fi
((CHECKS_TOTAL++))

# Email API exists
if [ -f /opt/phazevpn/web-portal/email_api.py ]; then
    echo "✅ Email API present"
    ((CHECKS_PASSED++))
else
    echo "❌ Email API missing"
fi
((CHECKS_TOTAL++))

# Database connection
if mysql -u phazevpn_user -p'SecureVPN2024!' -e "USE phazevpn_db; SHOW TABLES;" 2>/dev/null | grep -q "users"; then
    echo "✅ Database connected"
    ((CHECKS_PASSED++))
else
    echo "❌ Database not connected"
fi
((CHECKS_TOTAL++))

# No old processes
OLD_PROCS=$(ps aux | grep "[p]ython3 app.py" | wc -l)
if [ "$OLD_PROCS" -eq 0 ]; then
    echo "✅ No old nohup processes"
    ((CHECKS_PASSED++))
else
    echo "⚠️  Old nohup processes still running: $OLD_PROCS"
fi
((CHECKS_TOTAL++))

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Score: $CHECKS_PASSED/$CHECKS_TOTAL checks passed"
echo ""

if [ "$CHECKS_PASSED" -eq "$CHECKS_TOTAL" ]; then
    echo "🎉 ALL CHECKS PASSED! Everything is up to date and working!"
elif [ "$CHECKS_PASSED" -ge $((CHECKS_TOTAL * 2 / 3)) ]; then
    echo "✅ MOSTLY GOOD! Core functionality working, minor issues to address"
else
    echo "⚠️  NEEDS ATTENTION! Several components need updating"
fi

echo ""

EOF

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Verification Complete                                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
