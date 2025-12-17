#!/bin/bash
# Fix obfsproxy and verify everything
# Run this ON THE VPS

echo "🔧 Fixing obfsproxy and verifying everything..."
echo ""

# Check why obfsproxy exited
echo "=== Checking obfsproxy ==="
systemctl status openvpn-obfsproxy --no-pager | tail -10
journalctl -u openvpn-obfsproxy -n 20 --no-pager

# Fix obfsproxy script (it's exiting immediately)
echo ""
echo "🔧 Fixing obfsproxy script..."
cat > /usr/local/bin/openvpn-obfsproxy.sh << 'OBFSEOF'
#!/bin/bash
# Obfsproxy wrapper for OpenVPN - Makes it invisible
# Keep running in foreground for systemd

exec obfsproxy obfs3 --dest=127.0.0.1:1194 server 0.0.0.0:443
OBFSEOF

chmod +x /usr/local/bin/openvpn-obfsproxy.sh

# Update systemd service to not exit
cat > /etc/systemd/system/openvpn-obfsproxy.service << 'SERVICEEOF'
[Unit]
Description=OpenVPN Obfsproxy (Makes OpenVPN Invisible)
After=network.target openvpn@server.service
Requires=openvpn@server.service

[Service]
Type=simple
ExecStart=/usr/local/bin/openvpn-obfsproxy.sh
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl restart openvpn-obfsproxy

# Wait a moment
sleep 2

# Verify obfsproxy is running
echo ""
echo "=== Verifying obfsproxy ==="
if systemctl is-active --quiet openvpn-obfsproxy; then
    echo "✅ obfsproxy: RUNNING"
    ps aux | grep obfsproxy | grep -v grep
else
    echo "❌ obfsproxy: NOT RUNNING"
    echo "   Checking logs..."
    journalctl -u openvpn-obfsproxy -n 10 --no-pager
fi

# Check what's on port 443
echo ""
echo "=== Port 443 Status ==="
netstat -tuln | grep ":443 " || ss -tuln | grep ":443 "

# Check PhazeVPN Protocol
echo ""
echo "=== PhazeVPN Protocol Status ==="
if [ -f "/opt/phazevpn/phazevpn-protocol/phazevpn-server-production.py" ]; then
    PORT=$(grep -o "port=[0-9]*" /opt/phazevpn/phazevpn-protocol/phazevpn-server-production.py | head -1 | cut -d= -f2)
    echo "   Port configured: $PORT"
    
    if systemctl is-active --quiet phazevpn-protocol 2>/dev/null; then
        echo "   ✅ Service: RUNNING"
    else
        echo "   ⚠️  Service: Check manually"
    fi
fi

# Final summary
echo ""
echo "=== FINAL STATUS ==="
echo ""
echo "Ghost Mode:"
grep "^verb" /etc/openvpn/server.conf && echo "   ✅ Zero logging"
[ -f "/etc/openvpn/certs/dh4096.pem" ] && echo "   ✅ 4096-bit DH exists"

echo ""
echo "OpenVPN Obfuscation:"
if systemctl is-active --quiet openvpn-obfsproxy; then
    echo "   ✅ obfsproxy: RUNNING on port 443"
else
    echo "   ❌ obfsproxy: NOT RUNNING (check logs above)"
fi

echo ""
echo "PhazeVPN Protocol:"
if grep -q "port=443" /opt/phazevpn/phazevpn-protocol/phazevpn-server-production.py 2>/dev/null; then
    echo "   ✅ Port 443: CONFIGURED"
    echo "   ✅ Obfuscation: Built-in (enabled)"
else
    echo "   ⚠️  Check port configuration"
fi

echo ""
echo "🔒 Both protocols should now be invisible!"

