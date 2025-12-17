#!/bin/bash
# Connect to VPS and fix VPN connection issues

set -e

# VPS Connection Details
VPS_IP="15.204.11.19"
VPS_USER="root"
DOMAIN="phazevpn.duckdns.org"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "VPN CONNECTION FIX - DEPLOY TO VPS"
echo "=========================================="
echo ""
echo "VPS: $VPS_USER@$VPS_IP"
echo "Domain: $DOMAIN"
echo ""

# Step 1: Test SSH connection
echo "1. Testing SSH connection..."
if ssh -o ConnectTimeout=10 -o BatchMode=yes "$VPS_USER@$VPS_IP" "echo 'Connected'" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH connection works${NC}"
else
    echo -e "${YELLOW}⚠ SSH connection requires password or key${NC}"
    echo "   You'll be prompted for password: 96EAkcN3Dw4c"
    echo ""
fi

# Step 2: Copy fix scripts to VPS
echo "2. Uploading fix scripts to VPS..."
scp fix-vpn-connection.sh diagnose-vpn-connection.sh "$VPS_USER@$VPS_IP:/tmp/" || {
    echo -e "${RED}✗ Failed to upload scripts${NC}"
    echo "   Make sure SSH is working: ssh $VPS_USER@$VPS_IP"
    exit 1
}
echo -e "${GREEN}✓ Scripts uploaded${NC}"
echo ""

# Step 3: Run diagnostic first
echo "3. Running diagnostic on VPS..."
ssh "$VPS_USER@$VPS_IP" "chmod +x /tmp/diagnose-vpn-connection.sh && sudo bash /tmp/diagnose-vpn-connection.sh"
echo ""

# Step 4: Run fix script
echo "4. Running fix script on VPS..."
echo -e "${YELLOW}This will:${NC}"
echo "   - Start OpenVPN service if needed"
echo "   - Open port 1194/udp in firewall"
echo "   - Update all client configs with correct server address"
echo "   - Update vpn-manager.py configuration"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

ssh "$VPS_USER@$VPS_IP" "chmod +x /tmp/fix-vpn-connection.sh && sudo bash /tmp/fix-vpn-connection.sh"
echo ""

# Step 5: Verify VPN directory exists
echo "5. Verifying VPN setup..."
VPN_DIR="/opt/secure-vpn"
ssh "$VPS_USER@$VPS_IP" "test -d $VPN_DIR && echo 'VPN directory exists' || echo 'VPN directory missing!'"
echo ""

# Step 6: Get updated server address
echo "6. Getting current server address..."
SERVER_ADDRESS=$(ssh "$VPS_USER@$VPS_IP" "curl -s ifconfig.me 2>/dev/null || echo 'Could not determine'")
DOMAIN_IP=$(ssh "$VPS_USER@$VPS_IP" "dig +short $DOMAIN 2>/dev/null | tail -1 || echo ''")

if [ "$DOMAIN_IP" = "$SERVER_ADDRESS" ] && [ -n "$DOMAIN_IP" ]; then
    FINAL_ADDRESS="$DOMAIN"
else
    FINAL_ADDRESS="$SERVER_ADDRESS"
fi

echo "   Public IP: $SERVER_ADDRESS"
if [ -n "$DOMAIN_IP" ]; then
    echo "   Domain IP: $DOMAIN_IP"
fi
echo "   Using: $FINAL_ADDRESS"
echo ""

# Step 7: Check OpenVPN status
echo "7. Checking OpenVPN service status..."
ssh "$VPS_USER@$VPS_IP" "sudo systemctl status secure-vpn --no-pager -l | head -15 || echo 'Service check failed'"
echo ""

# Step 8: Check port listening
echo "8. Checking if port 1194 is listening..."
ssh "$VPS_USER@$VPS_IP" "sudo netstat -uln | grep ':1194' || sudo ss -uln | grep ':1194' || echo 'Port not listening'"
echo ""

# Step 9: Show recent client configs
echo "9. Recent client configs on VPS:"
ssh "$VPS_USER@$VPS_IP" "ls -lt $VPN_DIR/client-configs/*.ovpn 2>/dev/null | head -5 | awk '{print \$NF}' | xargs -I {} basename {} || echo 'No client configs found'"
echo ""

# Summary
echo "=========================================="
echo "FIX COMPLETE!"
echo "=========================================="
echo ""
echo -e "${GREEN}Server Address: $FINAL_ADDRESS${NC}"
echo -e "${GREEN}Port: 1194/udp${NC}"
echo ""
echo "Next steps:"
echo "1. Go to: https://$DOMAIN"
echo "2. Login to the web portal"
echo "3. Create a new client (or update existing one)"
echo "4. Download the .ovpn config file"
echo "5. Import into OpenVPN Connect app"
echo "6. Try connecting!"
echo ""
echo "If connection fails:"
echo "- Check that port 1194/udp is open in OVH firewall (control panel)"
echo "- View logs: ssh $VPS_USER@$VPS_IP 'sudo journalctl -u secure-vpn -f'"
echo "- Run diagnostic: ssh $VPS_USER@$VPS_IP 'sudo bash /tmp/diagnose-vpn-connection.sh'"
echo ""

