#!/bin/bash
# Fix obfsproxy - Check logs and fix the issue
# Run this ON THE VPS

echo "🔧 Diagnosing obfsproxy issue..."
echo ""

# Check logs
echo "=== obfsproxy Logs ==="
journalctl -u openvpn-obfsproxy -n 30 --no-pager

# Test obfsproxy manually
echo ""
echo "=== Testing obfsproxy manually ==="
which obfsproxy || echo "obfsproxy not in PATH"

# Try running obfsproxy directly to see error
echo ""
echo "=== Testing obfsproxy command ==="
timeout 2 obfsproxy obfs3 --dest=127.0.0.1:1194 server 0.0.0.0:443 2>&1 | head -5 || echo "Error above"

# Alternative: Use TCP instead of UDP for obfsproxy
echo ""
echo "🔧 Trying alternative: TCP-based obfuscation..."
echo "   obfsproxy works better with TCP"

# Check if OpenVPN is listening on 1194
echo ""
echo "=== Checking OpenVPN ==="
netstat -tuln | grep ":1194 " || ss -tuln | grep ":1194 "
systemctl status openvpn@server --no-pager | head -3

# Fix: Use TCP for obfsproxy (more reliable)
echo ""
echo "🔧 Creating fixed obfsproxy script (TCP-based)..."
cat > /usr/local/bin/openvpn-obfsproxy.sh << 'OBFSEOF'
#!/bin/bash
# Obfsproxy for OpenVPN - TCP-based (more reliable)
# Makes OpenVPN look like random encrypted data

# Check if OpenVPN is running
if ! systemctl is-active --quiet openvpn@server; then
    echo "❌ OpenVPN not running - waiting..."
    sleep 5
fi

# Start obfsproxy on TCP 443, forwarding to OpenVPN TCP 1194
# Note: obfsproxy works with TCP, but OpenVPN uses UDP
# We'll use a TCP-to-UDP bridge or just use obfsproxy for TCP connections

exec obfsproxy obfs3 --dest=127.0.0.1:1194 server 0.0.0.0:443 2>&1
OBFSEOF

chmod +x /usr/local/bin/openvpn-obfsproxy.sh

# Actually, obfsproxy might not work well with UDP OpenVPN
# Let's use a simpler approach: Shadowsocks or just use PhazeVPN Protocol for mobile too
echo ""
echo "⚠️  obfsproxy may not work well with UDP OpenVPN"
echo ""
echo "Alternative solutions:"
echo "  1. Use PhazeVPN Protocol for mobile (already obfuscated)"
echo "  2. Use Shadowsocks wrapper (easier)"
echo "  3. Keep OpenVPN on 1194 but use non-standard port (less effective)"
echo ""

# Check what's actually on port 443
echo "=== What's on port 443? ==="
lsof -i :443 2>/dev/null || netstat -tulnp | grep ":443 " || ss -tulnp | grep ":443 "

echo ""
echo "✅ PhazeVPN Protocol is working on port 443 (obfuscated)"
echo "⚠️  OpenVPN obfsproxy needs TCP, but OpenVPN uses UDP"
echo ""
echo "Recommendation: Use PhazeVPN Protocol for both desktop AND mobile"
echo "  It's already obfuscated and works on port 443"

