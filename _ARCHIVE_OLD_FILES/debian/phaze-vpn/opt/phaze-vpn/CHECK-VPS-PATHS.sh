#!/bin/bash
# Quick check for VPN paths on VPS
# Run this on your VPS to find where everything is

echo "🔍 Checking common VPN locations..."

# Common paths
PATHS=(
    "/opt/phaze-vpn"
    "/opt/secure-vpn"
    "/etc/openvpn"
    "/usr/local/phaze-vpn"
    "$HOME/phaze-vpn"
)

for path in "${PATHS[@]}"; do
    if [ -d "$path" ]; then
        echo "✅ Found: $path"
        if [ -f "$path/server.conf" ] || [ -f "$path/config/server.conf" ]; then
            echo "   📄 Has server.conf!"
        fi
    fi
done

# Check for OpenVPN service
echo ""
echo "🔍 Checking OpenVPN service..."
systemctl list-units | grep -i openvpn || echo "No OpenVPN service found"

# Check running OpenVPN processes
echo ""
echo "🔍 Checking running OpenVPN processes..."
ps aux | grep openvpn | grep -v grep || echo "No OpenVPN processes running"

# Find server.conf
echo ""
echo "🔍 Searching for server.conf..."
find /opt /etc /usr/local -name "server.conf" 2>/dev/null | head -5

