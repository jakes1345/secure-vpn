#!/bin/bash
# Quick fix for blank website - restart Flask and check Nginx

set -e

echo "🔧 QUICK FIX - WEBSITE BLANK PAGE"
echo "=================================="
echo ""

# Connect and fix
ssh root@15.204.11.19 << 'EOF'

echo "1. Stopping Flask..."
pkill -9 -f "python.*app.py" || true
sleep 2

echo "2. Starting Flask app..."
cd /opt/secure-vpn/web-portal
nohup python3 app.py > /tmp/flask-app.log 2>&1 &
sleep 3

echo "3. Checking Flask..."
ps aux | grep "python.*app.py" | grep -v grep
curl -s http://127.0.0.1:5000/ | head -20

echo ""
echo "4. Checking Nginx config..."
grep -A5 "proxy_pass" /etc/nginx/sites-enabled/securevpn | head -10

echo ""
echo "5. Restarting Nginx..."
systemctl restart nginx

echo ""
echo "✅ Done! Check website now."

EOF

echo ""
echo "✅ Fix applied!"

