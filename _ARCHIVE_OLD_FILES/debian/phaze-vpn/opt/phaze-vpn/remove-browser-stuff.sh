#!/bin/bash
# Remove all PhazeVPN browser-related files from PC

echo "🧹 Removing PhazeVPN browser files..."

# Directories to remove
DIRS_TO_REMOVE=(
    "phazebrowser"
    "debian/phaze-vpn/opt/phaze-vpn/phazebrowser"
    "debian/phaze-vpn/opt/phaze-vpn/web-portal/templates/phazebrowser.html"
)

# Files to remove
FILES_TO_REMOVE=(
    "enhance-browser-with-full-features.py"
    "setup-browser-on-vps-complete.py"
    "BROWSER-SETUP-COMPLETE.md"
    "fix-browser-vps-complete.py"
    "verify-browser-vps-setup.py"
    "vps-browser-automation.sh"
    "sync-browser-to-vps.py"
    "sync-and-build-browser-vps.py"
    "start-browser-build-vps.py"
    "setup-web-browser-access.sh"
    "setup-browser-on-vps.py"
    "install-browser-vps.py"
    "install-browser-vps-with-password.py"
    "fix-and-start-browser-vps.py"
    "fix-and-setup-browser-vps.py"
    "fix-and-continue-browser-vps.py"
    "continue-browser-development-vps.py"
    "complete-browser-setup-vps.py"
    "check-browser-status-vps.py"
    "check-browser-status-now.py"
    "automated-browser-build.py"
    "apply-browser-modifications-vps.py"
    "BROWSER-*.md"
    "VPS-BROWSER-*.md"
    "WEBSITE-BROWSER-*.md"
    "CHECK-BROWSER-*.sh"
    "CHECK-BROWSER-*.py"
)

# Remove directories
for dir in "${DIRS_TO_REMOVE[@]}"; do
    if [ -d "$dir" ]; then
        echo "  Removing directory: $dir"
        rm -rf "$dir"
    fi
done

# Remove files
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ] || [ -d "$file" ]; then
        echo "  Removing: $file"
        rm -rf "$file"
    fi
done

# Remove browser references from web portal
if [ -f "web-portal/app.py" ]; then
    echo "  Cleaning web-portal/app.py..."
    sed -i '/phazebrowser/d' web-portal/app.py
    sed -i '/PhazeBrowser/d' web-portal/app.py
fi

if [ -f "debian/phaze-vpn/opt/phaze-vpn/web-portal/app.py" ]; then
    echo "  Cleaning debian package web-portal/app.py..."
    sed -i '/phazebrowser/d' debian/phaze-vpn/opt/phaze-vpn/web-portal/app.py
    sed -i '/PhazeBrowser/d' debian/phaze-vpn/opt/phaze-vpn/web-portal/app.py
fi

echo "✅ Browser files removed!"

