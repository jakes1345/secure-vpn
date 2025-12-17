#!/bin/bash
# Fix Roundcube Webmail Configuration

set -euo pipefail

VPS_ENV_FILE="${VPS_ENV_FILE:-.vps.env}"
if [ -f "$VPS_ENV_FILE" ]; then
    set -a
    source "$VPS_ENV_FILE"
    set +a
fi

VPS_HOST="${VPS_HOST:-phazevpn.com}"
VPS_IP="${VPS_IP:-$VPS_HOST}"
VPS_USER="${VPS_USER:-root}"
SSH_OPTS="${SSH_OPTS:--o StrictHostKeyChecking=no -o ConnectTimeout=10}"

MYSQL_ROOT_PASS="${MYSQL_ROOT_PASS:-}"
if [ -z "$MYSQL_ROOT_PASS" ]; then
    echo "❌ MYSQL_ROOT_PASS is not set. Export it or put it in .vps.env"
    exit 1
fi

require_sshpass_if_needed() {
    if [ -n "${VPS_PASS:-}" ] && ! command -v sshpass &> /dev/null; then
        echo "❌ VPS_PASS is set but sshpass is not installed."
        echo "Install sshpass or use SSH keys (recommended)."
        exit 1
    fi
}

ssh_run() {
    if [ -n "${VPS_PASS:-}" ]; then
        require_sshpass_if_needed
        SSHPASS="$VPS_PASS" sshpass -e ssh $SSH_OPTS "$@"
    else
        ssh $SSH_OPTS "$@"
    fi
}

echo "🔧 Fixing Roundcube Webmail on mail.phazevpn.com..."

ssh_run $VPS_USER@$VPS_IP "MYSQL_ROOT_PASS=$MYSQL_ROOT_PASS bash -s" << 'ENDSSH'

# Create Roundcube config
cat > /usr/share/roundcube/config.inc.php << 'EOF'
<?php
/* Local configuration for Roundcube Webmail */

// Database connection
$config['db_dsnw'] = 'mysql://roundcube:roundcube_pass@localhost/roundcube';

// IMAP/SMTP Settings
$config['default_host'] = 'ssl://mail.phazevpn.com';
$config['default_port'] = 993;
$config['smtp_server'] = 'tls://mail.phazevpn.com';
$config['smtp_port'] = 587;
$config['smtp_user'] = '%u';
$config['smtp_pass'] = '%p';

// Display settings
$config['product_name'] = 'PhazeVPN Mail';
$config['support_url'] = 'https://phazevpn.com/support';
$config['des_key'] = 'phazevpn_secret_key_change_this_in_production';

// Plugins
$config['plugins'] = array('archive', 'zipdownload', 'managesieve');

// Security
$config['enable_installer'] = false;
$config['session_lifetime'] = 30;
$config['ip_check'] = true;

// Misc
$config['language'] = 'en_US';
$config['timezone'] = 'America/Chicago';
EOF

# Set permissions
chown www-data:www-data /usr/share/roundcube/config.inc.php
chmod 640 /usr/share/roundcube/config.inc.php

# Create Roundcube database if it doesn't exist
mysql -u root -p"$MYSQL_ROOT_PASS" << 'SQLEOF'
CREATE DATABASE IF NOT EXISTS roundcube CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'roundcube'@'localhost' IDENTIFIED BY 'roundcube_pass';
GRANT ALL PRIVILEGES ON roundcube.* TO 'roundcube'@'localhost';
FLUSH PRIVILEGES;
SQLEOF

# Import Roundcube schema
mysql -u roundcube -p'roundcube_pass' roundcube < /usr/share/roundcube/SQL/mysql.initial.sql 2>/dev/null || echo "Schema already exists"

# Restart PHP-FPM
systemctl restart php8.1-fpm

# Test nginx config and reload
nginx -t && systemctl reload nginx

echo "✅ Roundcube configuration complete!"
echo "🌐 Access at: https://mail.phazevpn.com"

ENDSSH

echo ""
echo "=========================================="
echo "✅ Webmail Fixed!"
echo "=========================================="
echo ""
echo "Test it now: https://mail.phazevpn.com"
echo ""
echo "Note: You'll need to configure an actual mail server"
echo "(Postfix/Dovecot) for sending/receiving emails."
echo "Roundcube is just the web interface."
