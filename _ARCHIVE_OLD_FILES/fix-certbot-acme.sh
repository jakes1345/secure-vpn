#!/bin/bash
# Fix Let's Encrypt ACME challenge directory

echo "=========================================="
echo "🔧 Fixing Let's Encrypt ACME Challenge"
echo "=========================================="
echo ""

# Create directory
echo "Creating .well-known directory..."
sudo mkdir -p /var/www/html/.well-known/acme-challenge
sudo chown -R www-data:www-data /var/www/html/.well-known
sudo chmod -R 755 /var/www/html/.well-known

# Test nginx config
echo ""
echo "Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx config is valid"
    echo ""
    echo "Reloading nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded"
else
    echo "❌ Nginx config has errors!"
    exit 1
fi

# Test ACME challenge
echo ""
echo "Testing ACME challenge path..."
echo "test" | sudo tee /var/www/html/.well-known/acme-challenge/test > /dev/null
RESULT=$(curl -s http://localhost/.well-known/acme-challenge/test)

if [ "$RESULT" = "test" ]; then
    echo "✅ ACME challenge path is accessible!"
else
    echo "❌ ACME challenge path not accessible"
    echo "Result: $RESULT"
fi

# Clean up test file
sudo rm -f /var/www/html/.well-known/acme-challenge/test

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Now try certbot again:"
echo "  sudo certbot --nginx -d phazevpn.duckdns.org"
echo ""

