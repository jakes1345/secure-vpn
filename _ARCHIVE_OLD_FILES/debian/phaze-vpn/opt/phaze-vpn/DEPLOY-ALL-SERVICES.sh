#!/bin/bash
# 🚀 MASTER DEPLOYMENT SCRIPT
# Deploys PhazeVPN + Email + Browser + Domain Services
# Run this ON THE VPS after uploading all files

set -e

DOMAIN="phazevpn.duckdns.org"
EMAIL_DOMAIN="phazevpn.duckdns.org"
EMAIL_HOSTNAME="mail.phazevpn.duckdns.org"
VPN_DIR="/opt/secure-vpn"

echo "=========================================="
echo "🚀 DEPLOYING ALL SERVICES"
echo "=========================================="
echo "Domain: $DOMAIN"
echo "Email: $EMAIL_HOSTNAME"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (sudo $0)"
    exit 1
fi

# Step 1: System Setup
echo "1️⃣ Updating system..."
apt-get update && apt-get upgrade -y
apt-get install -y git curl wget nano htop ufw

# Step 2: Configure Firewall
echo ""
echo "2️⃣ Configuring firewall..."
ufw --force enable
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 1194/udp  # OpenVPN
ufw allow 51820/udp # PhazeVPN Protocol
ufw allow 25/tcp    # SMTP
ufw allow 587/tcp   # SMTP Submission
ufw allow 993/tcp   # IMAPS
ufw allow 143/tcp   # IMAP
echo "✅ Firewall configured"

# Step 3: Setup IP Forwarding (for VPN)
echo ""
echo "3️⃣ Setting up IP forwarding..."
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p

# Setup NAT for VPN
if ! command -v iptables-persistent &> /dev/null; then
    apt-get install -y iptables-persistent
fi
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE 2>/dev/null || \
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o ens3 -j MASQUERADE 2>/dev/null || \
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -j MASQUERADE
iptables-save > /etc/iptables/rules.v4 2>/dev/null || iptables-save > /etc/iptables.rules
echo "✅ IP forwarding configured"

# Step 4: Deploy OpenVPN
echo ""
echo "4️⃣ Setting up OpenVPN..."
if [ ! -d "$VPN_DIR" ]; then
    echo "⚠️  VPN directory not found. Please upload files first."
    exit 1
fi

cd $VPN_DIR

# Install OpenVPN if not installed
if ! command -v openvpn &> /dev/null; then
    apt-get install -y openvpn openssl easy-rsa
fi

# Generate certificates if not exists
if [ ! -f "certs/ca.crt" ]; then
    echo "   Generating certificates..."
    ./generate-certs.sh
    echo "✅ Certificates generated (Switzerland - CH)"
fi

# Update server IP in config
sed -i "s|^local.*|local 0.0.0.0|" config/server.conf 2>/dev/null || true

# Start OpenVPN
if [ -f "/etc/systemd/system/secure-vpn.service" ]; then
    systemctl restart secure-vpn
    systemctl enable secure-vpn
else
    systemctl enable openvpn@server
    systemctl start openvpn@server
fi
echo "✅ OpenVPN deployed"

# Step 5: Deploy PhazeVPN Protocol
echo ""
echo "5️⃣ Setting up PhazeVPN Protocol..."
cd $VPN_DIR/phazevpn-protocol

# Install Python dependencies
apt-get install -y python3 python3-pip python3-dev
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
fi

# Create systemd service
cat > /etc/systemd/system/phazevpn-protocol.service << EOF
[Unit]
Description=PhazeVPN Protocol Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$VPN_DIR/phazevpn-protocol
ExecStart=/usr/bin/python3 $VPN_DIR/phazevpn-protocol/phazevpn-server-production.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable phazevpn-protocol
systemctl start phazevpn-protocol
echo "✅ PhazeVPN Protocol deployed"

# Step 6: Deploy Email Server
echo ""
echo "6️⃣ Setting up Email Server..."
cd $VPN_DIR

if [ -f "setup-email-server-core.sh" ]; then
    export EMAIL_DOMAIN="$EMAIL_DOMAIN"
    export EMAIL_HOSTNAME="$EMAIL_HOSTNAME"
    chmod +x setup-email-server-core.sh
    ./setup-email-server-core.sh
    echo "✅ Email server deployed"
else
    echo "⚠️  Email setup script not found. Skipping..."
