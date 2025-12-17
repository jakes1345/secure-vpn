#!/bin/bash
#
# PhazeVPN Webmail Setup (Roundcube)
# Install and configure Roundcube webmail interface
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load config
if [ ! -f /etc/phazevpn-email-db.conf ]; then
    echo -e "${RED}❌ Email server not configured. Run setup-email-server.sh first.${NC}"
    exit 1
fi

source /etc/phazevpn-email-db.conf

DOMAIN="${EMAIL_DOMAIN:-phazevpn.duckdns.org}"
WEBMAIL_DIR="/var/www/webmail"
ROUNDCUBE_VERSION="1.6.6"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           PhazeVPN Webmail Setup (Roundcube)                 ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root (sudo)${NC}"
    exit 1
fi

# Install PHP dependencies
echo -e "${BLUE}[1/5]${NC} Installing PHP dependencies..."
apt update -qq
apt install -y php php-fpm php-mysql php-mbstring php-xml php-curl php-zip php-gd php-imagick

# Download Roundcube
echo -e "${BLUE}[2/5]${NC} Downloading Roundcube..."
cd /tmp
if [ -d roundcubemail-${ROUNDCUBE_VERSION} ]; then
    rm -rf roundcubemail-${ROUNDCUBE_VERSION}
fi

wget -q https://github.com/roundcube/roundcubemail/releases/download/${ROUNDCUBE_VERSION}/roundcubemail-${ROUNDCUBE_VERSION}-complete.tar.gz
tar -xzf roundcubemail-${ROUNDCUBE_VERSION}-complete.tar.gz
rm roundcubemail-${ROUNDCUBE_VERSION}-complete.tar.gz

# Install Roundcube
echo -e "${BLUE}[3/5]${NC} Installing Roundcube..."
mkdir -p ${WEBMAIL_DIR}
mv roundcubemail-${ROUNDCUBE_VERSION}/* ${WEBMAIL_DIR}/
chown -R www-data:www-data ${WEBMAIL_DIR}
chmod -R 755 ${WEBMAIL_DIR}

# Create database
echo -e "${BLUE}[4/5]${NC} Setting up database..."
MYSQL_ROOT_PASS=$(cat /root/.mysql_root_password 2>/dev/null || echo "")

if [ -z "$MYSQL_ROOT_PASS" ]; then
    echo -e "${YELLOW}⚠️  MySQL root password not found. Please enter it:${NC}"
    read -sp "MySQL root password: " MYSQL_ROOT_PASS
    echo ""
fi

mysql -u root -p"${MYSQL_ROOT_PASS}" <<EOF
CREATE DATABASE IF NOT EXISTS roundcube;
GRANT ALL PRIVILEGES ON roundcube.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
EOF

# Import Roundcube database schema
mysql -u root -p"${MYSQL_ROOT_PASS}" roundcube < ${WEBMAIL_DIR}/SQL/mysql.initial.sql

# Configure Roundcube
echo -e "${BLUE}[5/5]${NC} Configuring Roundcube..."
cat > ${WEBMAIL_DIR}/config/config.inc.php <<EOF
<?php
\$config = array();

// Database
\$config['db_dsnw'] = 'mysql://${DB_USER}:${DB_PASS}@localhost/roundcube';

// IMAP settings
\$config['default_host'] = 'localhost';
\$config['default_port'] = 143;
\$config['imap_conn_options'] = array(
    'ssl' => array(
        'verify_peer' => false,
        'verify_peer_name' => false,
    ),
);

// SMTP settings
\$config['smtp_server'] = 'localhost';
\$config['smtp_port'] = 587;
\$config['smtp_user'] = '%u';
\$config['smtp_pass'] = '%p';
\$config['smtp_conn_options'] = array(
    'ssl' => array(
        'verify_peer' => false,
        'verify_peer_name' => false,
    ),
);

// Security
\$config['des_key'] = '$(openssl rand -base64 24)';
\$config['cipher_method'] = 'AES-256-CBC';

// Language
\$config['language'] = 'en_US';

// Skin
\$config['skin'] = 'elastic';

// Plugins
\$config['plugins'] = array('archive', 'zipdownload');

// Logging
\$config['log_dir'] = '/var/log/roundcube/';
\$config['temp_dir'] = '/tmp/roundcube-temp/';

// Session
\$config['session_lifetime'] = 10;
\$config['ip_check'] = false;

// Product name
\$config['product_name'] = 'PhazeVPN Webmail';
EOF

# Create directories
mkdir -p /var/log/roundcube /tmp/roundcube-temp
chown -R www-data:www-data /var/log/roundcube /tmp/roundcube-temp

# Configure Nginx
echo -e "${YELLOW}Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/webmail <<EOF
server {
    listen 80;
    server_name webmail.${DOMAIN};
    
    root ${WEBMAIL_DIR};
    index index.php;
    
    access_log /var/log/nginx/webmail-access.log;
    error_log /var/log/nginx/webmail-error.log;
    
    location / {
        try_files \$uri \$uri/ /index.php?\$query_string;
    }
    
    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php-fpm.sock;
        fastcgi_param SCRIPT_FILENAME \$document_root\$fastcgi_script_name;
        include fastcgi_params;
    }
    
    location ~ /\. {
        deny all;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/webmail /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo ""
echo -e "${GREEN}✅ Webmail installation complete!${NC}"
echo ""
echo -e "${YELLOW}Access your webmail at:${NC}"
echo -e "  ${GREEN}http://webmail.${DOMAIN}${NC}"
echo ""
echo -e "${YELLOW}Login with your email account:${NC}"
echo -e "  Email: your-email@${DOMAIN}"
echo -e "  Password: (your email password)"
echo ""
echo -e "${YELLOW}Note:${NC} You may need to configure DNS for webmail.${DOMAIN} or use your main domain"

