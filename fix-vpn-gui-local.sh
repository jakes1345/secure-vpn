#!/bin/bash
# Fix activefg issue in locally installed vpn-gui.py

echo "Fixing vpn-gui.py Tkinter error..."
sudo sed -i 's/activefg=/activeforeground=/g' /opt/phaze-vpn/vpn-gui.py

if grep -q "activefg" /opt/phaze-vpn/vpn-gui.py; then
    echo "❌ Error: Still found activefg in file"
    exit 1
else
    echo "✅ Fixed! All activefg replaced with activeforeground"
    echo ""
    echo "You can now run: phazevpn-client"
fi

