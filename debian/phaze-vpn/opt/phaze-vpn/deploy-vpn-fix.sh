#!/bin/bash
# Deploy VPN connection fix to VPS

echo "=========================================="
echo "DEPLOY VPN CONNECTION FIX TO VPS"
echo "=========================================="
echo ""

# Check if we have VPS connection info
if [ ! -f "VPS-CONNECTION-INFO.txt" ] && [ -z "$VPS_HOST" ]; then
    echo "VPS connection info not found."
    echo ""
    echo "Please provide VPS connection details:"
    read -p "VPS Host/IP: " VPS_HOST
    read -p "VPS User (usually root): " VPS_USER
    VPS_USER=${VPS_USER:-root}
else
    if [ -f "VPS-CONNECTION-INFO.txt" ]; then
        source VPS-CONNECTION-INFO.txt
    fi
    VPS_USER=${VPS_USER:-root}
fi

if [ -z "$VPS_HOST" ]; then
    echo "Error: VPS host required"
    exit 1
fi

echo "Connecting to: $VPS_USER@$VPS_HOST"
echo ""

# Copy fix scripts to VPS
echo "1. Copying fix scripts to VPS..."
scp fix-vpn-connection.sh diagnose-vpn-connection.sh "$VPS_USER@$VPS_HOST:/tmp/" || {
    echo "Error: Failed to copy scripts. Make sure you can SSH to the VPS."
    exit 1
}
echo "✓ Scripts copied"
echo ""

# Run fix script on VPS
echo "2. Running fix script on VPS..."
ssh "$VPS_USER@$VPS_HOST" "chmod +x /tmp/fix-vpn-connection.sh && sudo bash /tmp/fix-vpn-connection.sh" || {
    echo "Error: Failed to run fix script"
    exit 1
}

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Go to https://phazevpn.duckdns.org"
echo "2. Login and create a new client"
echo "3. Download the client config"
echo "4. Import into OpenVPN Connect"
echo "5. Try connecting!"
echo ""

