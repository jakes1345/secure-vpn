#!/bin/bash
# Complete Email Server Setup for phazevpn.com
# Installs Postfix + Dovecot + Webmail (Roundcube)
# Run this on your VPS (15.204.11.19)

set -e

DOMAIN="phazevpn.com"
MAIL_DOMAIN="mail.phazevpn.com"
VPS_IP="15.204.11.19"

echo "📧 Setting up complete email server for $DOMAIN"
echo "================================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (sudo)"
    exit 1
fi

# Update system
echo ""
echo "1️⃣  Updating system packages..."
apt-get update
apt-get upgrade -y

# Install required packages
echo ""
echo "2️⃣  Installing email server packages..."
apt-get install -y \
    postfix \
    dovecot-core \
    dovecot-imapd \
    dovecot-pop3d \
    dovecot-lmtpd \
    opendkim \
    opendkim-tools \
    spamassassin \
    spamc \
    mysql-server \
    php-fpm \
    php-mysql \
    php-mbstring \
    php-xml \
    php-zip \
    php-gd \
    php-curl \
    nginx

# Configure Postfix
echo ""
echo "3️⃣  Configuring Postfix..."

# Backup original config
cp /etc/postfix/main.cf /etc/postfix/main.cf.backup

# Configure Postfix main.cf
cat > /etc/postfix/main.cf << EOF
# Basic settings
myhostname = $MAIL_DOMAIN
mydomain = $DOMAIN
myorigin = \$mydomain
inet_interfaces = all
inet_protocols = ipv4

# Network settings
mydestination = \$myhostname, localhost.\$mydomain, localhost, \$mydomain
relayhost =

# Mailbox settings
home_mailbox = Maildir/
mailbox_command =

# Security settings
smtpd_banner = \$myhostname ESMTP
disable_vrfy_command = yes
smtpd_helo_required = yes

# TLS settings
smtpd_tls_cert_file = /etc/letsencrypt/live/$DOMAIN/fullchain.pem
smtpd_tls_key_file = /etc/letsencrypt/live/$DOMAIN/privkey.pem
smtpd_tls_security_level = may
smtpd_tls_auth_only = yes
smtpd_tls_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtpd_tls_ciphers = high
smtpd_tls_mandatory_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtpd_tls_mandatory_ciphers = high
smtpd_tls_received_header = yes
smtpd_tls_session_cache_timeout = 3600s
smtpd_tls_session_cache_database = btree:\${data_directory}/smtpd_scache

# Submission (port 587)
smtpd_client_restrictions = permit_mynetworks, permit_sasl_authenticated, reject
smtpd_helo_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_invalid_helo_hostname, reject_non_fqdn_helo_hostname
smtpd_sender_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_non_fqdn_sender, reject_unknown_sender_domain
smtpd_recipient_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_non_fqdn_recipient, reject_unknown_recipient_domain, permit

# SASL authentication
smtpd_sasl_type = dovecot
smtpd_sasl_path = private/auth
smtpd_sasl_auth_enable = yes
smtpd_sasl_security_options = noanonymous
smtpd_sasl_local_domain = \$myhostname

# Milter (for DKIM)
milter_default_action = accept
milter_protocol = 6
smtpd_milters = local:opendkim/opendkim.sock
non_smtpd_milters = local:opendkim/opendkim.sock

# Performance
smtpd_recipient_limit = 100
smtpd_error_sleep_time = 1s
smtpd_soft_error_limit = 10
smtpd_hard_error_limit = 20
EOF

# Configure Postfix master.cf for submission
cat >> /etc/postfix/master.cf << EOF

# Submission (port 587)
submission inet n       -       y       -       -       smtpd
  -o syslog_name=postfix/submission
  -o smtpd_tls_security_level=encrypt
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_tls_auth_only=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_client_restrictions=permit_sasl_authenticated,reject
  -o smtpd_helo_restrictions=permit_mynetworks,permit_sasl_authenticated,reject_invalid_helo_hostname,reject_non_fqdn_helo_hostname
  -o smtpd_sender_restrictions=permit_mynetworks,permit_sasl_authenticated,reject_non_fqdn_sender,reject_unknown_sender_domain
  -o smtpd_recipient_restrictions=permit_mynetworks,permit_sasl_authenticated,reject_non_fqdn_recipient,reject_unknown_recipient_domain,permit
  -o smtpd_relay_restrictions=permit_mynetworks,permit_sasl_authenticated,defer_unauth_destination
  -o milter_macro_daemon_name=ORIGINATING

# SMTPS (port 465)
smtps     inet  n       -       y       -       -       smtpd
  -o syslog_name=postfix/smtps
  -o smtpd_tls_wrappermode=yes
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_client_restrictions=permit_sasl_authenticated,reject
  -o smtpd_helo_restrictions=permit_mynetworks,permit_sasl_authenticated,reject_invalid_helo_hostname,reject_non_fqdn_helo_hostname
  -o smtpd_sender_restrictions=permit_mynetworks,permit_sasl_authenticated,reject_non_fqdn_sender,reject_unknown_sender_domain
  -o smtpd_recipient_restrictions=permit_mynetworks,permit_sasl_authenticated,reject_non_fqdn_recipient,reject_unknown_recipient_domain,permit
  -o smtpd_relay_restrictions=permit_mynetworks,permit_sasl_authenticated,defer_unauth_destination
  -o milter_macro_daemon_name=ORIGINATING
EOF

# Configure Dovecot
echo ""
echo "4️⃣  Configuring Dovecot..."

# Backup original config
cp /etc/dovecot/dovecot.conf /etc/dovecot/dovecot.conf.backup

