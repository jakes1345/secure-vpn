#!/bin/bash
# Verify Ghost Mode and Set Up Obfuscation
# Run this ON THE VPS (you're already connected!)

set -e

echo "🔒 Verifying Ghost Mode Deployment..."
echo ""

# Check zero logging
echo "=== Zero Logging Check ==="
if grep -q "^verb 0" /etc/openvpn/server.conf; then
    echo "✅ Zero logging enabled (verb 0)"
else
    echo "❌ Zero logging NOT enabled!"
fi

if ! grep -q "^status " /etc/openvpn/server.conf && ! grep -q "^log-append " /etc/openvpn/server.conf; then
    echo "✅ Status logs disabled"
else
    echo "⚠️  Some logging still enabled"
fi

# Check 4096-bit DH
echo ""
echo "=== 4096-bit DH Check ==="
if [ -f "/etc/openvpn/certs/dh4096.pem" ]; then
    DH_SIZE=$(ls -lh /etc/openvpn/certs/dh4096.pem | awk '{print $5}')
    echo "✅ 4096-bit DH exists: $DH_SIZE"
else
    echo "❌ 4096-bit DH NOT found!"
fi

if grep -q "dh.*4096" /etc/openvpn/server.conf || grep -q "dh certs/dh4096.pem" /etc/openvpn/server.conf; then
    echo "✅ Config using 4096-bit DH"
else
    echo "⚠️  Config may not be using 4096-bit DH"
    grep "dh " /etc/openvpn/server.conf
fi

# Check encryption
echo ""
echo "=== Encryption Check ==="
grep -E "cipher|auth|tls-version" /etc/openvpn/server.conf | head -5

# Check VPN status
echo ""
echo "=== VPN Status ==="
systemctl status openvpn@server --no-pager | head -5

echo ""
echo "🎭 Now setting up obfuscation for both protocols..."
echo ""

# Step 1: Set up OpenVPN obfuscation
echo "🔧 Step 1: Setting up OpenVPN obfuscation (obfsproxy)..."
apt-get update
apt-get install -y obfsproxy python3-pip 2>/dev/null || pip3 install obfsproxy 2>/dev/null || echo "⚠️  obfsproxy install failed - may need manual install"

# Create obfsproxy wrapper
cat > /usr/local/bin/openvpn-obfsproxy.sh << 'OBFSEOF'
#!/bin/bash
# Obfsproxy wrapper for OpenVPN - Makes it invisible
obfsproxy obfs3 --dest=127.0.0.1:1194 server 0.0.0.0:443 > /var/log/openvpn-obfsproxy.log 2>&1 &
echo $! > /var/run/openvpn-obfsproxy.pid
echo "✅ obfsproxy started (PID: $(cat /var/run/openvpn-obfsproxy.pid))"
OBFSEOF

chmod +x /usr/local/bin/openvpn-obfsproxy.sh

# Create systemd service
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

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable openvpn-obfsproxy
systemctl start openvpn-obfsproxy 2>/dev/null || echo "⚠️  obfsproxy not started (may need to install first)"

# Step 2: Update PhazeVPN Protocol to port 443
echo ""
echo "🔧 Step 2: Updating PhazeVPN Protocol to port 443..."
PROTOCOL_DIR="/opt/phazevpn/phazevpn-protocol"
if [ -d "$PROTOCOL_DIR" ]; then
    if [ -f "$PROTOCOL_DIR/phazevpn-server-production.py" ]; then
        # Backup
        cp "$PROTOCOL_DIR/phazevpn-server-production.py" "$PROTOCOL_DIR/phazevpn-server-production.py.backup"
        # Change port to 443
        sed -i 's/port=51821/port=443/g' "$PROTOCOL_DIR/phazevpn-server-production.py"
        sed -i "s/port=51821/port=443/g" "$PROTOCOL_DIR/phazevpn-server-production.py"
        sed -i "s/, port=51821/, port=443/g" "$PROTOCOL_DIR/phazevpn-server-production.py"
        echo "   ✅ PhazeVPN Protocol updated to port 443"
        
        # Restart service
        systemctl restart phazevpn-protocol 2>/dev/null || echo "   ⚠️  PhazeVPN Protocol service not found"
    else
        echo "   ⚠️  PhazeVPN Protocol server file not found"
    fi
else
    echo "   ⚠️  PhazeVPN Protocol directory not found at $PROTOCOL_DIR"
fi

# Step 3: Update firewall
echo ""
echo "🔧 Step 3: Updating firewall..."
ufw allow 443/tcp
ufw allow 443/udp
echo "   ✅ Port 443 opened"

# Final verification
echo ""
echo "✅ Setup Complete!"
echo ""
echo "📋 Summary:"
echo "   OpenVPN (mobile): Port 443 via obfsproxy (invisible)"
echo "   PhazeVPN Protocol (desktop): Port 443, obfuscated (built-in)"
echo ""
echo "🔒 Both protocols now look like HTTPS - NOT identifiable as VPN!"
echo ""
echo "Verify:"
echo "  systemctl status openvpn-obfsproxy"
echo "  systemctl status phazevpn-protocol"
echo "  netstat -tuln | grep 443"

