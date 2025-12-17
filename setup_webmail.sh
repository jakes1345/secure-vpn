#!/bin/bash
# PhazeVPN Webmail Installer (Roundcube)

DB_PASS="Jakes1328!@"
DOMAIN="phazevpn.com"

echo "📧 Installing Roundcube Webmail..."

# 1. Install Dependencies
apt-get update
apt-get install -y roundcube roundcube-mysql roundcube-plugins php-net-ldap3 php-net-sieve

# 2. Configure Database
# (The apt install should prompt, but we can configure manually if needed)
# We assume dbconfig-common handled it, but let's double check config
if [ ! -f /etc/roundcube/config.inc.php ]; then
    cp /etc/roundcube/config.inc.php.sample /etc/roundcube/config.inc.php
fi

# 3. Configure Nginx
cat > /etc/nginx/sites-available/webmail << EOF
server {
    listen 80;
    server_name mail.$DOMAIN;

    root /var/lib/roundcube;
    index index.php index.html;

    location / {
        try_files \$uri \$uri/ /index.php?\$query_string;
    }

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
    }

    location ~ ^/(README|INSTALL|LICENSE|CHANGELOG|UPGRADING)$ {
        deny all;
    }
    location ~ ^/(bin|SQL)/ {
        deny all;
    }
    location ~ /\. {
        deny all;
    }
}
EOF

# Link it
ln -sf /etc/nginx/sites-available/webmail /etc/nginx/sites-enabled/webmail

# 4. Enable plugins (Markasjunk, zipdownload)
# sed -i "s/\$config\['plugins'\] = array(/\$config\['plugins'\] = array('archive', 'zipdownload', 'markasjunk',/" /etc/roundcube/config.inc.php

# 5. Restart Services
systemctl restart nginx
systemctl restart php*-fpm

echo "✅ Webmail Installed at http://mail.$DOMAIN"
echo "⚠️  Ensure DNS 'mail.$DOMAIN' points to this IP!"
