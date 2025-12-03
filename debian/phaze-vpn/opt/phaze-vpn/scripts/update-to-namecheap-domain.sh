#!/bin/bash
# Update all configs from phazevpn.duckdns.org to phazevpn.com

set -e

OLD_DOMAIN="phazevpn.duckdns.org"
NEW_DOMAIN="phazevpn.com"
VPN_DIR="/opt/secure-vpn"

echo "=========================================="
echo "🌐 Updating Domain: $OLD_DOMAIN → $NEW_DOMAIN"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (sudo $0)"
    exit 1
fi

# Step 1: Update VPN configs
echo "1️⃣ Updating VPN configuration files..."
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
    find client-configs -type f -name "*.ovpn" -exec sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" {} +
    echo "   ✅ Updated client configs"
fi

# Update PhazeVPN protocol configs
if [ -d "phazevpn-protocol" ]; then
    find phazevpn-protocol -type f \( -name "*.py" -o -name "*.json" \) -exec sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" {} + 2>/dev/null || true
    echo "   ✅ Updated PhazeVPN protocol configs"
fi

echo ""

# Step 2: Update email configs
echo "2️⃣ Updating email server configuration..."

# Postfix
if [ -f "/etc/postfix/main.cf" ]; then
    sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" /etc/postfix/main.cf
    echo "   ✅ Updated Postfix config"
fi

# Dovecot
if [ -f "/etc/dovecot/dovecot.conf" ]; then
    sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" /etc/dovecot/dovecot.conf
    echo "   ✅ Updated Dovecot config"
fi

# Update hostname in Postfix
if [ -f "/etc/postfix/main.cf" ]; then
    sed -i "s|^myhostname =.*|myhostname = mail.$NEW_DOMAIN|" /etc/postfix/main.cf
    sed -i "s|^mydomain =.*|mydomain = $NEW_DOMAIN|" /etc/postfix/main.cf
fi

echo ""

# Step 3: Update web server configs
echo "3️⃣ Updating web server configuration..."

# Nginx
if [ -d "/etc/nginx/sites-available" ]; then
    find /etc/nginx/sites-available -type f -exec sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" {} + 2>/dev/null || true
    find /etc/nginx/sites-enabled -type f -exec sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" {} + 2>/dev/null || true
    echo "   ✅ Updated Nginx configs"
    
    # Test Nginx config
    if nginx -t 2>/dev/null; then
        echo "   ✅ Nginx config is valid"
    else
        echo "   ⚠️  Nginx config has errors, check manually"
    fi
fi

echo ""

# Step 4: Update web portal configs
echo "4️⃣ Updating web portal configuration..."

if [ -d "$VPN_DIR/web-portal" ]; then
    find "$VPN_DIR/web-portal" -type f \( -name "*.py" -o -name "*.html" -o -name "*.json" \) \
        -exec sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" {} + 2>/dev/null || true
    echo "   ✅ Updated web portal configs"
fi

echo ""

# Step 5: Update deployment scripts
echo "5️⃣ Updating deployment scripts..."

if [ -d "$VPN_DIR" ]; then
    find "$VPN_DIR" -type f \( -name "*.sh" -o -name "*.py" \) \
        -exec sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" {} + 2>/dev/null || true
    echo "   ✅ Updated deployment scripts"
fi

echo ""

# Step 6: Update system hostname (optional)
echo "6️⃣ Updating system hostname..."

if command -v hostnamectl &> /dev/null; then
    hostnamectl set-hostname "$NEW_DOMAIN" 2>/dev/null || true
    echo "   ✅ Updated system hostname"
fi

# Update /etc/hosts
if [ -f "/etc/hosts" ]; then
    sed -i "s|$OLD_DOMAIN|$NEW_DOMAIN|g" /etc/hosts
    echo "   ✅ Updated /etc/hosts"
fi

echo ""

# Step 7: Summary
echo "=========================================="
echo "✅ Domain Update Complete!"
echo "=========================================="
echo ""
echo "Updated from: $OLD_DOMAIN"
echo "Updated to:   $NEW_DOMAIN"
echo ""
echo "Files updated:"
echo "  ✅ VPN configs"
echo "  ✅ Email configs (Postfix/Dovecot)"
echo "  ✅ Web server configs (Nginx)"
echo "  ✅ Web portal configs"
echo "  ✅ Deployment scripts"
echo ""
echo "Next steps:"
echo "1. Configure DNS records in Namecheap (see NAMECHEAP-DOMAIN-SETUP.md)"
echo "2. Request SSL certificates:"
echo "   certbot --nginx -d $NEW_DOMAIN -d www.$NEW_DOMAIN -d mail.$NEW_DOMAIN"
echo "3. Restart services:"
echo "   systemctl restart postfix dovecot nginx"
echo "   systemctl restart openvpn@server"
echo "   systemctl restart phazevpn-protocol"
echo "4. Regenerate client configs:"
echo "   cd $VPN_DIR && python3 vpn-manager.py add-client CLIENT_NAME"
echo ""
echo "Don't forget to:"
echo "  - Add DNS A records in Namecheap"
echo "  - Add MX record for email"
echo "  - Add SPF/DKIM/DMARC records for email"
echo ""

