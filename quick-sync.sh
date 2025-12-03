#!/bin/bash
# Quick sync using sshpass

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="Jakes1328!@"
VPS_PATH="/opt/secure-vpn"
LOCAL_PATH="/opt/phaze-vpn"

echo "=========================================="
echo "🔄 SYNCING FILES TO VPS"
echo "=========================================="
echo ""

# Check if sshpass is available
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    sudo apt-get update -qq && sudo apt-get install -y sshpass -qq
fi

export SSHPASS="$VPS_PASS"

echo "[1/3] Syncing app.py..."
sshpass -e scp -o StrictHostKeyChecking=no \
    "$LOCAL_PATH/web-portal/app.py" \
    "${VPS_USER}@${VPS_IP}:${VPS_PATH}/web-portal/app.py" && echo "   ✓ Done" || echo "   ✗ Failed"

echo "[2/3] Syncing requirements.txt..."
sshpass -e scp -o StrictHostKeyChecking=no \
    "$LOCAL_PATH/web-portal/requirements.txt" \
    "${VPS_USER}@${VPS_IP}:${VPS_PATH}/web-portal/requirements.txt" && echo "   ✓ Done" || echo "   ✗ Failed"

echo "[3/3] Syncing base.html..."
sshpass -e scp -o StrictHostKeyChecking=no \
    "$LOCAL_PATH/web-portal/templates/base.html" \
    "${VPS_USER}@${VPS_IP}:${VPS_PATH}/web-portal/templates/base.html" && echo "   ✓ Done" || echo "   ✗ Failed"

unset SSHPASS

echo ""
echo "=========================================="
echo "✅ SYNC COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  ssh ${VPS_USER}@${VPS_IP}"
echo "  cd ${VPS_PATH}/web-portal"
echo "  pip3 install -r requirements.txt"
echo "  sudo systemctl restart secure-vpn-portal"
echo ""

