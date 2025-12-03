#!/bin/bash
# Quick fix for desktop icon - run with sudo

echo "=== Fixing PhazeVPN Desktop Icon ==="
echo ""

# Fix desktop file
DESKTOP_FILE="/usr/share/applications/phaze-vpn.desktop"
ICON_PATH="/opt/phaze-vpn/assets/icons/phazevpn-256x256.png"

if [ -f "$DESKTOP_FILE" ]; then
    # Update Icon line
    sed -i "s|Icon=.*|Icon=$ICON_PATH|" "$DESKTOP_FILE"
    echo "✅ Updated desktop file icon path"
    
    # Also add to system pixmaps for better compatibility
    if [ -f "$ICON_PATH" ] && [ ! -f "/usr/share/pixmaps/phazevpn.png" ]; then
        cp "$ICON_PATH" /usr/share/pixmaps/phazevpn.png
        echo "✅ Copied icon to /usr/share/pixmaps/"
    fi
    
    # Update desktop database
    update-desktop-database /usr/share/applications/ 2>/dev/null
    echo "✅ Updated desktop database"
    
    echo ""
    echo "✅ Icon fixed! The colorful logo should now show:"
    echo "   - In the application menu"
    echo "   - In the taskbar when running"
    echo "   - In the GUI window"
    echo ""
    echo "You may need to:"
    echo "  - Log out and back in"
    echo "  - Or restart your desktop environment"
else
    echo "❌ Desktop file not found: $DESKTOP_FILE"
fi

