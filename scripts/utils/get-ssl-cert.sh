#!/bin/bash
# Get Let's Encrypt SSL certificate for DuckDNS domain

DOMAIN="phazevpn.duckdns.org"
VPS_IP="15.204.11.19"

echo "🔒 Getting Let's Encrypt SSL Certificate..."
echo "=============================================="

# Install certbot
echo ""
echo "1️⃣  Installing certbot..."
apt-get update -qq
apt-get install -y certbot -qq

# Check if certbot exists
if ! command -v certbot &> /dev/null; then
    echo "   Installing via snap (alternative method)..."
    apt-get install -y snapd -qq
    systemctl enable --now snapd
    sleep 5
    snap install core
    snap refresh core
    snap install --classic certbot
    ln -sf /snap/bin/certbot /usr/bin/certbot
fi

# Verify
if ! command -v certbot &> /dev/null; then
    echo "❌ Certbot installation failed"
    exit 1
fi

echo "   ✅ Certbot installed: $(certbot --version | head -1)"

# Stop nginx
echo ""
echo "2️⃣  Stopping nginx temporarily..."
systemctl stop nginx

# Get certificate
echo ""
echo "3️⃣  Obtaining SSL certificate..."
certbot certonly --standalone \
    --non-interactive \
    --agree-tos \
    --email bigjacob710@gmail.com \
    -d $DOMAIN \
    --preferred-challenges http

if [ $? -eq 0 ]; then
    echo "   ✅ Certificate obtained!"
    
    # Configure nginx
    echo ""
    echo "4️⃣  Configuring nginx with SSL..."
    cat > /etc/nginx/sites-available/securevpn << EOF
server {
    listen 80;
    server_name $DOMAIN $VPS_IP;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN $VPS_IP;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
    
    nginx -t && systemctl restart nginx
    
    echo ""
    echo "=============================================="
    echo "✅ SSL CERTIFICATE INSTALLED!"
    echo "=============================================="
    echo ""
    echo "🌐 Your Secure Portal:"
    echo "   https://$DOMAIN"
    echo ""
    echo "✅ Features:"
    echo "   ✅ Valid SSL certificate (Let's Encrypt)"
    echo "   ✅ No certificate warnings!"
    echo "   ✅ DuckDNS auto-updates every 5 min"
    echo ""
else
    echo "❌ Certificate request failed"
    echo "DNS might need more time to propagate"
    systemctl start nginx
    exit 1
fi

