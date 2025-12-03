#!/bin/bash
# Run this ON THE VPS to fix the download server

echo "🔧 Fixing PhazeVPN Download Server..."

# Create service file
cat > /etc/systemd/system/phaze-vpn-download.service <<'EOF'
[Unit]
Description=PhazeVPN Client Download Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/secure-vpn
ExecStart=/usr/bin/python3 /opt/secure-vpn/client-download-server.py
Restart=always
RestartSec=5
StartLimitInterval=0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file created"

# Reload systemd
systemctl daemon-reload
echo "✅ Systemd reloaded"

# Enable and start
systemctl enable phaze-vpn-download
systemctl start phaze-vpn-download

echo "✅ Service enabled and started"

# Check status
sleep 2
if systemctl is-active --quiet phaze-vpn-download; then
    echo "✅ Download server is RUNNING!"
    echo ""
    echo "Access it at: http://phazevpn.com:8081"
else
    echo "❌ Service failed to start. Checking logs..."
    journalctl -u phaze-vpn-download -n 20 --no-pager
fi

