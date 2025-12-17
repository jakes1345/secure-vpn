#!/bin/bash
#
# Configure Email Deliverability - Maximize Inbox Delivery
# Sets up SPF, DKIM, DMARC, and best practices to avoid spam folder
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
HOSTNAME="${EMAIL_HOSTNAME:-mail.phazevpn.duckdns.org}"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Email Deliverability Configuration                    ║${NC}"
echo -e "${BLUE}║        Maximize Inbox Delivery, Avoid Spam Folder          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root (sudo)${NC}"
    exit 1
fi

# 1. Install OpenDKIM
echo -e "${BLUE}[1/8]${NC} Installing OpenDKIM..."
apt update -qq
apt install -y opendkim opendkim-tools

# 2. Generate DKIM Keys
echo -e "${BLUE}[2/8]${NC} Generating DKIM keys..."
mkdir -p /etc/opendkim/keys/${DOMAIN}
if [ ! -f /etc/opendkim/keys/${DOMAIN}/default.private ]; then
    opendkim-genkey -b 2048 -d ${DOMAIN} -s default -D /etc/opendkim/keys/${DOMAIN}
    chown opendkim:opendkim /etc/opendkim/keys/${DOMAIN}/default.private
    chmod 600 /etc/opendkim/keys/${DOMAIN}/default.private
    echo -e "${GREEN}✅ DKIM keys generated${NC}"
else
    echo -e "${YELLOW}⚠️  DKIM keys already exist${NC}"
fi

# 3. Configure OpenDKIM
echo -e "${BLUE}[3/8]${NC} Configuring OpenDKIM..."
cat > /etc/opendkim.conf <<EOF
# PhazeVPN Email Server - OpenDKIM Configuration
Domain                  ${DOMAIN}
KeyFile                 /etc/opendkim/keys/${DOMAIN}/default.private
Selector                default
Socket                  inet:8891@localhost
PidFile                 /var/run/opendkim/opendkim.pid
UMask                   022
UserID                  opendkim:opendkim
Mode                    sv
Canonicalization        relaxed/simple
SignatureAlgorithm      rsa-sha256
MinimumKeyBits          1024
KeyTable                 refile:/etc/opendkim/KeyTable
SigningTable            refile:/etc/opendkim/SigningTable
ExternalIgnoreList      refile:/etc/opendkim/TrustedHosts
InternalHosts           refile:/etc/opendkim/TrustedHosts
EOF

# Create OpenDKIM tables
cat > /etc/opendkim/KeyTable <<EOF
default._domainkey.${DOMAIN} ${DOMAIN}:default:/etc/opendkim/keys/${DOMAIN}/default.private
EOF

cat > /etc/opendkim/SigningTable <<EOF
*@${DOMAIN} default._domainkey.${DOMAIN}
EOF

cat > /etc/opendkim/TrustedHosts <<EOF
127.0.0.1
localhost
${HOSTNAME}
${DOMAIN}
EOF

chown -R opendkim:opendkim /etc/opendkim
systemctl enable opendkim
systemctl restart opendkim

echo -e "${GREEN}✅ OpenDKIM configured${NC}"

# 4. Configure Postfix for Deliverability
echo -e "${BLUE}[4/8]${NC} Configuring Postfix for maximum deliverability..."

# Backup original config
cp /etc/postfix/main.cf /etc/postfix/main.cf.backup.$(date +%Y%m%d)

# Add deliverability settings to main.cf
cat >> /etc/postfix/main.cf <<EOF

# Deliverability Enhancements
# HELO/EHLO restrictions
smtpd_helo_required = yes
smtpd_helo_restrictions = 
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_invalid_helo_hostname,
    reject_non_fqdn_helo_hostname,
    permit

# Rate limiting (prevents spam-like behavior)
smtpd_client_connection_count_limit = 10
smtpd_client_connection_rate_limit = 30
smtpd_error_sleep_time = 1s
smtpd_soft_error_limit = 10
smtpd_hard_error_limit = 20

# DKIM signing
milter_protocol = 2
milter_default_action = accept
smtpd_milters = inet:localhost:8891
non_smtpd_milters = inet:localhost:8891

# Message size limit
message_size_limit = 10240000

# Proper headers
header_checks = regexp:/etc/postfix/header_checks
EOF

# Create header checks file
cat > /etc/postfix/header_checks <<EOF
# Reject obvious spam in subject lines
/^Subject:.*FREE.*CLICK/ REJECT Spam trigger words detected
/^Subject:.*URGENT.*BUY/ REJECT Spam trigger words detected
/^Subject:.*\$\$\$/ REJECT Spam trigger words detected
EOF

postmap /etc/postfix/header_checks
postfix reload

echo -e "${GREEN}✅ Postfix configured for deliverability${NC}"

# 5. Display DKIM Public Key
echo -e "${BLUE}[5/8]${NC} DKIM Public Key (add to DNS):"
echo ""
echo -e "${YELLOW}DNS Record to Add:${NC}"
echo -e "${GREEN}Type: TXT${NC}"
echo -e "${GREEN}Name: default._domainkey${NC}"
echo ""
cat /etc/opendkim/keys/${DOMAIN}/default.txt
echo ""

# 6. Check DNS Records
echo -e "${BLUE}[6/8]${NC} Checking DNS records..."
echo ""

# Check MX
echo -n "  MX Record: "
if dig MX ${DOMAIN} +short | grep -q "${HOSTNAME}"; then
    echo -e "${GREEN}✅ Found${NC}"