# Main dovecot config
cat > /etc/dovecot/dovecot.conf << EOF
protocols = imap pop3 lmtp
listen = *
mail_location = maildir:~/Maildir
mail_privileged_group = mail
userdb {
    driver = passwd
}
passdb {
    driver = pam
}
service auth {
    unix_listener /var/spool/postfix/private/auth {
        mode = 0666
        user = postfix
        group = postfix
    }
}
ssl = required
ssl_cert = </etc/letsencrypt/live/$DOMAIN/fullchain.pem
ssl_key = </etc/letsencrypt/live/$DOMAIN/privkey.pem
ssl_protocols = !SSLv2 !SSLv3 !TLSv1 !TLSv1.1
ssl_cipher_list = ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
ssl_prefer_server_ciphers = yes
EOF

# Configure OpenDKIM
echo ""
echo "5️⃣  Configuring OpenDKIM..."

# Create opendkim directory
mkdir -p /etc/opendkim
mkdir -p /var/spool/postfix/opendkim
chown opendkim:opendkim /var/spool/postfix/opendkim

# Generate DKIM keys
if [ ! -f "/etc/opendkim/mail.private" ]; then
    opendkim-genkey -t -s mail -d $DOMAIN -b 2048
    mv mail.private /etc/opendkim/mail.private
    mv mail.txt /etc/opendkim/mail.txt
    chown opendkim:opendkim /etc/opendkim/mail.private
    chmod 600 /etc/opendkim/mail.private
fi

# OpenDKIM config
cat > /etc/opendkim.conf << EOF
Domain                  $DOMAIN
KeyFile                 /etc/opendkim/mail.private
Selector                mail
Socket                  local:/var/spool/postfix/opendkim/opendkim.sock
PidFile                 /var/run/opendkim/opendkim.pid
UMask                   022
UserID                  opendkim:opendkim
TemporaryDirectory      /var/tmp
Canonicalization        relaxed/simple
Mode                    sv
SubDomains              no
AutoRestart             yes
AutoRestartRate         10/1h
Background              yes
DNSTimeout              5
SignatureAlgorithm      rsa-sha256
EOF

# Open firewall ports
echo ""
echo "6️⃣  Opening firewall ports..."
ufw allow 25/tcp   # SMTP
ufw allow 587/tcp  # SMTP Submission
ufw allow 465/tcp # SMTPS
ufw allow 143/tcp # IMAP
ufw allow 993/tcp # IMAPS
ufw allow 110/tcp # POP3
ufw allow 995/tcp # POP3S

# Create system user for email (example: admin@phazevpn.com)
echo ""
echo "7️⃣  Creating email user..."
# Use default 'admin' user, or set EMAIL_USER environment variable
EMAIL_USER="${EMAIL_USER:-admin}"

echo "   Using email user: $EMAIL_USER"

# Create user if doesn't exist
if ! id "$EMAIL_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$EMAIL_USER"
    echo "   User $EMAIL_USER created."
    echo "   ⚠️  IMPORTANT: Set password manually with: passwd $EMAIL_USER"
    echo "   Or set password now (will prompt):"
    # Only prompt for password if running interactively
    if [ -t 0 ]; then
        passwd "$EMAIL_USER"
    else
        echo "   ⚠️  Running non-interactively. Set password later with: passwd $EMAIL_USER"
    fi
else
    echo "   User $EMAIL_USER already exists"
fi

# Create Maildir
sudo -u "$EMAIL_USER" mkdir -p /home/$EMAIL_USER/Maildir/{new,cur,tmp}
sudo -u "$EMAIL_USER" chmod 700 /home/$EMAIL_USER/Maildir

# Restart services
echo ""
echo "8️⃣  Starting email services..."
systemctl enable postfix dovecot opendkim
systemctl restart postfix dovecot opendkim

# Get DKIM public key
echo ""
echo "9️⃣  DKIM Public Key (add this to Namecheap DNS):"
echo "================================================"
if [ -f "/etc/opendkim/mail.txt" ]; then
    cat /etc/opendkim/mail.txt
    echo ""
    echo "Add this as a TXT record in Namecheap:"
    echo "  Host: mail._domainkey"
    echo "  Value: (copy the entire TXT record from above)"
else
    echo "⚠️  DKIM key file not found. Run: opendkim-genkey -t -s mail -d $DOMAIN"
fi

# Test services
echo ""
echo "🔟 Testing email services..."
systemctl status postfix --no-pager | head -5
systemctl status dovecot --no-pager | head -5
systemctl status opendkim --no-pager | head -5

echo ""
echo "✅ Email server setup complete!"
echo ""
echo "📋 Summary:"
echo "   Domain: $DOMAIN"
echo "   Mail Server: $MAIL_DOMAIN"
echo "   Email User: $EMAIL_USER@$DOMAIN"
echo ""
echo "📧 Email Server Settings:"
echo "   SMTP Server: $MAIL_DOMAIN"
echo "   SMTP Port: 587 (STARTTLS) or 465 (SSL)"
echo "   IMAP Server: $MAIL_DOMAIN"
echo "   IMAP Port: 993 (SSL)"
echo ""
echo "🔒 Next Steps:"
echo "   1. Add DKIM TXT record to Namecheap DNS (see above)"
echo "   2. Test sending email: echo 'Test' | mail -s 'Test' $EMAIL_USER@$DOMAIN"
echo "   3. Configure email client with the settings above"
echo "   4. Install webmail (Roundcube) if desired"
echo ""
echo "🧪 Test email server:"
echo "   telnet $MAIL_DOMAIN 25"
echo "   telnet $MAIL_DOMAIN 587"

