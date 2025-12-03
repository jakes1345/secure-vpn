#!/bin/bash
# One-command fix - copy this entire script and paste into VPS

# This script runs directly on the VPS
# SSH in first: ssh root@15.204.11.19

set -e

echo "=========================================="
echo "VPN CONNECTION FIX"
echo "=========================================="
echo ""

VPN_DIR="/opt/secure-vpn"
DOMAIN="phazevpn.duckdns.org"

# Step 1: Start OpenVPN
echo "1. Starting OpenVPN service..."
sudo systemctl start secure-vpn
sudo systemctl enable secure-vpn
sleep 2
if systemctl is-active --quiet secure-vpn; then
    echo "✓ OpenVPN service is running"
else
    echo "✗ Failed to start OpenVPN"
    sudo journalctl -u secure-vpn -n 20
    exit 1
fi
echo ""

# Step 2: Open firewall
echo "2. Opening port 1194/udp in firewall..."
sudo ufw allow 1194/udp 2>/dev/null || true
if command -v firewall-cmd > /dev/null; then
    sudo firewall-cmd --permanent --add-port=1194/udp 2>/dev/null || true
    sudo firewall-cmd --reload 2>/dev/null || true
fi
echo "✓ Firewall updated"
echo ""

# Step 3: Get server address
echo "3. Getting server address..."
cd "$VPN_DIR" || { echo "✗ VPN directory not found: $VPN_DIR"; exit 1; }

PUBLIC_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || curl -s ipinfo.io/ip)
DOMAIN_IP=$(dig +short "$DOMAIN" 2>/dev/null | tail -1)

if [ -z "$PUBLIC_IP" ]; then
    echo "✗ Could not determine public IP"
    exit 1
fi

echo "   Public IP: $PUBLIC_IP"
if [ -n "$DOMAIN_IP" ]; then
    echo "   Domain IP: $DOMAIN_IP"
    if [ "$DOMAIN_IP" = "$PUBLIC_IP" ]; then
        SERVER_ADDRESS="$DOMAIN"
        echo "   ✓ Using domain: $SERVER_ADDRESS"
    else
        SERVER_ADDRESS="$PUBLIC_IP"
        echo "   ⚠ Domain doesn't match IP, using: $SERVER_ADDRESS"
    fi
else
    SERVER_ADDRESS="$PUBLIC_IP"
    echo "   Using IP: $SERVER_ADDRESS"
fi
echo ""

# Step 4: Update vpn-manager.py
echo "4. Updating vpn-manager.py..."
if [ -f "vpn-manager.py" ]; then
    cp vpn-manager.py vpn-manager.py.backup
    sed -i "s|'server_ip': '[^']*'|'server_ip': '$SERVER_ADDRESS'|g" vpn-manager.py
    echo "✓ Updated vpn-manager.py with: $SERVER_ADDRESS"
else
    echo "⚠ vpn-manager.py not found"
fi
echo ""

# Step 5: Update all client configs
echo "5. Updating client configs..."
if [ -d "client-configs" ]; then
    UPDATED=0
    for config in client-configs/*.ovpn; do
        if [ -f "$config" ]; then
            filename=$(basename "$config")
            current_remote=$(grep "^remote" "$config" | head -1)
            if [ -n "$current_remote" ]; then
                current_ip=$(echo "$current_remote" | awk '{print $2}')
                if [ "$current_ip" != "$SERVER_ADDRESS" ]; then
                    # Backup
                    cp "$config" "$config.backup"
                    # Update
                    sed -i "s|^remote .* 1194|remote $SERVER_ADDRESS 1194|g" "$config"
                    echo "   ✓ Updated $filename"
                    UPDATED=$((UPDATED + 1))
                fi
            fi
        fi
    done
    if [ $UPDATED -gt 0 ]; then
        echo "✓ Updated $UPDATED client config(s)"
    else
        echo "✓ All client configs already correct"
    fi
else
    echo "⚠ client-configs directory not found"
fi
echo ""

# Step 6: Verify
echo "6. Verifying..."
sleep 2
if netstat -uln 2>/dev/null | grep -q ":1194 " || ss -uln 2>/dev/null | grep -q ":1194 "; then
    echo "✓ OpenVPN is listening on port 1194"
    netstat -uln 2>/dev/null | grep ":1194" || ss -uln 2>/dev/null | grep ":1194"
else
    echo "✗ OpenVPN is NOT listening on port 1194"
    echo "   Checking logs..."
    sudo journalctl -u secure-vpn -n 20 --no-pager
fi
echo ""

# Summary
echo "=========================================="
echo "FIX COMPLETE!"
echo "=========================================="
echo ""
echo "Server Address: $SERVER_ADDRESS"
echo "Port: 1194/udp"
echo ""
echo "Next steps:"
echo "1. Go to: https://phazevpn.duckdns.org"
echo "2. Create/download a new client config"
echo "3. Import into OpenVPN Connect"
echo "4. Connect!"
echo ""

