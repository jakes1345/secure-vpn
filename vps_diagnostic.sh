#!/bin/bash
# VPS Comprehensive Audit & Fix

echo "=========================================="
echo "  PhazeVPN VPS Complete Diagnostic"
echo "=========================================="

# 1. Check Running Services
echo -e "\n1. RUNNING SERVICES:"
echo "VPN Server:"
ps aux | grep phazevpn-server | grep -v grep || echo "  ❌ NOT RUNNING"

echo "Web Portal:"
ps aux | grep "python3 app.py" | grep web-portal | grep -v grep || echo "  ❌ NOT RUNNING"

echo "Email Service:"
ps aux | grep "python3 app.py" | grep email-service | grep -v grep || echo "  ❌ NOT RUNNING"

# 2. Check Database
echo -e "\n2. DATABASE STATUS:"
mysql -u root -pJakes1328!@ -e "SHOW DATABASES;" 2>/dev/null | grep -E "phaze|vpn" || echo "  ⚠️  No PhazeVPN database found"

# 3. Check Python Environment
echo -e "\n3. PYTHON ENVIRONMENT:"
if [ -d "/opt/phazevpn/venv" ]; then
    echo "  ✅ Virtual environment exists"
    /opt/phazevpn/venv/bin/python3 -c "import flask; print('  ✅ Flask installed')" 2>/dev/null || echo "  ❌ Flask NOT installed"
    /opt/phazevpn/venv/bin/python3 -c "import mysql.connector; print('  ✅ MySQL connector installed')" 2>/dev/null || echo "  ❌ MySQL connector NOT installed"
else
    echo "  ❌ Virtual environment NOT found"
fi

# 4. Check Config Files
echo -e "\n4. CONFIGURATION FILES:"
[ -f "/opt/phaze-vpn/web-portal/app.py" ] && echo "  ✅ app.py exists" || echo "  ❌ app.py missing"
[ -f "/opt/phazevpn/phazevpn-protocol-go/phazevpn-server" ] && echo "  ✅ VPN server binary exists" || echo "  ❌ VPN server binary missing"

# 5. Check Ports
echo -e "\n5. LISTENING PORTS:"
netstat -tulpn | grep -E ":(80|443|5000|5005|51821)" | awk '{print "  " $4 " -> " $7}'

# 6. Check Logs for Errors
echo -e "\n6. RECENT ERRORS:"
echo "Web Portal:"
tail -20 /var/log/phazeweb.log 2>/dev/null | grep -i error | tail -3 || echo "  No errors"

echo "VPN Server:"
tail -20 /var/log/phazevpn.log 2>/dev/null | grep -i error | tail -3 || echo "  No errors"

# 7. Check Database Tables
echo -e "\n7. DATABASE TABLES:"
mysql -u root -pJakes1328!@ -e "USE phazevpn_db; SHOW TABLES;" 2>/dev/null || echo "  ⚠️  Cannot access database"

echo -e "\n=========================================="
echo "  Diagnostic Complete"
echo "=========================================="
