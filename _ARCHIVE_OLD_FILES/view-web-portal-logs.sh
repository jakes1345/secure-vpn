#!/bin/bash
# View web portal logs in real-time for debugging

echo "📋 Viewing PhazeVPN Web Portal logs..."
echo "Press Ctrl+C to stop"
echo ""

# Try different service names
if systemctl list-units --type=service | grep -q "phazevpn-portal.service"; then
    journalctl -u phazevpn-portal.service -f --no-pager
elif systemctl list-units --type=service | grep -q "phazevpn-web-portal.service"; then
    journalctl -u phazevpn-web-portal.service -f --no-pager
elif systemctl list-units --type=service | grep -q "phazevpn-webportal.service"; then
    journalctl -u phazevpn-webportal.service -f --no-pager
else
    echo "⚠️  Web portal service not found. Checking all PhazeVPN services..."
    systemctl list-units --type=service | grep -i phaze
    echo ""
    echo "Try: journalctl -u <service-name> -f"
fi

