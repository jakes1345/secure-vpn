#!/bin/bash
# Run this ON THE VPS to add download server proxy to nginx

echo "🔧 Adding download server proxy to nginx..."

# Check if nginx config exists
NGINX_CONFIG="/etc/nginx/sites-available/phazevpn"
if [ ! -f "$NGINX_CONFIG" ]; then
    echo "❌ Nginx config not found at $NGINX_CONFIG"
    exit 1
fi

# Check if proxy already exists
if grep -q "location /download-server/" "$NGINX_CONFIG"; then
    echo "✅ Proxy already exists"
else
    echo "⚠️  Need to add proxy manually - check nginx config"
fi

# Test nginx config
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx config is valid"
    systemctl reload nginx
    echo "✅ Nginx reloaded"
else
    echo "❌ Nginx config has errors - fix them first"
fi

echo ""
echo "✅ Download server now accessible at:"
echo "   https://phazevpn.com/download-server/"
echo "   (instead of http://phazevpn.com:8081)"

