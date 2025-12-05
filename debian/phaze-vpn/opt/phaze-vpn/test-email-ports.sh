#!/bin/bash
# Test email server ports

echo "🧪 Testing Email Server Ports"
echo "=============================="

echo ""
echo "1️⃣ Testing SMTP (port 25)..."
timeout 5 bash -c 'echo "QUIT" | telnet mail.phazevpn.com 25 2>&1 | head -10' || echo "   Connection test complete"

echo ""
echo "2️⃣ Testing SMTP Submission (port 587)..."
timeout 5 bash -c 'echo "QUIT" | telnet mail.phazevpn.com 587 2>&1 | head -10' || echo "   Connection test complete"

echo ""
echo "3️⃣ Testing IMAP (port 993)..."
timeout 5 openssl s_client -connect mail.phazevpn.com:993 -quiet 2>&1 | head -5 || echo "   Connection test complete"

echo ""
echo "4️⃣ Checking if Postfix is listening..."
netstat -tlnp | grep :25

echo ""
echo "5️⃣ Checking Postfix logs..."
tail -5 /var/log/mail.log 2>/dev/null || echo "   No recent logs"

echo ""
echo "✅ Tests complete!"

