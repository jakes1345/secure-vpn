#!/bin/bash
# Setup Webmail Dashboard (Roundcube) for mail.phazevpn.com
# Run this on your VPS

set -e

DOMAIN="phazevpn.com"
MAIL_DOMAIN="mail.phazevpn.com"

echo "🌐 Setting up Webmail Dashboard"
echo "=============================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (sudo)"
    exit 1
fi

# Install Roundcube
echo ""
echo "1️⃣ Installing Roundcube webmail..."
apt-get update
apt-get install -y roundcube roundcube-mysql roundcube-plugins

# Configure Roundcube database
echo ""
echo "2️⃣ Setting up Roundcube database..."
# Check if MySQL/MariaDB is running
if systemctl is-active --quiet mysql || systemctl is-active --quiet mariadb; then
    DB_ROOT_PASS=""
    read -sp "Enter MySQL root password (or press Enter if none): " DB_ROOT_PASS
    echo ""
    
    # Create database and user
    mysql -u root ${DB_ROOT_PASS:+-p$DB_ROOT_PASS} <<EOF
CREATE DATABASE IF NOT EXISTS roundcube;
CREATE USER IF NOT EXISTS 'roundcube'@'localhost' IDENTIFIED BY 'roundcube_password_change_me';
GRANT ALL PRIVILEGES ON roundcube.* TO 'roundcube'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    # Initialize Roundcube database
    if [ -f /usr/share/roundcube/SQL/mysql.initial.sql ]; then
        mysql -u roundcube -proundcube_password_change_me roundcube < /usr/share/roundcube/SQL/mysql.initial.sql
        echo "   ✅ Database initialized"
    fi
else
    echo "   ⚠️  MySQL/MariaDB not running. Using SQLite instead."
    # Roundcube will use SQLite by default if MySQL not configured
fi

# Configure Roundcube
echo ""
echo "3️⃣ Configuring Roundcube..."
ROUNDCUBE_CONFIG="/etc/roundcube/config.inc.php"

# Backup original config
if [ -f "$ROUNDCUBE_CONFIG" ]; then
    cp "$ROUNDCUBE_CONFIG" "${ROUNDCUBE_CONFIG}.backup"
fi

# Update config for our domain
cat > "$ROUNDCUBE_CONFIG" << 'EOF'
<?php
$config = array();

// Database
$config['db_dsnw'] = 'mysql://roundcube:roundcube_password_change_me@localhost/roundcube';

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
$config['des_key'] = '$(openssl rand -base64 24)';
$config['cipher_method'] = 'AES-256-CBC';

// Interface
$config['product_name'] = 'PhazeVPN Mail';
$config['skin'] = 'elastic';
$config['plugins'] = array('archive', 'zipdownload', 'managesieve');

// Logging
$config['log_dir'] = '/var/log/roundcube/';
$config['temp_dir'] = '/var/lib/roundcube/temp/';

// File uploads
$config['max_message_size'] = '25M';

// Timezone
$config['timezone'] = 'UTC';

// Language
$config['language'] = 'en_US';
EOF

# Generate des_key
DES_KEY=$(openssl rand -base64 24 | tr -d '\n')
sed -i "s/\$(openssl rand -base64 24)/$DES_KEY/" "$ROUNDCUBE_CONFIG"

# Set permissions
chown -R www-data:www-data /var/lib/roundcube
chown -R www-data:www-data /var/log/roundcube
chmod 755 /var/lib/roundcube/temp

# Configure Nginx for Roundcube
echo ""
echo "4️⃣ Configuring Nginx for webmail..."
NGINX_CONFIG="/etc/nginx/sites-available/phazevpn"

# Check if config exists
if [ -f "$NGINX_CONFIG" ]; then
    # Update mail subdomain to serve Roundcube
    if grep -q "mail.phazevpn.com" "$NGINX_CONFIG"; then
        # Create separate config for mail
        cat > /etc/nginx/sites-available/mail-phazevpn << 'NGINXEOF'
# HTTP to HTTPS redirect for mail subdomain
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

# HTTPS server for mail subdomain (Roundcube)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name mail.phazevpn.com;

    ssl_certificate /etc/letsencrypt/live/phazevpn.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/phazevpn.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    root /var/lib/roundcube;
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

        # Enable the site
        ln -sf /etc/nginx/sites-available/mail-phazevpn /etc/nginx/sites-enabled/mail-phazevpn
        echo "   ✅ Nginx config created"
    fi
else
    echo "   ⚠️  Main Nginx config not found. Creating mail config anyway..."
    # Create the config file as above
fi

# Test Nginx config
echo ""
echo "5️⃣ Testing Nginx configuration..."
nginx -t && echo "   ✅ Nginx config is valid" || echo "   ❌ Nginx config has errors"

# Restart services
echo ""
echo "6️⃣ Restarting services..."
systemctl restart nginx
systemctl restart php8.1-fpm 2>/dev/null || systemctl restart php-fpm
echo "   ✅ Services restarted"

# Create admin info page
echo ""
echo "7️⃣ Creating admin info page..."
mkdir -p /var/www/mail
cat > /var/www/mail/index.html << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhazeVPN Email - Webmail Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 3rem;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }
        h1 { color: #667eea; margin-bottom: 1rem; }
        .login-btn {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 1rem 2rem;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            margin: 1rem 0;
            transition: background 0.3s;
        }
        .login-btn:hover { background: #5568d3; }
        .info-box {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 1.5rem;
            margin: 2rem 0;
            text-align: left;
            border-radius: 5px;
        }
        .info-box h2 {
            color: #667eea;
            margin-bottom: 1rem;
            font-size: 1.2rem;
        }
        .info-box ul {
            list-style: none;
            padding-left: 0;
        }
        .info-box li {
            padding: 0.5rem 0;
            color: #555;
        }
        .info-box li:before {
            content: "✓ ";
            color: #28a745;
            font-weight: bold;
            margin-right: 0.5rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📧 PhazeVPN Email</h1>
        <p>Webmail Access</p>
        
        <a href="/webmail" class="login-btn">Login to Webmail</a>
        
        <div class="info-box">
            <h2>Email Server Information</h2>
            <ul>
                <li>Webmail: <a href="/webmail">mail.phazevpn.com/webmail</a></li>
                <li>SMTP: mail.phazevpn.com:587 (STARTTLS)</li>
                <li>IMAP: mail.phazevpn.com:993 (SSL)</li>
                <li>Domain: phazevpn.com</li>
            </ul>
        </div>
        
        <div class="info-box">
            <h2>Email Client Settings</h2>
            <ul>
                <li>Username: your-email@phazevpn.com</li>
                <li>Password: (your email password)</li>
                <li>Use SSL/TLS for all connections</li>
            </ul>
        </div>
    </div>
</body>
</html>
HTMLEOF

chown -R www-data:www-data /var/www/mail

echo ""
echo "✅ Webmail Dashboard Setup Complete!"
echo ""
echo "🌐 Access your webmail at:"
echo "   https://mail.phazevpn.com/webmail"
echo ""
echo "📋 Login with:"
echo "   Username: admin@phazevpn.com"
echo "   Password: (your email password)"
echo ""
echo "📝 Note: If you see a database error, you may need to:"
echo "   1. Set MySQL root password"
echo "   2. Update /etc/roundcube/config.inc.php with correct database credentials"
echo "   3. Or use SQLite (remove db_dsnw line from config)"