else
    echo -e "${RED}❌ Not found${NC}"
    echo -e "${YELLOW}   Add: MX @ ${HOSTNAME} (Priority: 10)${NC}"
fi

# Check A record for mail
echo -n "  A Record (mail): "
if dig A ${HOSTNAME} +short | grep -q "."; then
    echo -e "${GREEN}✅ Found${NC}"
else
    echo -e "${RED}❌ Not found${NC}"
    echo -e "${YELLOW}   Add: A mail YOUR_IP${NC}"
fi

# Check SPF
echo -n "  SPF Record: "
if dig TXT ${DOMAIN} +short | grep -q "spf1"; then
    echo -e "${GREEN}✅ Found${NC}"
else
    echo -e "${RED}❌ Not found${NC}"
    echo -e "${YELLOW}   Add: TXT @ \"v=spf1 mx ip4:YOUR_IP ~all\"${NC}"
fi

# Check DKIM
echo -n "  DKIM Record: "
if dig TXT default._domainkey.${DOMAIN} +short | grep -q "DKIM1"; then
    echo -e "${GREEN}✅ Found${NC}"
else
    echo -e "${RED}❌ Not found${NC}"
    echo -e "${YELLOW}   Add the DKIM key shown above${NC}"
fi

# Check DMARC
echo -n "  DMARC Record: "
if dig TXT _dmarc.${DOMAIN} +short | grep -q "DMARC1"; then
    echo -e "${GREEN}✅ Found${NC}"
else
    echo -e "${RED}❌ Not found${NC}"
    echo -e "${YELLOW}   Add: TXT _dmarc \"v=DMARC1; p=none; rua=mailto:admin@${DOMAIN}\"${NC}"
fi

# Check PTR
echo -n "  PTR Record: "
PUBLIC_IP=$(dig A ${HOSTNAME} +short | head -1)
if [ -n "$PUBLIC_IP" ]; then
    PTR_RESULT=$(dig -x ${PUBLIC_IP} +short)
    if echo "$PTR_RESULT" | grep -q "${HOSTNAME}"; then
        echo -e "${GREEN}✅ Found${NC}"
    else
        echo -e "${RED}❌ Not found${NC}"
        echo -e "${YELLOW}   Request from hosting provider: ${PUBLIC_IP} → ${HOSTNAME}${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Could not determine IP${NC}"
fi

echo ""

# 7. Check Blacklists
echo -e "${BLUE}[7/8]${NC} Checking IP blacklists..."
PUBLIC_IP=$(dig A ${HOSTNAME} +short | head -1)
if [ -n "$PUBLIC_IP" ]; then
    echo -e "${YELLOW}Checking IP: ${PUBLIC_IP}${NC}"
    echo ""
    echo -e "${YELLOW}Check manually at:${NC}"
    echo -e "  https://mxtoolbox.com/blacklists.aspx"
    echo -e "  Enter IP: ${PUBLIC_IP}"
    echo ""
else
    echo -e "${YELLOW}⚠️  Could not determine IP for blacklist check${NC}"
fi

# 8. Generate Deliverability Report
echo -e "${BLUE}[8/8]${NC} Generating deliverability report..."
cat > /tmp/deliverability-report.txt <<EOF
╔══════════════════════════════════════════════════════════════╗
║           Email Deliverability Configuration Report         ║
╚══════════════════════════════════════════════════════════════╝

Domain: ${DOMAIN}
Hostname: ${HOSTNAME}
IP: ${PUBLIC_IP:-Unknown}

✅ CONFIGURED:
  • OpenDKIM installed and configured
  • DKIM keys generated
  • Postfix configured for deliverability
  • Rate limiting enabled
  • Header checks configured

📋 DNS RECORDS TO ADD:

1. MX Record:
   Type: MX
   Name: @
   Value: ${HOSTNAME}
   Priority: 10

2. A Record:
   Type: A
   Name: mail
   Value: ${PUBLIC_IP:-YOUR_IP}

3. SPF Record:
   Type: TXT
   Name: @
   Value: v=spf1 mx ip4:${PUBLIC_IP:-YOUR_IP} a:${HOSTNAME} ~all

4. DKIM Record:
   Type: TXT
   Name: default._domainkey
   Value: (see output above)

5. DMARC Record:
   Type: TXT
   Name: _dmarc
   Value: v=DMARC1; p=none; rua=mailto:admin@${DOMAIN}; ruf=mailto:admin@${DOMAIN}; fo=1

6. PTR Record:
   Request from hosting provider: ${PUBLIC_IP:-YOUR_IP} → ${HOSTNAME}

📊 NEXT STEPS:

1. Add all DNS records (wait 24-48 hours for propagation)
2. Test with Mail-Tester: https://www.mail-tester.com/
3. Warm up IP (send 5-10 emails/day for first week)
4. Monitor with Google Postmaster Tools
5. Check blacklists regularly

⚠️  IMPORTANT:
  • New email servers need 1-2 weeks to build reputation
  • Start with small email volumes
  • Monitor bounce rates and spam complaints
  • Never send unsolicited emails

📖 Full Guide: See EMAIL-DELIVERABILITY-GUIDE.md
EOF

cat /tmp/deliverability-report.txt
echo ""
echo -e "${GREEN}✅ Report saved to: /tmp/deliverability-report.txt${NC}"

# Summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Configuration Complete!                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Add DNS records (see report above)"
echo "  2. Wait 24-48 hours for DNS propagation"
echo "  3. Test with: https://www.mail-tester.com/"
echo "  4. Start sending emails gradually (warm-up period)"
echo ""
echo -e "${GREEN}✅ Email deliverability configured!${NC}"
echo ""

