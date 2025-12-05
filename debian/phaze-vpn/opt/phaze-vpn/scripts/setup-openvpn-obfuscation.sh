#!/bin/bash
# Setup OpenVPN Obfuscation - Makes OpenVPN Look Like HTTPS
# Run this ON THE VPS

set -e

echo "🎭 Setting up OpenVPN obfuscation..."
echo "   This makes OpenVPN traffic look like random encrypted data"
echo "   DPI systems won't be able to identify it as VPN"
echo ""

# Install obfsproxy
echo "📦 Installing obfsproxy..."
if ! command -v obfsproxy &> /dev/null; then
    apt-get update
    apt-get install -y obfsproxy python3-pip || pip3 install obfsproxy
fi

# Create obfsproxy wrapper for OpenVPN
echo "🔧 Creating obfsproxy wrapper..."
cat > /usr/local/bin/openvpn-obfsproxy.sh << 'EOF'
#!/bin/bash
# Obfsproxy wrapper for OpenVPN
# Makes OpenVPN look like random encrypted data (not VPN)

# Start obfsproxy on port 443, forwarding to OpenVPN on 127.0.0.1:1194
obfsproxy obfs3 --dest=127.0.0.1:1194 server 0.0.0.0:443 > /var/log/openvpn-obfsproxy.log 2>&1 &
OBFS_PID=$!
echo $OBFS_PID > /var/run/openvpn-obfsproxy.pid
echo "✅ obfsproxy started (PID: $OBFS_PID)"
echo "   OpenVPN now accessible via port 443 (obfuscated)"
echo "   Traffic looks like random encrypted data - NOT identifiable as VPN"
EOF

chmod +x /usr/local/bin/openvpn-obfsproxy.sh

# Create systemd service
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/openvpn-obfsproxy.service << 'EOF'
[Unit]
Description=OpenVPN Obfsproxy Wrapper (Makes OpenVPN Invisible)
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
EOF

systemctl daemon-reload
systemctl enable openvpn-obfsproxy

# Update firewall
echo "🔧 Updating firewall..."
ufw allow 443/tcp
ufw allow 443/udp
echo "   ✅ Port 443 opened"

# Start service
echo "🔄 Starting obfsproxy service..."
systemctl start openvpn-obfsproxy

# Wait a moment
sleep 2

# Verify
if systemctl is-active --quiet openvpn-obfsproxy; then
    echo "✅ OpenVPN obfuscation is ACTIVE!"
    echo ""
    echo "📋 Summary:"
    echo "   OpenVPN (mobile): Port 443 via obfsproxy (invisible)"
    echo "   Traffic looks like: Random encrypted data (NOT VPN)"
    echo ""
    echo "🔒 Mobile clients can now connect to port 443 (obfuscated)"
else
    echo "⚠️  Service started but may need checking"
    systemctl status openvpn-obfsproxy --no-pager | head -10
fi

echo ""
echo "📝 Client Configuration:"
echo "   Mobile clients need to connect through obfsproxy:"
echo "   1. Start obfsproxy on client: obfsproxy obfs3 --dest=phazevpn.duckdns.org:443 client 127.0.0.1:1194"
echo "   2. Connect OpenVPN to: 127.0.0.1:1194"
echo ""

