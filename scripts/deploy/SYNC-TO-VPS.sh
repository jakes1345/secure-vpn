#!/bin/bash
# Sync Local Changes to VPS
# Run this from your LOCAL computer

set -e

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PATH="/opt/secure-vpn"
LOCAL_PATH="/opt/phaze-vpn"

echo "=========================================="
echo "🔄 SYNCING LOCAL CHANGES TO VPS"
echo "=========================================="
echo ""
echo "VPS: ${VPS_USER}@${VPS_IP}"
echo "Remote Path: ${VPS_PATH}"
echo "Local Path: ${LOCAL_PATH}"
echo ""

# Check if we're in the right directory
if [ ! -f "${LOCAL_PATH}/web-portal/app.py" ]; then
    echo "❌ Error: Can't find web-portal/app.py"
    echo "   Make sure you're running this from the project root"
    exit 1
fi

echo "📋 Files to sync:"
echo "  ✓ web-portal/app.py (type fixes)"
echo "  ✓ web-portal/requirements.txt (dependencies)"
echo "  ✓ web-portal/templates/base.html (flash messages fix)"
echo "  ✓ web-portal/pyrightconfig.json (type checker config)"
echo ""

# Create backup directory on VPS first
echo "📦 Creating backup on VPS..."
ssh ${VPS_USER}@${VPS_IP} "mkdir -p ${VPS_PATH}/backups/$(date +%Y%m%d-%H%M%S)" || true

echo ""
echo "🚀 Starting sync..."
echo ""

# Sync web portal app.py
echo "[1/4] Syncing app.py..."
scp ${LOCAL_PATH}/web-portal/app.py ${VPS_USER}@${VPS_IP}:${VPS_PATH}/web-portal/app.py
echo "   ✓ app.py synced"

# Sync requirements.txt
echo "[2/4] Syncing requirements.txt..."
scp ${LOCAL_PATH}/web-portal/requirements.txt ${VPS_USER}@${VPS_IP}:${VPS_PATH}/web-portal/requirements.txt
echo "   ✓ requirements.txt synced"

# Sync base.html template
echo "[3/4] Syncing templates/base.html..."
scp ${LOCAL_PATH}/web-portal/templates/base.html ${VPS_USER}@${VPS_IP}:${VPS_PATH}/web-portal/templates/base.html
echo "   ✓ base.html synced"

# Sync pyrightconfig.json (if it exists)
if [ -f "${LOCAL_PATH}/web-portal/pyrightconfig.json" ]; then
    echo "[4/4] Syncing pyrightconfig.json..."
    scp ${LOCAL_PATH}/web-portal/pyrightconfig.json ${VPS_USER}@${VPS_IP}:${VPS_PATH}/web-portal/pyrightconfig.json
    echo "   ✓ pyrightconfig.json synced"
else
    echo "[4/4] Skipping pyrightconfig.json (not needed on VPS)"
fi

echo ""
echo "=========================================="
echo "✅ SYNC COMPLETE!"
echo "=========================================="
echo ""
echo "📝 Next steps on VPS:"
echo ""
echo "1. SSH into VPS:"
echo "   ssh ${VPS_USER}@${VPS_IP}"
echo ""
echo "2. Install/update dependencies:"
echo "   cd ${VPS_PATH}/web-portal"
echo "   pip3 install -r requirements.txt"
echo ""
echo "3. Restart web portal service:"
echo "   sudo systemctl restart secure-vpn-portal"
echo "   # OR if running manually:"
echo "   # Find and restart the process"
echo ""
echo "4. Check status:"
echo "   sudo systemctl status secure-vpn-portal"
echo ""
echo "=========================================="

