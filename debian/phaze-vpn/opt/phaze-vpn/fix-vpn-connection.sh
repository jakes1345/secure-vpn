#!/bin/bash
# Fix VPN Connection Issues - Updates server addresses and ensures service is running

echo "=========================================="
echo "VPN CONNECTION FIX SCRIPT"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VPN_DIR="/opt/secure-vpn"
DOMAIN="phazevpn.duckdns.org"

# Step 1: Get current public IP
echo "1. Getting current public IP..."
PUBLIC_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || curl -s ipinfo.io/ip)
if [ -z "$PUBLIC_IP" ]; then
    echo -e "${RED}✗ Could not determine public IP${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Public IP: $PUBLIC_IP${NC}"

# Step 2: Check domain resolution
echo ""
echo "2. Checking domain resolution..."
DOMAIN_IP=$(dig +short $DOMAIN 2>/dev/null | tail -1)
if [ -n "$DOMAIN_IP" ]; then
    echo -e "${GREEN}✓ Domain $DOMAIN resolves to: $DOMAIN_IP${NC}"
    if [ "$DOMAIN_IP" = "$PUBLIC_IP" ]; then
        echo -e "${GREEN}✓ Domain IP matches public IP - using domain${NC}"
        SERVER_ADDRESS="$DOMAIN"
    else
        echo -e "${YELLOW}⚠ Domain IP ($DOMAIN_IP) does NOT match public IP ($PUBLIC_IP)${NC}"
        echo -e "${YELLOW}   Using public IP instead${NC}"
        SERVER_ADDRESS="$PUBLIC_IP"
    fi
else
    echo -e "${YELLOW}⚠ Domain $DOMAIN does not resolve - using public IP${NC}"
    SERVER_ADDRESS="$PUBLIC_IP"
fi

echo ""
echo -e "${GREEN}Using server address: $SERVER_ADDRESS${NC}"
echo ""

# Step 3: Ensure OpenVPN service is running
echo "3. Ensuring OpenVPN service is running..."
if ! systemctl is-active --quiet secure-vpn; then
    echo "   Starting OpenVPN service..."
    sudo systemctl start secure-vpn
    sleep 3
    if systemctl is-active --quiet secure-vpn; then
        echo -e "${GREEN}✓ Service started${NC}"
    else
        echo -e "${RED}✗ Failed to start service${NC}"
        echo "   Checking logs..."
        sudo journalctl -u secure-vpn -n 20 --no-pager
    fi
else
    echo -e "${GREEN}✓ Service is already running${NC}"
fi

# Enable auto-start
sudo systemctl enable secure-vpn 2>/dev/null
echo ""

# Step 4: Ensure port 1194 is open in firewall
echo "4. Ensuring port 1194/udp is open in firewall..."
if command -v ufw > /dev/null; then
    if sudo ufw status | grep -q "1194/udp"; then
        echo -e "${GREEN}✓ Port 1194/udp is already allowed${NC}"
    else
        echo "   Adding firewall rule..."
        sudo ufw allow 1194/udp
        echo -e "${GREEN}✓ Port 1194/udp added to firewall${NC}"
    fi
elif command -v firewall-cmd > /dev/null; then
    if sudo firewall-cmd --list-ports | grep -q "1194/udp"; then
        echo -e "${GREEN}✓ Port 1194/udp is already open${NC}"
    else
        echo "   Opening port in firewalld..."
        sudo firewall-cmd --permanent --add-port=1194/udp
        sudo firewall-cmd --reload
        echo -e "${GREEN}✓ Port 1194/udp opened${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No firewall manager detected - please manually open port 1194/udp${NC}"
fi
echo ""

