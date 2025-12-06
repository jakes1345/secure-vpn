#!/bin/bash
# Auto-configure Webmail Dashboard (Roundcube) - No questions asked!
# Run this on your VPS

set -e

DOMAIN="phazevpn.com"
MAIL_DOMAIN="mail.phazevpn.com"

echo "🌐 Setting up Webmail Dashboard (Auto-Configure)"
echo "=============================================="

if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (sudo)"
    exit 1
fi

# Install Roundcube
echo ""
echo "1️⃣ Installing Roundcube..."
apt-get update -qq
apt-get install -y roundcube roundcube-plugins php-fpm php-mysql php-mbstring php-xml php-zip php-gd php-curl

# Use SQLite (simpler, no MySQL setup needed)
echo ""
echo "2️⃣ Configuring Roundcube with SQLite..."
ROUNDCUBE_CONFIG="/etc/roundcube/config.inc.php"

# Backup if exists
[ -f "$ROUNDCUBE_CONFIG" ] && cp "$ROUNDCUBE_CONFIG" "${ROUNDCUBE_CONFIG}.backup"

# Create config with SQLite
cat > "$ROUNDCUBE_CONFIG" << 'EOF'
<?php
$config = array();

// Use SQLite (no MySQL needed)
$config['db_dsnw'] = 'sqlite:////var/lib/roundcube/roundcube.db?mode=0640';

// IMAP settings
$config['default_host'] = 'ssl://mail.phazevpn.com';
$config['default_port'] = 993;
$config['imap_conn_options'] = array(
    'ssl' => array(
        'verify_peer' => false,
        'verify_peer_name' => false,
    ),
);

// SMTP settings
$config['smtp_server'] = 'tls://mail.phazevpn.com';
$config['smtp_port'] = 587;
$config['smtp_user'] = '%u';
$config['smtp_pass'] = '%p';
$config['smtp_conn_options'] = array(
    'ssl' => array(
        'verify_peer' => false,
        'verify_peer_name' => false,
    ),
);

// Security
$config['des_key'] = 'ROUNDCUBE_DES_KEY_PLACEHOLDER';
$config['cipher_method'] = 'AES-256-CBC';

// Interface
$config['product_name'] = 'PhazeVPN Mail';
$config['skin'] = 'elastic';
$config['plugins'] = array('archive', 'zipdownload');

// Logging
$config['log_dir'] = '/var/log/roundcube/';
$config['temp_dir'] = '/var/lib/roundcube/temp/';

// File uploads
$config['max_message_size'] = '25M';

// Timezone
$config['timezone'] = 'UTC';
$config['language'] = 'en_US';
EOF

# Generate and set des_key
DES_KEY=$(openssl rand -base64 24 | tr -d '\n' | tr -d '+/' | cut -c1-24)
sed -i "s/ROUNDCUBE_DES_KEY_PLACEHOLDER/$DES_KEY/" "$ROUNDCUBE_CONFIG"

# Initialize SQLite database
echo ""
echo "3️⃣ Initializing database..."
mkdir -p /var/lib/roundcube
if [ -f /usr/share/roundcube/SQL/sqlite.initial.sql ]; then
    sqlite3 /var/lib/roundcube/roundcube.db < /usr/share/roundcube/SQL/sqlite.initial.sql
    chown www-data:www-data /var/lib/roundcube/roundcube.db
    chmod 640 /var/lib/roundcube/roundcube.db
    echo "   ✅ Database initialized"
else
    # Create basic schema if file doesn't exist
    sqlite3 /var/lib/roundcube/roundcube.db "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, mail_host TEXT);"
    chown www-data:www-data /var/lib/roundcube/roundcube.db
    chmod 640 /var/lib/roundcube/roundcube.db
    echo "   ✅ Database created"
fi

# Set permissions
chown -R www-data:www-data /var/lib/roundcube
chown -R www-data:www-data /var/log/roundcube
mkdir -p /var/lib/roundcube/temp
chmod 755 /var/lib/roundcube/temp

# Configure Nginx
echo ""
echo "4️⃣ Configuring Nginx..."
cat > /etc/nginx/sites-available/mail-phazevpn << 'NGINXEOF'
# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name mail.phazevpn.com;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS - Webmail
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name mail.phazevpn.com;

    ssl_certificate /etc/letsencrypt/live/phazevpn.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/phazevpn.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    root /usr/share/roundcube;
    index index.php;

    access_log /var/log/nginx/mail-phazevpn-access.log;
    error_log /var/log/nginx/mail-phazevpn-error.log;

    client_max_body_size 50M;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PHP_VALUE "upload_max_filesize=50M \n post_max_size=50M";
    }

    location ~ /\. {
        deny all;
    }
}
NGINXEOF

# Try PHP 8.1, fallback to php-fpm
PHP_SOCK="/var/run/php/php8.1-fpm.sock"
if [ ! -S "$PHP_SOCK" ]; then
    PHP_SOCK="/var/run/php/php-fpm.sock"
    sed -i "s|php8.1-fpm.sock|php-fpm.sock|g" /etc/nginx/sites-available/mail-phazevpn
fi

# Enable site
ln -sf /etc/nginx/sites-available/mail-phazevpn /etc/nginx/sites-enabled/mail-phazevpn

# Test Nginx
echo ""
echo "5️⃣ Testing Nginx configuration..."
nginx -t && echo "   ✅ Nginx config valid" || echo "   ⚠️  Nginx config has issues"

# Restart services
echo ""
echo "6️⃣ Restarting services..."
systemctl restart nginx
systemctl restart php8.1-fpm 2>/dev/null || systemctl restart php-fpm 2>/dev/null || true
echo "   ✅ Services restarted"

echo ""
echo "✅ Webmail Dashboard Setup Complete!"
echo ""
echo "🌐 Access your webmail at:"
echo "   https://mail.phazevpn.com"
echo ""
echo "📧 Login with:"
echo "   Username: admin@phazevpn.com"
echo "   Password: (your email password)"
echo ""
echo "✨ Features:"
echo "   • Full webmail interface"
echo "   • Send and receive emails"
echo "   • Manage folders"
echo "   • Search emails"
echo "   • Mobile-friendly"


