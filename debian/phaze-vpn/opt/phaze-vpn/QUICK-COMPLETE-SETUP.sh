#!/bin/bash
# Quick completion script - Run this on your VPS after DNS is added

echo "=========================================="
echo "🚀 Completing phazevpn.com Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (sudo $0)"
    exit 1
fi

VPN_DIR="/opt/secure-vpn"

# Step 1: Update domain
echo "1️⃣ Updating domain from duckdns.org to phazevpn.com..."
if [ -f "$VPN_DIR/scripts/update-domain-simple.sh" ]; then
    cd "$VPN_DIR"
    ./scripts/update-domain-simple.sh
else
    echo "   ⚠️  Update script not found, updating manually..."
    cd "$VPN_DIR"
    sed -i "s|phazevpn.duckdns.org|phazevpn.com|g" vpn-manager.py
    find config -type f -name "*.conf" -exec sed -i "s|phazevpn.duckdns.org|phazevpn.com|g" {} +
    echo "   ✅ Manual update complete"
fi

# Step 2: Check DNS
echo ""
echo "2️⃣ Checking DNS propagation..."
DNS_RESULT=$(dig +short phazevpn.com | head -1)
if [ "$DNS_RESULT" = "15.204.11.19" ]; then
    echo "   ✅ DNS is pointing to your VPS!"
elif [ -n "$DNS_RESULT" ]; then
    echo "   ⚠️  DNS shows: $DNS_RESULT (might not be propagated yet)"
    echo "   Wait 5-10 minutes and check again"
else
    echo "   ⚠️  DNS not resolving yet - wait 5-10 minutes"
fi

# Step 3: SSL Certificate
echo ""
echo "3️⃣ Setting up SSL certificate..."
if command -v certbot &> /dev/null; then
    echo "   Requesting SSL for phazevpn.com and www.phazevpn.com..."
    certbot --nginx -d phazevpn.com -d www.phazevpn.com --non-interactive --agree-tos --register-unsafely-without-email 2>&1 | head -20
    echo ""
    echo "   ✅ SSL setup attempted (check output above)"
else
    echo "   ⚠️  Certbot not installed. Install with: apt-get install certbot python3-certbot-nginx"
fi

# Step 4: Restart services
echo ""
echo "4️⃣ Restarting services..."
systemctl restart nginx 2>/dev/null && echo "   ✅ Nginx restarted" || echo "   ⚠️  Nginx not running"
systemctl restart openvpn@server 2>/dev/null && echo "   ✅ OpenVPN restarted" || echo "   ⚠️  OpenVPN not running"
systemctl restart phazevpn-protocol 2>/dev/null && echo "   ✅ PhazeVPN Protocol restarted" || echo "   ⚠️  PhazeVPN Protocol not running"

# Step 5: Test
echo ""
echo "5️⃣ Testing..."
echo ""
echo "DNS Check:"
dig phazevpn.com +short | head -1
echo ""
echo "Website Test:"
curl -I https://phazevpn.com 2>&1 | head -5 || echo "   HTTPS not ready yet - DNS might need more time"

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Your domain: phazevpn.com"
echo "Your VPS IP: 15.204.11.19"
echo ""
echo "Test in browser: https://phazevpn.com"
echo ""
