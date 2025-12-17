#!/bin/bash
# Complete Email Server Setup
# Postfix + Dovecot + MySQL + SpamAssassin + ClamAV + Amavis
# Full production-ready email server

set -e

EMAIL_DOMAIN="${EMAIL_DOMAIN:-phazevpn.duckdns.org}"
EMAIL_HOSTNAME="${EMAIL_HOSTNAME:-mail.phazevpn.duckdns.org}"
MYSQL_ROOT_PASS="${MYSQL_ROOT_PASS:-mailpass}"
MYSQL_MAIL_USER="${MYSQL_MAIL_USER:-mailuser}"
MYSQL_MAIL_PASS="${MYSQL_MAIL_PASS:-mailpass}"

echo "📧 Setting up Complete Email Server..."
echo "   Domain: $EMAIL_DOMAIN"
echo "   Hostname: $EMAIL_HOSTNAME"

# Update system
apt-get update
apt-get upgrade -y

# Install all email components
apt-get install -y \
    postfix \
    postfix-mysql \
    dovecot-core \
    dovecot-imapd \
    dovecot-pop3d \
    dovecot-lmtpd \
    dovecot-mysql \
    mysql-server \
    mysql-client \
    spamassassin \
    clamav \
    clamav-daemon \
    amavisd-new \
    amavisd-new \
    libnet-dns-perl \
    libmail-spf-perl \
    pyzor \
    razor \
    opendkim \
    opendkim-tools \
    fail2ban \
    certbot \
    python3-certbot-nginx

# Start MySQL
systemctl start mysql
systemctl enable mysql

# Create MySQL database and user
mysql -u root << EOF
CREATE DATABASE IF NOT EXISTS mailserver;
CREATE USER IF NOT EXISTS '$MYSQL_MAIL_USER'@'localhost' IDENTIFIED BY '$MYSQL_MAIL_PASS';
GRANT ALL PRIVILEGES ON mailserver.* TO '$MYSQL_MAIL_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

