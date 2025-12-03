#!/bin/bash
#
# PhazeVPN Email Server Setup
# Complete email server installation with Postfix, Dovecot, SpamAssassin, ClamAV, and Roundcube
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="${EMAIL_DOMAIN:-phazevpn.duckdns.org}"
HOSTNAME="${EMAIL_HOSTNAME:-mail.phazevpn.duckdns.org}"
EMAIL_DIR="/var/mail/vhosts"
DB_NAME="phazevpn_email"
DB_USER="phazevpn_email"
DB_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     PhazeVPN Email Server Setup - Complete Installation     ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Domain: ${GREEN}${DOMAIN}${NC}"
echo -e "  Hostname: ${GREEN}${HOSTNAME}${NC}"
echo -e "  Mail Directory: ${GREEN}${EMAIL_DIR}${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root (sudo)${NC}"
    exit 1
fi

# Update system
echo -e "${BLUE}[1/10]${NC} Updating system packages..."
apt update -qq
apt upgrade -y -qq

# Install required packages
echo -e "${BLUE}[2/10]${NC} Installing email server packages..."
export DEBIAN_FRONTEND=noninteractive

apt install -y \
    postfix \
    postfix-mysql \
    dovecot-core \
    dovecot-imapd \
    dovecot-pop3d \
    dovecot-lmtpd \
    dovecot-mysql \
    mysql-server \
    spamassassin \
    spamc \
    clamav \
    clamav-daemon \
    amavisd-new \
    libnet-dns-perl \
    libmail-spf-perl \
    pyzor \
    razor \
    opendkim \
    opendkim-tools \
    fail2ban \
    curl \
    wget \
    unzip \
    php \
    php-fpm \
    php-mysql \
    php-mbstring \
    php-xml \
    php-curl \
    php-zip \
    php-gd \
    php-imagick \
    nginx

# Stop services for configuration
systemctl stop postfix dovecot amavis spamassassin || true

# Create mail directory structure
echo -e "${BLUE}[3/10]${NC} Creating mail directory structure..."
mkdir -p ${EMAIL_DIR}/${DOMAIN}
groupadd -f vmail
useradd -g vmail -u 5000 -d ${EMAIL_DIR} -s /sbin/nologin -c "Virtual Mailbox" vmail || true
chown -R vmail:vmail ${EMAIL_DIR}
chmod -R 770 ${EMAIL_DIR}

# Setup MySQL database
echo -e "${BLUE}[4/10]${NC} Setting up MySQL database..."
systemctl start mysql
systemctl enable mysql

# Generate secure MySQL root password if not set
if [ ! -f /root/.mysql_root_password ]; then
    MYSQL_ROOT_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    echo "$MYSQL_ROOT_PASS" > /root/.mysql_root_password
    chmod 600 /root/.mysql_root_password
    
    # Set MySQL root password
    mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${MYSQL_ROOT_PASS}';" 2>/dev/null || \
    mysql -e "UPDATE mysql.user SET authentication_string=PASSWORD('${MYSQL_ROOT_PASS}') WHERE User='root';" 2>/dev/null || \
    mysqladmin -u root password "${MYSQL_ROOT_PASS}" 2>/dev/null || true
fi

MYSQL_ROOT_PASS=$(cat /root/.mysql_root_password)

# Create database and user
mysql -u root -p"${MYSQL_ROOT_PASS}" <<EOF
CREATE DATABASE IF NOT EXISTS ${DB_NAME};
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
EOF