# Step 5: Update vpn-manager.py with correct server address
echo "5. Updating vpn-manager.py configuration..."
if [ -f "$VPN_DIR/vpn-manager.py" ]; then
    # Backup original
    sudo cp "$VPN_DIR/vpn-manager.py" "$VPN_DIR/vpn-manager.py.backup"
    
    # Update server_ip in vpn-manager.py
    if grep -q "server_ip.*:" "$VPN_DIR/vpn-manager.py"; then
        # Use domain if it resolves correctly, otherwise use IP
        sudo sed -i "s|'server_ip': '[^']*'|'server_ip': '$SERVER_ADDRESS'|g" "$VPN_DIR/vpn-manager.py"
        echo -e "${GREEN}✓ Updated vpn-manager.py server address to: $SERVER_ADDRESS${NC}"
    else
        echo -e "${YELLOW}⚠ Could not find server_ip in vpn-manager.py${NC}"
    fi
else
    echo -e "${YELLOW}⚠ vpn-manager.py not found at $VPN_DIR/vpn-manager.py${NC}"
fi
echo ""

# Step 6: Update all existing client configs
echo "6. Updating existing client configs..."
CLIENT_CONFIGS_DIR="$VPN_DIR/client-configs"
if [ -d "$CLIENT_CONFIGS_DIR" ]; then
    UPDATED=0
    for config_file in "$CLIENT_CONFIGS_DIR"/*.ovpn; do
        if [ -f "$config_file" ]; then
            filename=$(basename "$config_file")
            # Check current remote address
            current_remote=$(grep "^remote" "$config_file" | head -1)
            if [ -n "$current_remote" ]; then
                current_ip=$(echo "$current_remote" | awk '{print $2}')
                if [ "$current_ip" != "$SERVER_ADDRESS" ]; then
                    echo "   Updating $filename: $current_ip -> $SERVER_ADDRESS"
                    # Create backup
                    cp "$config_file" "$config_file.backup"
                    # Update remote address
                    sed -i "s|^remote .* 1194|remote $SERVER_ADDRESS 1194|g" "$config_file"
                    UPDATED=$((UPDATED + 1))
                else
                    echo "   $filename already has correct address"
                fi
            fi
        fi
    done
    if [ $UPDATED -gt 0 ]; then
        echo -e "${GREEN}✓ Updated $UPDATED client config(s)${NC}"
    else
        echo -e "${GREEN}✓ All client configs already have correct address${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Client configs directory not found${NC}"
fi
echo ""

# Step 7: Verify OpenVPN is listening
echo "7. Verifying OpenVPN is listening on port 1194..."
sleep 2
if netstat -uln 2>/dev/null | grep -q ":1194 " || ss -uln 2>/dev/null | grep -q ":1194 "; then
    echo -e "${GREEN}✓ OpenVPN is listening on port 1194${NC}"
    if netstat -uln 2>/dev/null | grep ":1194 "; then
        netstat -uln | grep ":1194 "
    else
        ss -uln | grep ":1194 "
    fi
else
    echo -e "${RED}✗ OpenVPN is NOT listening on port 1194${NC}"
    echo "   Checking server config..."
    if [ -f "$VPN_DIR/config/server.conf" ]; then
        echo "   Server config exists, checking for issues..."
        sudo journalctl -u secure-vpn -n 30 --no-pager | tail -20
    fi
fi
echo ""

# Step 8: Summary
echo "=========================================="
echo "FIX COMPLETE"
echo "=========================================="
echo ""
echo -e "${GREEN}Server Address: $SERVER_ADDRESS${NC}"
echo -e "${GREEN}Port: 1194/udp${NC}"
echo ""
echo "Next steps:"
echo "1. Download a client config from the web portal"
echo "2. Verify the config has: remote $SERVER_ADDRESS 1194"
echo "3. Try connecting with OpenVPN Connect"
echo ""
echo "If connection still fails:"
echo "- Check that port 1194/udp is open in your VPS provider's firewall"
echo "- Check OpenVPN logs: sudo journalctl -u secure-vpn -f"
echo "- Run diagnostic: ./diagnose-vpn-connection.sh"
echo ""

