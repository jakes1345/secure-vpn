#!/bin/bash
# Setup download server service on VPS

echo "🔧 Setting up PhazeVPN Download Server on VPS..."

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

# Enable and start service
systemctl enable phaze-vpn-download
systemctl start phaze-vpn-download

echo "✅ Download server service enabled and started"

# Check status
sleep 2
systemctl status phaze-vpn-download --no-pager -l

echo ""
echo "✅ Setup complete!"
echo ""
echo "Download server is now running at: http://phazevpn.com:8081"
echo "Check status: systemctl status phaze-vpn-download"

