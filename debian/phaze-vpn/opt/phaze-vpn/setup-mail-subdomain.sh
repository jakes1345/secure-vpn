#!/bin/bash
# Setup mail.phazevpn.com subdomain on VPS
# Run this on your VPS (15.204.11.19)

set -e

echo "🔧 Setting up mail.phazevpn.com subdomain..."

# Create mail web directory
sudo mkdir -p /var/www/mail
sudo chown -R www-data:www-data /var/www/mail

# Copy placeholder page (if running from repo)
if [ -f "web-portal/mail-index.html" ]; then
    sudo cp web-portal/mail-index.html /var/www/mail/index.html
    sudo chown www-data:www-data /var/www/mail/index.html
else
    # Create a simple placeholder if file doesn't exist
    sudo tee /var/www/mail/index.html > /dev/null << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>PhazeVPN Email Server</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f0f0f0; }
        .container { background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; }
        h1 { color: #667eea; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📧 PhazeVPN Email Server</h1>
        <p>mail.phazevpn.com</p>
        <p>Email server placeholder page</p>
    </div>
</body>
</html>
EOF
fi

# Update Nginx config
if [ -f "web-portal/nginx-phazevpn.conf" ]; then
    echo "📝 Updating Nginx configuration..."
    sudo cp web-portal/nginx-phazevpn.conf /etc/nginx/sites-available/phazevpn
    sudo ln -sf /etc/nginx/sites-available/phazevpn /etc/nginx/sites-enabled/phazevpn
    
    # Remove old default if it exists
    sudo rm -f /etc/nginx/sites-enabled/default
fi

# Test Nginx config
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx config is valid"
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded"
else
    echo "❌ Nginx config has errors. Please fix them first."
    exit 1
fi

# Get SSL certificate for mail subdomain (if not already done)
echo "🔒 Checking SSL certificate..."
if [ ! -f "/etc/letsencrypt/live/phazevpn.com/fullchain.pem" ]; then
    echo "📜 Requesting SSL certificate for phazevpn.com, www.phazevpn.com, and mail.phazevpn.com..."
    sudo certbot --nginx -d phazevpn.com -d www.phazevpn.com -d mail.phazevpn.com --non-interactive --agree-tos --register-unsafely-without-email || {
        echo "⚠️  SSL certificate request failed. You may need to run it manually:"
        echo "   sudo certbot --nginx -d phazevpn.com -d www.phazevpn.com -d mail.phazevpn.com"
    }
else
    echo "✅ SSL certificate already exists"
    # Make sure mail subdomain is included
    sudo certbot --nginx -d phazevpn.com -d www.phazevpn.com -d mail.phazevpn.com --expand --non-interactive || true
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Test your mail subdomain:"
echo "   curl https://mail.phazevpn.com"
echo "   Or open in browser: https://mail.phazevpn.com"
echo ""
echo "📝 Next steps:"
echo "   1. Install email server (Postfix + Dovecot, or Mail-in-a-Box)"
echo "   2. Configure webmail interface (Roundcube, Rainloop, etc.)"
echo "   3. Update Nginx config to point to your webmail interface"

