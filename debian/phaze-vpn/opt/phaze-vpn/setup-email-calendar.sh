#!/bin/bash
# Setup Calendar System for PhazeVPN Email
# Implements CalDAV calendar server

set -e

echo "📅 Setting up Calendar System for PhazeVPN Email..."

# Install dependencies
echo "1️⃣ Installing calendar dependencies..."
apt-get update
apt-get install -y \
    radicale \
    python3-pip \
    python3-requests \
    nginx

# Install Radicale (CalDAV/CardDAV server)
echo "2️⃣ Configuring Radicale calendar server..."
pip3 install radicale[bcrypt]

# Create Radicale user
if ! id "radicale" &>/dev/null; then
    useradd -r -s /bin/false radicale
fi

# Create directories
mkdir -p /etc/radicale
mkdir -p /var/lib/radicale/collections
mkdir -p /var/log/radicale
chown -R radicale:radicale /var/lib/radicale
chown -R radicale:radicale /var/log/radicale

# Configure Radicale
cat > /etc/radicale/config << 'EOF'
[server]
hosts = 0.0.0.0:5232
ssl = False

[auth]
type = htpasswd
htpasswd_filename = /etc/radicale/users
htpasswd_encryption = bcrypt

[storage]
filesystem_folder = /var/lib/radicale/collections

[rights]
type = owner_only

[logging]
level = INFO
EOF

# Create initial user (will be managed by email system)
touch /etc/radicale/users
chmod 600 /etc/radicale/users
chown radicale:radicale /etc/radicale/users

# Create systemd service
cat > /etc/systemd/system/radicale.service << 'EOF'
[Unit]
Description=Radicale CalDAV/CardDAV Server
After=network.target

[Service]
Type=simple
User=radicale
ExecStart=/usr/local/bin/radicale
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start Radicale
systemctl daemon-reload
systemctl enable radicale
systemctl start radicale

# Configure Nginx reverse proxy
cat > /etc/nginx/sites-available/calendar << 'EOF'
server {
    listen 80;
    server_name calendar.phazevpn.duckdns.org;

    location / {
        proxy_pass http://127.0.0.1:5232;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/calendar /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "✅ Calendar system installed!"
echo ""
echo "📅 Calendar Server:"
echo "   - CalDAV URL: http://calendar.phazevpn.duckdns.org"
echo "   - Port: 5232"
echo "   - Service: radicale"
echo ""
echo "🔧 Next steps:"
echo "   1. Create calendar users: ./manage-calendar-users.sh add user@phazevpn.duckdns.org"
echo "   2. Configure email accounts to use calendar"
echo "   3. Test with calendar client (Thunderbird, Apple Calendar, etc.)"