# Create database tables
mysql -u root -p"${MYSQL_ROOT_PASS}" ${DB_NAME} <<EOF
CREATE TABLE IF NOT EXISTS virtual_domains (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(50) NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS virtual_users (
  id int(11) NOT NULL AUTO_INCREMENT,
  domain_id int(11) NOT NULL,
  password varchar(106) NOT NULL,
  email varchar(120) NOT NULL,
  quota bigint(20) DEFAULT 1073741824,
  PRIMARY KEY (id),
  UNIQUE KEY email (email),
  KEY domain_id (domain_id),
  FOREIGN KEY (domain_id) REFERENCES virtual_domains(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS virtual_aliases (
  id int(11) NOT NULL AUTO_INCREMENT,
  domain_id int(11) NOT NULL,
  source varchar(100) NOT NULL,
  destination varchar(100) NOT NULL,
  PRIMARY KEY (id),
  KEY domain_id (domain_id),
  FOREIGN KEY (domain_id) REFERENCES virtual_domains(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO virtual_domains (name) VALUES ('${DOMAIN}');
EOF

# Save database credentials
cat > /etc/phazevpn-email-db.conf <<EOF
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASS=${DB_PASS}
DOMAIN=${DOMAIN}
HOSTNAME=${HOSTNAME}
EOF
chmod 600 /etc/phazevpn-email-db.conf

echo -e "${GREEN}✅ Database created${NC}"
echo -e "${YELLOW}   Database credentials saved to: /etc/phazevpn-email-db.conf${NC}"

# Configure Postfix
echo -e "${BLUE}[5/10]${NC} Configuring Postfix..."
cp /etc/postfix/main.cf /etc/postfix/main.cf.backup

cat > /etc/postfix/main.cf <<EOF
# PhazeVPN Email Server - Postfix Configuration
smtpd_banner = \$myhostname ESMTP \$mail_name
biff = no
append_dot_mydomain = no
readme_directory = no
compatibility_level = 2

# TLS parameters
smtpd_tls_cert_file=/etc/ssl/certs/ssl-cert-snakeoil.pem
smtpd_tls_key_file=/etc/ssl/private/ssl-cert-snakeoil.key
smtpd_use_tls=yes
smtpd_tls_auth_only = yes
smtp_tls_security_level = may
smtpd_tls_security_level = may
smtpd_tls_protocols = !SSLv2, !SSLv3
smtpd_tls_ciphers = high
smtpd_tls_exclude_ciphers = aNULL, MD5, DES, ADH, RC4, PSD, SRP, 3DES, eNULL
smtpd_tls_dh1024_param_file = /etc/ssl/private/dhparams.pem
smtpd_tls_mandatory_protocols = !SSLv2, !SSLv3
smtpd_tls_mandatory_ciphers = high

# Network settings
myhostname = ${HOSTNAME}
mydomain = ${DOMAIN}
myorigin = \$mydomain
inet_interfaces = all
inet_protocols = ipv4
mydestination = localhost

# Virtual mailbox settings
virtual_transport = lmtp:unix:private/dovecot-lmtp
virtual_mailbox_domains = mysql:/etc/postfix/mysql-virtual-mailbox-domains.cf
virtual_mailbox_maps = mysql:/etc/postfix/mysql-virtual-mailbox-maps.cf
virtual_alias_maps = mysql:/etc/postfix/mysql-virtual-alias-maps.cf

# Security settings
smtpd_helo_required = yes
smtpd_helo_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_invalid_helo_hostname, reject_non_fqdn_helo_hostname, warn_if_reject reject_rbl_client zen.spamhaus.org, permit
smtpd_recipient_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_unauth_destination, reject_non_fqdn_recipient, reject_unknown_recipient_domain, reject_rbl_client zen.spamhaus.org, permit
smtpd_sender_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_non_fqdn_sender, reject_unknown_sender_domain, permit
smtpd_client_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_rbl_client zen.spamhaus.org, permit

# SASL authentication
smtpd_sasl_type = dovecot
smtpd_sasl_path = private/auth
smtpd_sasl_auth_enable = yes
smtpd_sasl_security_options = noanonymous
smtpd_sasl_local_domain = \$myhostname

# Mailbox settings
mailbox_size_limit = 0
message_size_limit = 10240000
virtual_minimum_uid = 100
virtual_uid_maps = static:5000
virtual_gid_maps = static:5000

# Performance
default_process_limit = 100
smtpd_client_connection_count_limit = 10
smtpd_client_connection_rate_limit = 30
queue_minfree = 20971520
header_size_limit = 51200
EOF

# Create Postfix MySQL maps
cat > /etc/postfix/mysql-virtual-mailbox-domains.cf <<EOF
user = ${DB_USER}
password = ${DB_PASS}
hosts = 127.0.0.1
dbname = ${DB_NAME}
query = SELECT 1 FROM virtual_domains WHERE name='%s'
EOF

cat > /etc/postfix/mysql-virtual-mailbox-maps.cf <<EOF
user = ${DB_USER}
password = ${DB_PASS}
hosts = 127.0.0.1
dbname = ${DB_NAME}
query = SELECT 1 FROM virtual_users WHERE email='%s'
EOF

cat > /etc/postfix/mysql-virtual-alias-maps.cf <<EOF
user = ${DB_USER}
password = ${DB_PASS}
hosts = 127.0.0.1
dbname = ${DB_NAME}
query = SELECT destination FROM virtual_aliases WHERE source='%s'
EOF

chmod 600 /etc/postfix/mysql-virtual-*.cf

# Configure master.cf for submission
sed -i '/^#submission/,/^$/s/^#//' /etc/postfix/master.cf
sed -i '/^#smtps/,/^$/s/^#//' /etc/postfix/master.cf

# Configure Dovecot
echo -e "${BLUE}[6/10]${NC} Configuring Dovecot..."
cp /etc/dovecot/dovecot.conf /etc/dovecot/dovecot.conf.backup

cat > /etc/dovecot/dovecot.conf <<EOF
# PhazeVPN Email Server - Dovecot Configuration
protocols = imap pop3 lmtp
listen = *, ::

# Mail location
mail_location = maildir:${EMAIL_DIR}/%d/%n

# User/group
mail_uid = vmail
mail_gid = vmail

# Authentication
disable_plaintext_auth = yes
auth_mechanisms = plain login

# MySQL authentication
passdb {
  driver = sql
  args = /etc/dovecot/dovecot-sql.conf.ext
}

userdb {
  driver = static
  args = uid=vmail gid=vmail home=${EMAIL_DIR}/%d/%n
}

# SSL/TLS
ssl = required
ssl_cert = </etc/ssl/certs/ssl-cert-snakeoil.pem
ssl_key = </etc/ssl/private/ssl-cert-snakeoil.key
ssl_protocols = !SSLv2 !SSLv3
ssl_cipher_list = ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384

# IMAP settings
protocol imap {
  mail_plugins = \$mail_plugins
}

# POP3 settings
protocol pop3 {
  mail_plugins = \$mail_plugins
  pop3_uidl_format = %08Xu%08Xv
}

# LMTP settings
protocol lmtp {
  mail_plugins = \$mail_plugins
}

# Logging
log_path = /var/log/dovecot.log
info_log_path = /var/log/dovecot-info.log
debug_log_path = /var/log/dovecot-debug.log
EOF

# Create Dovecot SQL config
cat > /etc/dovecot/dovecot-sql.conf.ext <<EOF
driver = mysql
connect = host=127.0.0.1 dbname=${DB_NAME} user=${DB_USER} password=${DB_PASS}
default_pass_scheme = SHA512-CRYPT
password_query = SELECT email as user, password FROM virtual_users WHERE email='%u';
EOF

chmod 600 /etc/dovecot/dovecot-sql.conf.ext

# Configure SpamAssassin
echo -e "${BLUE}[7/10]${NC} Configuring SpamAssassin..."
sed -i 's/^ENABLED=0/ENABLED=1/' /etc/default/spamassassin
sed -i 's/^CRON=0/CRON=1/' /etc/default/spamassassin

# Update ClamAV database
echo -e "${BLUE}[8/10]${NC} Updating ClamAV database..."
freshclam || true

# Configure Amavis
echo -e "${BLUE}[9/10]${NC} Configuring Amavis..."
usermod -a -G amavis clamav || true

# Generate SSL certificates (self-signed for now)
echo -e "${BLUE}[10/10]${NC} Generating SSL certificates..."
if [ ! -f /etc/ssl/private/dhparams.pem ]; then
    openssl dhparam -out /etc/ssl/private/dhparams.pem 2048
fi

# Open firewall ports
echo -e "${YELLOW}Opening firewall ports...${NC}"
ufw allow 25/tcp comment 'SMTP'
ufw allow 587/tcp comment 'SMTP Submission'
ufw allow 465/tcp comment 'SMTPS'
ufw allow 143/tcp comment 'IMAP'
ufw allow 993/tcp comment 'IMAPS'
ufw allow 110/tcp comment 'POP3'
ufw allow 995/tcp comment 'POP3S'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Start and enable services
echo -e "${YELLOW}Starting services...${NC}"
systemctl enable postfix dovecot spamassassin clamav-daemon amavis mysql
systemctl start postfix dovecot spamassassin clamav-daemon amavis mysql

# Wait for services to start
sleep 3

# Check service status
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Installation Complete!                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Service status check
check_service() {
    if systemctl is-active --quiet $1; then
        echo -e "  ${GREEN}✅${NC} $1 is running"
    else
        echo -e "  ${RED}❌${NC} $1 is not running"
    fi
}

echo -e "${YELLOW}Service Status:${NC}"
check_service postfix
check_service dovecot
check_service spamassassin
check_service clamav-daemon
check_service amavis
check_service mysql

echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Configure DNS records (see DNS-SETUP.md)"
echo -e "  2. Create email accounts: ${GREEN}./manage-email-accounts.sh add user@${DOMAIN}${NC}"
echo -e "  3. Setup webmail (optional): ${GREEN}./setup-webmail.sh${NC}"
echo ""
echo -e "${GREEN}✅ Email server installation complete!${NC}"
echo ""
