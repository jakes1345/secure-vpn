#!/bin/bash
# Quick script to open port 8081 for the download server
# Run with: sudo ./open-download-port.sh

echo "=========================================="
echo "Opening Port 8081 for Download Server"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Check if UFW is active
if systemctl is-active --quiet ufw 2>/dev/null || ufw status | grep -q "Status: active"; then
    echo "UFW is active - using UFW to open port..."
    ufw allow 8081/tcp
    if [ $? -eq 0 ]; then
        echo "✅ Port 8081 opened via UFW!"
    else
        echo "❌ Failed to open port 8081 via UFW"
        exit 1
    fi
else
    echo "UFW not active - using iptables..."
    # Open port 8081
    iptables -D INPUT -p tcp --dport 8081 -j ACCEPT 2>/dev/null
    iptables -I INPUT -p tcp --dport 8081 -j ACCEPT
    
    if [ $? -eq 0 ]; then
        echo "✅ Port 8081 opened via iptables!"
    else
        echo "❌ Failed to open port 8081"
        exit 1
    fi
fi

echo ""
echo "Your download server should now be accessible from:"
echo "  - Local network: http://$(hostname -I | awk '{print $1}'):8081"
echo "  - This device: http://localhost:8081"
echo ""

