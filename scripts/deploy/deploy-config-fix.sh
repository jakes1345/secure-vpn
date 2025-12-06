#!/bin/bash
# Deploy config generation fixes to VPS

echo "🚀 Deploying config generation fixes to VPS..."
echo ""

VPS="root@phazevpn.com"
VPS_DIR="/opt/phaze-vpn"

# Deploy generate-all-configs.py
echo "📦 Deploying generate-all-configs.py..."
scp generate-all-configs.py $VPS:$VPS_DIR/
ssh $VPS "chmod +x $VPS_DIR/generate-all-configs.py"

# Deploy updated app.py
echo "📦 Deploying updated web-portal/app.py..."
scp web-portal/app.py $VPS:$VPS_DIR/web-portal/

# Restart web portal
echo "🔄 Restarting web portal..."
ssh $VPS "systemctl restart phaze-vpn-web || systemctl restart gunicorn || pkill -f 'python.*app.py'"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Now test by:"
echo "1. Open GUI and add a new client"
echo "2. Try downloading all 3 config types (OpenVPN, PhazeVPN, WireGuard)"
echo "3. Verify all configs download correctly"