# Create database tables
mysql -u root mailserver << 'SQL_EOF'
CREATE TABLE IF NOT EXISTS virtual_domains (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS virtual_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    domain_id INT NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(106) NOT NULL,
    quota BIGINT DEFAULT 1073741824,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (domain_id) REFERENCES virtual_domains(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS virtual_aliases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    domain_id INT NOT NULL,
    source VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    FOREIGN KEY (domain_id) REFERENCES virtual_domains(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS virtual_transports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    domain VARCHAR(120) NOT NULL,
    transport VARCHAR(200) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert domain
INSERT IGNORE INTO virtual_domains (name) VALUES ('phazevpn.duckdns.org');

-- Insert default admin user
INSERT IGNORE INTO virtual_users (domain_id, email, password) 
SELECT 1, 'admin@phazevpn.duckdns.org', 
'{PLAIN}admin123' FROM virtual_domains WHERE name = 'phazevpn.duckdns.org' LIMIT 1;
SQL_EOF

# Configure Postfix
echo "📝 Configuring Postfix..."

# Backup original config
cp /etc/postfix/main.cf /etc/postfix/main.cf.backup

# Main Postfix configuration
cat > /etc/postfix/main.cf << POSTFIX_EOF
# Basic settings
myhostname = $EMAIL_HOSTNAME
mydomain = $EMAIL_DOMAIN
myorigin = \$mydomain
inet_interfaces = all
inet_protocols = ipv4

# Virtual mailbox settings
virtual_mailbox_domains = mysql:/etc/postfix/mysql-virtual-mailbox-domains.cf
virtual_mailbox_maps = mysql:/etc/postfix/mysql-virtual-mailbox-maps.cf
virtual_alias_maps = mysql:/etc/postfix/mysql-virtual-alias-maps.cf
virtual_minimum_uid = 100
virtual_uid_maps = static:5000
virtual_gid_maps = static:5000
virtual_mailbox_base = /var/mail/vhosts

# Security settings
smtpd_tls_cert_file = /etc/ssl/certs/ssl-cert-snakeoil.pem
smtpd_tls_key_file = /etc/ssl/private/ssl-cert-snakeoil.key
smtpd_use_tls = yes
smtpd_tls_auth_only = yes
smtpd_tls_security_level = may
smtpd_tls_protocols = !SSLv2, !SSLv3
smtpd_tls_ciphers = high
smtpd_tls_mandatory_protocols = !SSLv2, !SSLv3

# Submission (port 587)
smtpd_sasl_type = dovecot
smtpd_sasl_path = private/auth
smtpd_sasl_auth_enable = yes
smtpd_sasl_security_options = noanonymous
smtpd_sasl_local_domain = \$myhostname
smtpd_recipient_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_unauth_destination
smtpd_relay_restrictions = permit_mynetworks, permit_sasl_authenticated, defer_unauth_destination

# Restrictions
smtpd_helo_restrictions = permit_mynetworks, permit_sasl_authenticated, warn_if_reject reject_non_fqdn_helo_hostname, reject_invalid_helo_hostname, permit
smtpd_sender_restrictions = permit_mynetworks, permit_sasl_authenticated, warn_if_reject reject_non_fqdn_sender, reject_unknown_sender_domain, permit
smtpd_client_restrictions = permit_mynetworks, permit_sasl_authenticated, permit

# Message size limit (50MB)
message_size_limit = 52428800
mailbox_size_limit = 0

# Network settings
mynetworks = 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128

# Amavis integration
content_filter = amavis:[127.0.0.1]:10024

# Other settings
biff = no
append_dot_mydomain = no
readme_directory = no
compatibility_level = 2
POSTFIX_EOF

# Master configuration
cat >> /etc/postfix/master.cf << MASTER_EOF

# Amavis
amavis unix - - - - 2 smtp
    -o smtp_data_done_timeout=1200
    -o smtp_send_xforward_command=yes
    -o disable_dns_lookups=yes
    -o max_use=20

127.0.0.1:10025 inet n - - - - smtpd
    -o content_filter=
    -o local_recipient_maps=
    -o relay_recipient_maps=
    -o smtpd_restriction_classes=
    -o smtpd_helo_restrictions=
    -o smtpd_sender_restrictions=
    -o smtpd_recipient_restrictions=permit_mynetworks,reject
    -o mynetworks=127.0.0.0/8
    -o smtpd_authorized_xforward_hosts=127.0.0.0/8
MASTER_EOF

# MySQL maps for Postfix
cat > /etc/postfix/mysql-virtual-mailbox-domains.cf << EOF
user = $MYSQL_MAIL_USER
password = $MYSQL_MAIL_PASS
hosts = 127.0.0.1
dbname = mailserver
query = SELECT 1 FROM virtual_domains WHERE name='%s'
EOF

cat > /etc/postfix/mysql-virtual-mailbox-maps.cf << EOF
user = $MYSQL_MAIL_USER
password = $MYSQL_MAIL_PASS
hosts = 127.0.0.1
dbname = mailserver
query = SELECT 1 FROM virtual_users WHERE email='%s'
EOF

cat > /etc/postfix/mysql-virtual-alias-maps.cf << EOF
user = $MYSQL_MAIL_USER
password = $MYSQL_MAIL_PASS
hosts = 127.0.0.1
dbname = mailserver
query = SELECT destination FROM virtual_aliases WHERE source='%s'
EOF

# Configure Dovecot
echo "📝 Configuring Dovecot..."

# Create mail directory
mkdir -p /var/mail/vhosts/$EMAIL_DOMAIN
groupadd -g 5000 vmail || true
useradd -g vmail -u 5000 vmail -d /var/mail || true
chown -R vmail:vmail /var/mail

# Dovecot main config
cat > /etc/dovecot/dovecot.conf << DOVECOT_EOF
protocols = imap pop3 lmtp
listen = *
mail_location = maildir:/var/mail/vhosts/%d/%n
mail_privileged_group = mail
userdb {
    driver = static
    args = uid=vmail gid=vmail home=/var/mail/vhosts/%d/%n
}
passdb {
    driver = sql
    args = /etc/dovecot/dovecot-sql.conf.ext
}
namespace inbox {
    inbox = yes
}
service imap-login {
    inet_listener imap {
        port = 143
    }
    inet_listener imaps {
        port = 993
        ssl = yes
    }
}
service pop3-login {
    inet_listener pop3 {
        port = 110
    }
    inet_listener pop3s {
        port = 995
        ssl = yes
    }
}
service lmtp {
    unix_listener /var/spool/postfix/private/dovecot-lmtp {
        mode = 0600
        user = postfix
        group = postfix
    }
}
service auth {
    unix_listener /var/spool/postfix/private/auth {
        mode = 0666
        user = postfix
        group = postfix
    }
    unix_listener auth-userdb {
        mode = 0600
        user = vmail
        group = vmail
    }
    user = dovecot
}
service auth-worker {
    user = vmail
}
ssl = required
ssl_cert = </etc/ssl/certs/ssl-cert-snakeoil.pem
ssl_key = </etc/ssl/private/ssl-cert-snakeoil.key
ssl_protocols = !SSLv2 !SSLv3
ssl_cipher_list = ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
DOVECOT_EOF

# Dovecot SQL config
cat > /etc/dovecot/dovecot-sql.conf.ext << EOF
driver = mysql
connect = host=127.0.0.1 dbname=mailserver user=$MYSQL_MAIL_USER password=$MYSQL_MAIL_PASS
default_pass_scheme = PLAIN
password_query = SELECT email as user, password FROM virtual_users WHERE email='%u' AND active=1;
EOF

# Configure Amavis
echo "📝 Configuring Amavis..."
sed -i "s/\$mydomain = 'example.com';/\$mydomain = '$EMAIL_DOMAIN';/" /etc/amavis/conf.d/05-domain_id
sed -i "s/\$myhostname = 'example.com';/\$myhostname = '$EMAIL_HOSTNAME';/" /etc/amavis/conf.d/05-domain_id

# Update ClamAV
freshclam

# Start and enable services
systemctl restart postfix
systemctl restart dovecot
systemctl restart amavis
systemctl restart spamassassin
systemctl restart clamav-daemon

systemctl enable postfix
systemctl enable dovecot
systemctl enable amavis
systemctl enable spamassassin
systemctl enable clamav-daemon

# Configure firewall
ufw allow 25/tcp comment 'SMTP'
ufw allow 587/tcp comment 'SMTP Submission'
ufw allow 993/tcp comment 'IMAPS'
ufw allow 995/tcp comment 'POP3S'
ufw allow 143/tcp comment 'IMAP'
ufw allow 110/tcp comment 'POP3'

echo ""
echo "✅ Email Server Setup Complete!"
echo ""
echo "📧 Email Configuration:"
echo "   Domain: $EMAIL_DOMAIN"
echo "   Hostname: $EMAIL_HOSTNAME"
echo "   Default user: admin@$EMAIL_DOMAIN"
echo "   Default password: admin123"
echo ""
echo "🔧 Services:"
echo "   - Postfix (SMTP): Ports 25, 587"
echo "   - Dovecot (IMAP/POP3): Ports 143, 993, 110, 995"
echo "   - SpamAssassin: Active"
echo "   - ClamAV: Active"
echo "   - Amavis: Active"
echo ""
echo "📝 Next Steps:"
echo "   1. Configure DNS records (SPF, DKIM, DMARC, MX)"
echo "   2. Set up SSL certificates (Let's Encrypt)"
echo "   3. Create email accounts: ./manage-email-accounts.sh add user@$EMAIL_DOMAIN"
echo ""
