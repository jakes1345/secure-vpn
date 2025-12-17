#!/bin/bash
# Complete APT Repository Setup - Makes updates appear in Update Manager

set -e

echo "================================================================================"
echo "🚀 COMPLETE APT REPOSITORY SETUP FOR PHAZEVPN"
echo "================================================================================"
echo ""
echo "This will set up the APT repository so users see updates automatically!"
echo ""

# Step 1: Set up repository on VPS
echo "1️⃣ Setting up repository on VPS..."
python3 create-apt-repository-on-vps.py

echo ""
echo "2️⃣ Building Linux package..."
./rebuild-linux-package.sh

echo ""
echo "3️⃣ Publishing to repository..."
python3 publish-update-to-apt-repo.py

echo ""
echo "================================================================================"
echo "✅ COMPLETE! Updates are now available via APT!"
echo "================================================================================"
echo ""
echo "📱 Users can add the repository:"
echo "   curl -fsSL https://phazevpn.duckdns.org/repo/gpg-key.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/phazevpn.gpg"
echo "   echo 'deb https://phazevpn.duckdns.org/repo stable main' | sudo tee /etc/apt/sources.list.d/phazevpn.list"
echo "   sudo apt update"
echo ""
echo "🔔 Updates will show in Update Manager automatically!"
echo "   Users just run: sudo apt update && sudo apt upgrade"
echo ""

