#!/bin/bash
# Simple domain update - Main domain only (skip email)

set -e

OLD_DOMAIN="phazevpn.duckdns.org"
NEW_DOMAIN="phazevpn.com"
VPN_DIR="/opt/secure-vpn"

echo "=========================================="
echo "🌐 Updating Domain (Simple - No Email)"
echo "=========================================="
echo "Updating: $OLD_DOMAIN → $NEW_DOMAIN"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (sudo $0)"
    exit 1
fi

# Step 1: Update VPN configs
echo "1️⃣ Updating VPN configuration..."
cd "$VPN_DIR"

# Update vpn-manager.py
if [ -f "vpn-manager.py" ]; then
    sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" vpn-manager.py
    echo "   ✅ Updated vpn-manager.py"
fi

# Update server configs
if [ -d "config" ]; then
    find config -type f -name "*.conf" -exec sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" {} +
    echo "   ✅ Updated server configs"
fi

# Update client configs
if [ -d "client-configs" ]; then
    find client-configs -type f -name "*.ovpn" -exec sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" {} + 2>/dev/null || true
    echo "   ✅ Updated client configs"
fi

# Update PhazeVPN protocol
if [ -d "phazevpn-protocol" ]; then
    find phazevpn-protocol -type f -name "*.py" -exec sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" {} + 2>/dev/null || true
    echo "   ✅ Updated PhazeVPN protocol"
fi

echo ""

# Step 2: Update Nginx (skip mail)
echo "2️⃣ Updating web server (skipping email)..."

if [ -d "/etc/nginx/sites-available" ]; then
    # Update main domain only
    find /etc/nginx/sites-available -type f -exec sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" {} + 2>/dev/null || true
    find /etc/nginx/sites-enabled -type f -exec sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" {} + 2>/dev/null || true
    
    # Create simple Nginx config (no mail)
    cat > /etc/nginx/sites-available/phazevpn << EOF
server {
    listen 80;
    server_name $NEW_DOMAIN www.$NEW_DOMAIN;
    
    location / {
        proxy_pass http://localhost:8081;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    ln -sf /etc/nginx/sites-available/phazevpn /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    if nginx -t 2>/dev/null; then
        echo "   ✅ Nginx config updated (email skipped)"
    else
        echo "   ⚠️  Nginx config has errors, check manually"
    fi
fi

echo ""

# Step 3: Update web portal
echo "3️⃣ Updating web portal..."
if [ -d "$VPN_DIR/web-portal" ]; then
    find "$VPN_DIR/web-portal" -type f \( -name "*.py" -o -name "*.html" \) \
        -exec sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" {} + 2>/dev/null || true
    echo "   ✅ Updated web portal"
fi

echo ""

# Step 4: Update hostname
echo "4️⃣ Updating system hostname..."
if command -v hostnamectl &> /dev/null; then
    hostnamectl set-hostname "$NEW_DOMAIN" 2>/dev/null || true
fi

if [ -f "/etc/hosts" ]; then
    sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" /etc/hosts
    echo "   ✅ Updated /etc/hosts"
fi

echo ""

# Summary
echo "=========================================="
echo "✅ Domain Update Complete!"
echo "=========================================="
echo ""
echo "Updated to: $NEW_DOMAIN"
echo ""
echo "Next steps:"
echo "1. Add DNS records in Namecheap:"
echo "   - A record: @ → YOUR_VPS_IP"
echo "   - A record: www → YOUR_VPS_IP"
echo ""
echo "2. Get SSL certificate:"
echo "   certbot --nginx -d $NEW_DOMAIN -d www.$NEW_DOMAIN"
echo ""
echo "3. Restart services:"
echo "   systemctl restart nginx openvpn@server"
echo ""
echo "4. Test:"
echo "   curl https://$NEW_DOMAIN"
echo ""
echo "📧 Email setup skipped - do that later with mail subdomain"
echo ""

