#!/bin/bash
# Fix APT Repository Issues

echo "🔧 Fixing APT repository issues..."

# 1. Fix Cursor repository (disable it - it's causing errors)
echo "1. Disabling problematic Cursor repository..."
sudo sed -i 's/^deb/#deb/g' /etc/apt/sources.list.d/cursor.list 2>/dev/null || echo "  No cursor.list found"

# 2. Fix local PhazeVPN repository (remove it - outdated)
echo "2. Removing old local PhazeVPN repository..."
sudo rm -f /etc/apt/sources.list.d/phazevpn*.list 2>/dev/null || echo "  No phazevpn list found"

# 3. Clean up APT cache
echo "3. Cleaning APT cache..."
sudo apt clean

# 4. Update package lists
echo "4. Updating package lists..."
sudo apt update

echo "✅ APT issues fixed!"
