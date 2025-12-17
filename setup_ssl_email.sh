#!/bin/bash
# SSL and Email Security Setup

echo "🔒 Configuring SSL and Email Security..."

# 2. Setup SSL with Let's Encrypt
echo "Running Certbot..."
certbot --nginx -d phazevpn.com -d www.phazevpn.com --non-interactive --agree-tos -m admin@phazevpn.com --redirect

# 3. Setup DKIM
echo "Configuring DKIM..."
mkdir -p /etc/opendkim/keys
chown -R opendkim:opendkim /etc/opendkim
chmod 700 /etc/opendkim/keys

# Generate keys if not exists
if [ ! -f /etc/opendkim/keys/default.private ]; then
    opendkim-genkey -s default -d phazevpn.com -D /etc/opendkim/keys
    chown opendkim:opendkim /etc/opendkim/keys/default.private
fi

# Configure OpenDKIM
cat > /etc/opendkim.conf <<EOF
Syslog                  yes
UMask                   002
Domain                  phazevpn.com
KeyFile                 /etc/opendkim/keys/default.private
Selector                default
Socket                  inet:8891@localhost
PidFile                 /var/run/opendkim/opendkim.pid
OversignHeaders         From
TrustAnchorFile         /usr/share/dns/root.key
UserID                  opendkim
EOF

cat > /etc/default/opendkim <<EOF
SOCKET="inet:8891@localhost"
EOF

# Restart OpenDKIM
systemctl restart opendkim

# Configure Postfix
postconf -e 'milter_default_action = accept'
postconf -e 'milter_protocol = 6'
postconf -e 'smtpd_milters = inet:localhost:8891'
postconf -e 'non_smtpd_milters = inet:localhost:8891'
systemctl restart postfix

echo "✅ SSL and DKIM Configured!"
echo "--------------------------------------------------------"
echo "👉 ADD THIS DNS RECORD FOR EMAIL SECURITY (DKIM):"
echo "--------------------------------------------------------"
cat /etc/opendkim/keys/default.txt
echo "--------------------------------------------------------"
