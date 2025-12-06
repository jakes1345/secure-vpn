#!/bin/bash
# Sync all files to VPS when connection is ready
# Run this when SSH works

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="Jakes1328!@"

echo "=========================================="
echo "🚀 SYNCING ALL FILES TO VPS"
echo "=========================================="
echo ""

# Use scp with sshpass if available, or expect
if command -v sshpass &> /dev/null; then
    echo "Using sshpass..."
    SSHPASS=$VPS_PASS sshpass -e scp -r \
        web-portal/app.py \
        web-portal/email_api.py \
        web-portal/email_mailjet.py \
        web-portal/mailjet_config.py \
        phazevpn-client/phazevpn-client.py \
        ${VPS_USER}@${VPS_IP}:/opt/secure-vpn/
else
    echo "Using expect..."
    expect << EOF
spawn scp -r web-portal/app.py web-portal/email_api.py web-portal/email_mailjet.py web-portal/mailjet_config.py phazevpn-client/phazevpn-client.py ${VPS_USER}@${VPS_IP}:/opt/secure-vpn/
expect "password:"
send "${VPS_PASS}\r"
expect eof
EOF
fi

echo ""
echo "✅ Files synced!"
echo ""
echo "Now restart services on VPS:"
echo "  ssh root@15.204.11.19"
echo "  systemctl restart secure-vpn-portal"

