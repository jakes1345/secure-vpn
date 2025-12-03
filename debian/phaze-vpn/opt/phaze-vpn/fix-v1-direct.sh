#!/bin/bash
# Direct fix for v1.0.0 issue - run this via SSH

ssh root@15.204.11.19 << 'ENDSSH'
# Remove ALL old files
rm -f /opt/phaze-vpn/web-portal/static/downloads/phazevpn-client_*.deb
rm -f /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.0.*.deb
rm -f /opt/phaze-vpn/web-portal/static/downloads/phaze-vpn_1.1.*.deb

# Copy ONLY v1.0.4
mkdir -p /opt/phaze-vpn/web-portal/static/downloads
cp /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/ 2>/dev/null || \
cp /opt/phaze-vpn/../phaze-vpn_1.0.4_all.deb /opt/phaze-vpn/web-portal/static/downloads/ 2>/dev/null

# Restart web portal
pkill -f 'python.*app.py'
sleep 2
cd /opt/phaze-vpn/web-portal && nohup python3 app.py > /dev/null 2>&1 &

echo "✅ Fixed - only v1.0.4 should be available now"
ls -lh /opt/phaze-vpn/web-portal/static/downloads/*.deb 2>/dev/null
ENDSSH

