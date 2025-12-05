#!/bin/bash
# Complete Production Deployment Setup for PhazeVPN Portal
# This sets up: Gunicorn, Systemd, Nginx, and HTTPS

set -e  # Exit on error

echo "=================================================================================="
echo "🚀 PhazeVPN Portal - Production Deployment Setup"
echo "=================================================================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

BASE_DIR="/opt/phaze-vpn"
WEB_PORTAL_DIR="$BASE_DIR/web-portal"

# Step 1: Install dependencies
echo "1️⃣  Installing dependencies..."
apt-get update
apt-get install -y python3-pip python3-venv nginx certbot python3-certbot-nginx

# Install Python packages
echo "   Installing Python packages..."
cd "$WEB_PORTAL_DIR"
pip3 install -r requirements.txt

echo "   ✅ Dependencies installed"
echo ""

# Step 2: Create systemd service
echo "2️⃣  Setting up systemd service..."
cp "$WEB_PORTAL_DIR/phazevpn-portal.service" /etc/systemd/system/phazevpn-portal.service

# Update paths in service file if needed
sed -i "s|/opt/phaze-vpn|$BASE_DIR|g" /etc/systemd/system/phazevpn-portal.service

systemctl daemon-reload
systemctl enable phazevpn-portal

echo "   ✅ Systemd service created and enabled"
echo ""

# Step 3: Set up Nginx
echo "3️⃣  Setting up Nginx..."
cp "$WEB_PORTAL_DIR/nginx-phazevpn.conf" /etc/nginx/sites-available/phazevpn

# Update paths in nginx config
sed -i "s|/opt/phaze-vpn|$BASE_DIR|g" /etc/nginx/sites-available/phazevpn

# Create symlink
if [ ! -L /etc/nginx/sites-enabled/phazevpn ]; then
    ln -s /etc/nginx/sites-available/phazevpn /etc/nginx/sites-enabled/phazevpn
fi

# Remove default nginx site if it exists
if [ -L /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Test nginx config
nginx -t

echo "   ✅ Nginx configured"
echo ""

# Step 4: Set up HTTPS with Let's Encrypt
echo "4️⃣  Setting up HTTPS with Let's Encrypt..."
echo "   This will request an SSL certificate for phazevpn.duckdns.org"
echo "   Make sure the domain points to this server's IP!"
echo ""
read -p "   Continue with SSL certificate setup? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # First, start nginx with HTTP only (for Let's Encrypt challenge)
    systemctl start nginx
    
    # Get certificate
    certbot --nginx -d phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --redirect
    
    # Reload nginx
    systemctl reload nginx
    
    echo "   ✅ HTTPS certificate installed"
else
    echo "   ⚠️  Skipping SSL certificate setup"
    echo "   You can run this later:"
    echo "   sudo certbot --nginx -d phazevpn.duckdns.org"
fi

echo ""

# Step 5: Start services
echo "5️⃣  Starting services..."
systemctl start phazevpn-portal
systemctl start nginx

echo "   ✅ Services started"
echo ""

# Step 6: Check status
echo "6️⃣  Checking service status..."
echo ""
echo "PhazeVPN Portal:"
systemctl status phazevpn-portal --no-pager -l | head -10

echo ""
echo "Nginx:"
systemctl status nginx --no-pager -l | head -10

echo ""

# Step 7: Firewall setup
echo "7️⃣  Setting up firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 'Nginx Full'
    ufw allow 80/tcp
    ufw allow 443/tcp
    echo "   ✅ Firewall rules added"
else
    echo "   ⚠️  UFW not found - configure firewall manually"
fi

echo ""

# Summary
echo "=================================================================================="
echo "✅ PRODUCTION DEPLOYMENT COMPLETE!"
echo "=================================================================================="
echo ""
echo "📋 Summary:"
echo "   ✅ Gunicorn installed and configured"
echo "   ✅ Systemd service created and enabled"
echo "   ✅ Nginx reverse proxy configured"
echo "   ✅ HTTPS certificate installed (if you chose yes)"
echo "   ✅ Services started"
echo ""
echo "🌐 Your site should be accessible at:"
if [ -f /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem ]; then
    echo "   https://phazevpn.duckdns.org"
else
    echo "   http://phazevpn.duckdns.org (HTTPS pending)"
fi
echo ""
echo "📝 Useful commands:"
echo "   sudo systemctl status phazevpn-portal    # Check portal status"
echo "   sudo systemctl restart phazevpn-portal    # Restart portal"
echo "   sudo journalctl -u phazevpn-portal -f     # View portal logs"
echo "   sudo nginx -t                              # Test nginx config"
echo "   sudo systemctl reload nginx                # Reload nginx"
echo ""
echo "🔒 To enable secure cookies, update app.py:"
echo "   Set HTTPS_ENABLED=true in the systemd service"
echo "   (Already done in the service file!)"
echo ""

