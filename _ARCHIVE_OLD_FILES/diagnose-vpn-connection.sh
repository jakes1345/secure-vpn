#!/bin/bash
# VPN Connection Diagnostic Script

echo "=========================================="
echo "VPN CONNECTION DIAGNOSTIC"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: OpenVPN Service Status
echo "1. Checking OpenVPN Service Status..."
if systemctl is-active --quiet secure-vpn; then
    echo -e "${GREEN}✓ OpenVPN service is running${NC}"
else
    echo -e "${RED}✗ OpenVPN service is NOT running${NC}"
    echo "   Attempting to start..."
    sudo systemctl start secure-vpn
    sleep 2
    if systemctl is-active --quiet secure-vpn; then
        echo -e "${GREEN}✓ Service started successfully${NC}"
    else
        echo -e "${RED}✗ Failed to start service${NC}"
    fi
fi
echo ""

# Check 2: OpenVPN Process
echo "2. Checking OpenVPN Process..."
if pgrep -f "openvpn.*server.conf" > /dev/null; then
    echo -e "${GREEN}✓ OpenVPN process is running${NC}"
    pgrep -f "openvpn.*server.conf" | xargs ps -p
else
    echo -e "${RED}✗ No OpenVPN process found${NC}"
fi
echo ""

# Check 3: Port 1194 Listening
echo "3. Checking if port 1194 is listening..."
if netstat -uln | grep -q ":1194 "; then
    echo -e "${GREEN}✓ Port 1194 is listening${NC}"
    netstat -uln | grep ":1194 "
elif ss -uln | grep -q ":1194 "; then
    echo -e "${GREEN}✓ Port 1194 is listening${NC}"
    ss -uln | grep ":1194 "
else
    echo -e "${RED}✗ Port 1194 is NOT listening${NC}"
fi
echo ""

# Check 4: Firewall Rules
echo "4. Checking Firewall Rules..."
if command -v ufw > /dev/null; then
    echo "UFW Status:"
    sudo ufw status | grep -E "(1194|OpenVPN)" || echo -e "${YELLOW}⚠ No specific OpenVPN rules found${NC}"
    
    # Check if port 1194 is allowed
    if sudo ufw status | grep -q "1194"; then
        echo -e "${GREEN}✓ Port 1194 is allowed in firewall${NC}"
    else
        echo -e "${YELLOW}⚠ Port 1194 might not be explicitly allowed${NC}"
        echo "   Run: sudo ufw allow 1194/udp"
    fi
elif command -v firewall-cmd > /dev/null; then
    echo "Firewalld Status:"
    sudo firewall-cmd --list-ports | grep -q "1194" && echo -e "${GREEN}✓ Port 1194 is open${NC}" || echo -e "${RED}✗ Port 1194 is NOT open${NC}"
else
    echo -e "${YELLOW}⚠ No firewall manager detected (ufw/firewalld)${NC}"
fi
echo ""

# Check 5: Server Configuration
echo "5. Checking Server Configuration..."
VPN_DIR="/opt/secure-vpn"
if [ -d "$VPN_DIR" ]; then
    CONFIG_FILE="$VPN_DIR/config/server.conf"
    if [ -f "$CONFIG_FILE" ]; then
        echo -e "${GREEN}✓ Server config found: $CONFIG_FILE${NC}"
        echo "   Port: $(grep '^port' $CONFIG_FILE | head -1)"
        echo "   Protocol: $(grep '^proto' $CONFIG_FILE | head -1)"
        echo "   Server IP range: $(grep '^server' $CONFIG_FILE | head -1)"
    else
        echo -e "${RED}✗ Server config not found: $CONFIG_FILE${NC}"
    fi
else
    echo -e "${YELLOW}⚠ VPN directory not found: $VPN_DIR${NC}"
fi
echo ""

# Check 6: Certificates
echo "6. Checking Certificates..."
if [ -d "$VPN_DIR/certs" ]; then
    CERTS_DIR="$VPN_DIR/certs"
    required_certs=("ca.crt" "server.crt" "server.key" "dh.pem" "ta.key")
    all_present=true
    for cert in "${required_certs[@]}"; do
        if [ -f "$CERTS_DIR/$cert" ]; then
            echo -e "${GREEN}✓ $cert exists${NC}"
        else
            echo -e "${RED}✗ $cert MISSING${NC}"
            all_present=false
        fi
    done
    if [ "$all_present" = false ]; then
        echo -e "${RED}✗ Some certificates are missing!${NC}"
    fi
else
    echo -e "${RED}✗ Certificates directory not found${NC}"
