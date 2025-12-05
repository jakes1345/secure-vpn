#!/bin/bash
# Quick test script for email server

echo "🧪 Testing Email Server Setup"
echo "=============================="

echo ""
echo "1️⃣ Checking services..."
systemctl is-active postfix && echo "   ✅ Postfix: running" || echo "   ❌ Postfix: not running"
systemctl is-active dovecot && echo "   ✅ Dovecot: running" || echo "   ❌ Dovecot: not running"
systemctl is-active opendkim && echo "   ✅ OpenDKIM: running" || echo "   ❌ OpenDKIM: not running"

echo ""
echo "2️⃣ Checking ports..."
netstat -tlnp | grep -E ':25|:587|:465|:143|:993' | head -5

echo ""
echo "3️⃣ Testing SMTP connection..."
timeout 3 telnet localhost 25 <<EOF
quit
EOF

echo ""
echo "4️⃣ Checking Postfix config..."
grep "myhostname = mail.phazevpn.com" /etc/postfix/main.cf && echo "   ✅ Postfix configured for mail.phazevpn.com" || echo "   ❌ Postfix not configured"

echo ""
echo "5️⃣ Checking admin user..."
id admin && echo "   ✅ Admin user exists" || echo "   ❌ Admin user missing"
test -d /home/admin/Maildir && echo "   ✅ Maildir exists" || echo "   ❌ Maildir missing"

echo ""
echo "✅ Test complete!"