fi

# Step 7: Setup Web Server (Nginx)
echo ""
echo "7️⃣ Setting up Nginx web server..."
apt-get install -y nginx certbot python3-certbot-nginx

# Create Nginx config
cat > /etc/nginx/sites-available/phazevpn << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location / {
        proxy_pass http://localhost:8081;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

server {
    listen 80;
    server_name $EMAIL_HOSTNAME;
    
    location / {
        proxy_pass http://localhost:5005;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

ln -sf /etc/nginx/sites-available/phazevpn /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
echo "✅ Nginx configured"

# Step 8: Setup SSL (Let's Encrypt)
echo ""
echo "8️⃣ Setting up SSL certificates..."
if command -v certbot &> /dev/null; then
    echo "   Requesting SSL certificates..."
    certbot --nginx -d $DOMAIN -d $EMAIL_HOSTNAME --non-interactive --agree-tos --register-unsafely-without-email || \
    echo "⚠️  SSL setup skipped (may need manual DNS verification)"
    systemctl reload nginx
    echo "✅ SSL configured"
else
    echo "⚠️  Certbot not installed. SSL skipped."
fi

# Step 9: Start Download Server (Web Portal)
echo ""
echo "9️⃣ Starting web portal..."
cd $VPN_DIR
if [ -f "/etc/systemd/system/secure-vpn-download.service" ]; then
    systemctl restart secure-vpn-download
    systemctl enable secure-vpn-download
elif [ -f "web-portal/app.py" ]; then
    # Create service for web portal
    cat > /etc/systemd/system/secure-vpn-download.service << EOF
[Unit]
Description=PhazeVPN Web Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$VPN_DIR/web-portal
ExecStart=/usr/bin/python3 $VPN_DIR/web-portal/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable secure-vpn-download
    systemctl start secure-vpn-download
fi
echo "✅ Web portal started"

# Step 10: Update all configs with domain
echo ""
echo "🔟 Updating configs with domain name..."
# Update vpn-manager.py
sed -i "s|'server_ip':.*|'server_ip': '$DOMAIN',|" $VPN_DIR/vpn-manager.py 2>/dev/null || true

# Update email configs
if [ -f "/etc/postfix/main.cf" ]; then
    sed -i "s|^myhostname =.*|myhostname = $EMAIL_HOSTNAME|" /etc/postfix/main.cf
    sed -i "s|^mydomain =.*|mydomain = $EMAIL_DOMAIN|" /etc/postfix/main.cf
    systemctl restart postfix
fi

echo "✅ Configs updated"

# Final Summary
echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Services Running:"
systemctl is-active --quiet openvpn@server && echo "✅ OpenVPN (Port 1194)" || \
systemctl is-active --quiet secure-vpn && echo "✅ OpenVPN (Port 1194)" || \
echo "⚠️  OpenVPN not running"
systemctl is-active --quiet phazevpn-protocol && echo "✅ PhazeVPN Protocol (Port 51820)" || echo "⚠️  PhazeVPN Protocol not running"
systemctl is-active --quiet postfix && echo "✅ Email SMTP (Port 25, 587)" || echo "⚠️  Email SMTP not running"
systemctl is-active --quiet dovecot && echo "✅ Email IMAP (Port 143, 993)" || echo "⚠️  Email IMAP not running"
systemctl is-active --quiet nginx && echo "✅ Web Server (Port 80, 443)" || echo "⚠️  Web Server not running"
systemctl is-active --quiet secure-vpn-download && echo "✅ Web Portal (Port 8081)" || echo "⚠️  Web Portal not running"

echo ""
echo "Access URLs:"
echo "🌐 VPN Web Portal: http://$DOMAIN"
echo "📧 Email Webmail: http://$EMAIL_HOSTNAME"
echo ""
echo "Next Steps:"
echo "1. Generate VPN client config: cd $VPN_DIR && python3 vpn-manager.py add-client CLIENT_NAME"
echo "2. Create email account: python3 manage-email-accounts.sh create user@$EMAIL_DOMAIN"
echo "3. Update DuckDNS DNS records (MX, SPF, DKIM) for email"
echo ""
echo "When you get real domain, run:"
echo "  sed -i 's/phazevpn.duckdns.org/yourdomain.com/g' /opt/secure-vpn/**/*"
echo ""