fi
echo ""

# Check 7: Get Public IP
echo "7. Getting Public IP Address..."
PUBLIC_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || curl -s ipinfo.io/ip)
if [ -n "$PUBLIC_IP" ]; then
    echo -e "${GREEN}✓ Public IP: $PUBLIC_IP${NC}"
else
    echo -e "${YELLOW}⚠ Could not determine public IP${NC}"
fi
echo ""

# Check 8: Get Domain (if configured)
echo "8. Checking Domain Configuration..."
DOMAIN="phazevpn.duckdns.org"
if [ -n "$DOMAIN" ]; then
    DOMAIN_IP=$(dig +short $DOMAIN 2>/dev/null | tail -1)
    if [ -n "$DOMAIN_IP" ]; then
        echo -e "${GREEN}✓ Domain $DOMAIN resolves to: $DOMAIN_IP${NC}"
        if [ "$DOMAIN_IP" = "$PUBLIC_IP" ]; then
            echo -e "${GREEN}✓ Domain IP matches public IP${NC}"
        else
            echo -e "${YELLOW}⚠ Domain IP ($DOMAIN_IP) does NOT match public IP ($PUBLIC_IP)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Domain $DOMAIN does not resolve${NC}"
    fi
fi
echo ""

# Check 9: Check Recent Client Configs
echo "9. Checking Recent Client Configs..."
CLIENT_CONFIGS_DIR="$VPN_DIR/client-configs"
if [ -d "$CLIENT_CONFIGS_DIR" ]; then
    echo "Recent client configs:"
    ls -lt "$CLIENT_CONFIGS_DIR"/*.ovpn 2>/dev/null | head -5 | while read line; do
        filename=$(echo "$line" | awk '{print $NF}')
        echo "   - $(basename $filename)"
        # Check remote address
        remote=$(grep "^remote" "$filename" | head -1)
        if [ -n "$remote" ]; then
            echo "     $remote"
            # Check if it matches current IP
            remote_ip=$(echo "$remote" | awk '{print $2}')
            if [ "$remote_ip" = "$PUBLIC_IP" ] || [ "$remote_ip" = "$DOMAIN" ]; then
                echo -e "     ${GREEN}✓ Remote address looks correct${NC}"
            else
                echo -e "     ${RED}✗ Remote address ($remote_ip) might be wrong!${NC}"
                echo -e "     ${YELLOW}   Should be: $PUBLIC_IP or $DOMAIN${NC}"
            fi
        fi
    done
else
    echo -e "${YELLOW}⚠ Client configs directory not found${NC}"
fi
echo ""

# Check 10: OpenVPN Logs
echo "10. Checking Recent OpenVPN Logs..."
LOG_FILE="$VPN_DIR/logs/server.log"
if [ -f "$LOG_FILE" ]; then
    echo "Last 10 lines of server.log:"
    tail -10 "$LOG_FILE" | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠ Log file not found: $LOG_FILE${NC}"
fi
echo ""

# Summary and Recommendations
echo "=========================================="
echo "SUMMARY & RECOMMENDATIONS"
echo "=========================================="
echo ""

# Check if everything is OK
ISSUES=0

if ! systemctl is-active --quiet secure-vpn; then
    echo -e "${RED}✗ ISSUE: OpenVPN service is not running${NC}"
    echo "   Fix: sudo systemctl start secure-vpn && sudo systemctl enable secure-vpn"
    ISSUES=$((ISSUES + 1))
fi

if ! netstat -uln 2>/dev/null | grep -q ":1194 " && ! ss -uln 2>/dev/null | grep -q ":1194 "; then
    echo -e "${RED}✗ ISSUE: Port 1194 is not listening${NC}"
    echo "   Fix: Check OpenVPN service and configuration"
    ISSUES=$((ISSUES + 1))
fi

if [ -n "$PUBLIC_IP" ]; then
    echo -e "${GREEN}✓ Use this address in client configs:${NC}"
    echo "   - IP: $PUBLIC_IP"
    if [ -n "$DOMAIN" ]; then
        echo "   - Domain: $DOMAIN (recommended)"
    fi
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! VPN should be working.${NC}"
    echo ""
    echo "If clients still can't connect:"
    echo "1. Check client config remote address matches: $PUBLIC_IP or $DOMAIN"
    echo "2. Check firewall allows port 1194/udp from outside"
    echo "3. Check client certificates are valid"
else
    echo ""
    echo -e "${YELLOW}⚠ Found $ISSUES issue(s) that need to be fixed${NC}"
fi

echo ""

