#!/bin/bash
# ============================================
# Quick Verification Script - Run After Restore
# ============================================

echo "=========================================="
echo "🔍 VERIFYING VPS AFTER RESTORE"
echo "=========================================="
echo ""

# Check VPN server
echo "1️⃣ Checking OpenVPN server..."
if systemctl is-active openvpn >/dev/null 2>&1; then
    echo "   ✅ OpenVPN is RUNNING"
else
    echo "   ❌ OpenVPN is NOT running"
    echo "   💡 Try: systemctl start openvpn"
fi
echo ""

# Check certificates
echo "2️⃣ Checking certificates..."
CERT_DIR="/opt/secure-vpn/certs"
if [ -d "$CERT_DIR" ]; then
    [ -f "$CERT_DIR/ca.crt" ] && echo "   ✅ CA cert exists" || echo "   ❌ CA cert missing"
    [ -f "$CERT_DIR/server.crt" ] && echo "   ✅ Server cert exists" || echo "   ❌ Server cert missing"
    [ -f "$CERT_DIR/server.key" ] && echo "   ✅ Server key exists" || echo "   ❌ Server key missing"
    [ -f "$CERT_DIR/dh.pem" ] && echo "   ✅ DH params exist" || echo "   ❌ DH params missing"
else
    echo "   ⚠️  Cert directory not found at $CERT_DIR"
    echo "   💡 Checking common locations..."
    find /opt /root /home -name "ca.crt" -type f 2>/dev/null | head -3
fi
echo ""

# Check config
echo "3️⃣ Checking server config..."
CONFIG_FILE="/opt/secure-vpn/config/server.conf"
if [ -f "$CONFIG_FILE" ]; then
    echo "   ✅ Server config exists"
    echo "   Location: $CONFIG_FILE"
else
    echo "   ⚠️  Server config not found at $CONFIG_FILE"
    find /opt /root /home -name "server.conf" -type f 2>/dev/null | head -3
fi
echo ""

# Check users
echo "4️⃣ Checking user accounts..."
USERS_FILE="/opt/secure-vpn/users.json"
if [ -f "$USERS_FILE" ]; then
    echo "   ✅ Users file exists"
    USER_COUNT=$(grep -c '"username"' "$USERS_FILE" 2>/dev/null || echo "0")
    echo "   Users found: $USER_COUNT"
else
    echo "   ⚠️  Users file not found at $USERS_FILE"
    find /opt /root /home -name "users.json" -type f 2>/dev/null | head -3
fi
echo ""

# Check firewall
echo "5️⃣ Checking firewall..."
if iptables -L INPUT -n 2>/dev/null | grep -q "22\|ssh"; then
    echo "   ✅ SSH rule exists in iptables"
else
    echo "   ❌ SSH rule missing in iptables"
    echo "   💡 May need to add firewall rule"
fi
echo ""

# Check DNS
echo "6️⃣ Checking DNS..."
if grep -q "8.8.8.8\|1.1.1.1\|8.8.4.4" /etc/resolv.conf 2>/dev/null; then
    echo "   ✅ DNS configured"
    cat /etc/resolv.conf
else
    echo "   ⚠️  DNS may not be configured"
fi
echo ""

# Check web portal
echo "7️⃣ Checking web portal..."
if systemctl list-units --type=service 2>/dev/null | grep -qiE "flask|portal|web"; then
    echo "   ✅ Web portal service found"
    systemctl list-units --type=service | grep -iE "flask|portal|web"
else
    echo "   ⚠️  Web portal service not found"
    echo "   💡 May need to start web portal manually"
fi
echo ""

# Summary
echo "=========================================="
echo "📋 SUMMARY"
echo "=========================================="
echo ""
echo "If everything shows ✅, you're good to go!"
echo "If you see ❌ or ⚠️, we may need to fix those items."
echo ""
echo "Next steps:"
echo "   1. Test VPN connection from a client"
echo "   2. Test web portal: https://phazevpn.duckdns.org"
echo "   3. Test user login"
echo ""

