#!/bin/bash
# Deploy package to VPS

set -e

PACKAGE="/media/jack/Liunux/phaze-vpn_1.0.4_all.deb"
VPS_HOST="phazevpn.com"
VPS_USER="root"

if [ ! -f "$PACKAGE" ]; then
    echo "❌ Package not found: $PACKAGE"
    exit 1
fi

echo "============================================================"
echo "Deploying Package to VPS"
echo "============================================================"
echo ""
echo "📦 Package: $PACKAGE"
ls -lh "$PACKAGE"
echo ""

echo "[1/3] Copying to repository..."
scp "$PACKAGE" "$VPS_USER@$VPS_HOST:/opt/phazevpn-repo/"
echo "✅ Copied to repository"
echo ""

echo "[2/3] Copying to downloads directory..."
scp "$PACKAGE" "$VPS_USER@$VPS_HOST:/opt/phaze-vpn/web-portal/static/downloads/"
echo "✅ Copied to downloads"
echo ""

echo "[3/3] Updating repository index..."
ssh "$VPS_USER@$VPS_HOST" "cd /opt/phazevpn-repo && dpkg-scanpackages . /dev/null > Packages && gzip -kf Packages"
echo "✅ Repository index updated"
echo ""

echo "============================================================"
echo "✅ Package Deployed!"
echo "============================================================"
echo ""
echo "To install:"
echo "  ssh $VPS_USER@$VPS_HOST"
echo "  sudo dpkg -i /opt/phazevpn-repo/phaze-vpn_1.0.4_all.deb"
echo "  sudo apt-get install -f"
echo ""

