#!/bin/bash
# Setup Unified Web Portal
# Integrates Email, Files, and Productivity

set -e

echo "🌐 Setting up Unified Web Portal..."

# Install dependencies
apt-get update
apt-get install -y \
    python3-pip \
    python3-flask \
    python3-flask-cors \
    nginx

pip3 install \
    flask \
    flask-cors \
    requests \
    gunicorn

# Create portal directory
PORTAL_DIR="/opt/phazevpn-portal"
mkdir -p ${PORTAL_DIR}
cd ${PORTAL_DIR}

# Copy portal files (assuming they're in the repo)
# In production, these would be deployed from the repo

# Create systemd service
cat > /etc/systemd/system/phazevpn-portal.service << 'SERVICE_EOF'
[Unit]
Description=PhazeVPN Unified Web Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phazevpn-portal
ExecStart=/usr/bin/gunicorn -w 4 -b 0.0.0.0:8080 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Configure Nginx reverse proxy
cat > /etc/nginx/sites-available/phazevpn-portal << 'NGINX_EOF'
server {
    listen 80;
    server_name phazevpn.duckdns.org;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/phazevpn-portal /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Enable and start service
systemctl daemon-reload
systemctl enable phazevpn-portal
systemctl start phazevpn-portal

# Configure firewall
ufw allow 8080/tcp comment 'Unified Web Portal'
ufw allow 80/tcp comment 'Nginx HTTP'

echo "✅ Unified Web Portal setup complete!"
echo "   - Portal: http://phazevpn.duckdns.org"
echo "   - Direct: http://0.0.0.0:8080"
