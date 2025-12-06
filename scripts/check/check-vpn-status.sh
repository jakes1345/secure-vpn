#!/bin/bash
# Comprehensive VPN Status Check

echo "=========================================="
echo "VPN COMPREHENSIVE STATUS CHECK"
echo "=========================================="
echo ""

VPN_DIR="/opt/secure-vpn"

# 1. Service Status
echo "1. OPENVPN SERVICE STATUS:"
echo "------------------------"
systemctl status secure-vpn --no-pager -l | head -15
echo ""

# 2. Process Check
echo "2. OPENVPN PROCESS:"
echo "------------------"
if pgrep -f "openvpn.*server.conf" > /dev/null; then
    echo "✓ Process is running:"
    ps aux | grep "[o]penvpn.*server.conf"
else
    echo "✗ No OpenVPN process found!"
fi
echo ""

# 3. Port Listening
echo "3. PORT 1194 LISTENING:"
echo "----------------------"
if netstat -uln 2>/dev/null | grep -q ":1194 " || ss -uln 2>/dev/null | grep -q ":1194 "; then
    echo "✓ Port 1194 is listening:"
    netstat -uln 2>/dev/null | grep ":1194" || ss -uln 2>/dev/null | grep ":1194"
else
    echo "✗ Port 1194 is NOT listening!"
fi
echo ""

# 4. Firewall Rules
echo "4. FIREWALL STATUS:"
echo "------------------"
if command -v ufw > /dev/null; then
    echo "UFW Status:"
    ufw status | grep -E "(1194|Status|OpenVPN)" || ufw status numbered | head -10
elif command -v firewall-cmd > /dev/null; then
    echo "Firewalld ports:"
    firewall-cmd --list-ports 2>/dev/null | grep 1194 || echo "Port 1194 not found in firewalld"
else
    echo "No firewall manager detected"
fi
echo ""

# 5. Server Config
echo "5. SERVER CONFIGURATION:"
echo "-----------------------"
if [ -f "$VPN_DIR/config/server.conf" ]; then
    echo "✓ Config file exists"
    echo "Port: $(grep '^port' $VPN_DIR/config/server.conf | head -1)"
    echo "Protocol: $(grep '^proto' $VPN_DIR/config/server.conf | head -1)"
    echo "Server subnet: $(grep '^server' $VPN_DIR/config/server.conf | head -1)"
else
    echo "✗ Server config not found!"
fi
echo ""

# 6. Certificates
echo "6. CERTIFICATES:"
echo "---------------"
CERTS_DIR="$VPN_DIR/certs"
required=("ca.crt" "server.crt" "server.key" "dh.pem" "ta.key")
for cert in "${required[@]}"; do
    if [ -f "$CERTS_DIR/$cert" ]; then
        echo "✓ $cert exists"
    else
        echo "✗ $cert MISSING!"
    fi
done
echo ""

# 7. Server IP in vpn-manager.py
echo "7. VPN-MANAGER.PY CONFIG:"
echo "------------------------"
if [ -f "$VPN_DIR/vpn-manager.py" ]; then
    SERVER_IP=$(grep "server_ip" "$VPN_DIR/vpn-manager.py" | grep -o "'[^']*'" | head -1 | tr -d "'")
    echo "Configured server IP: $SERVER_IP"
else
    echo "✗ vpn-manager.py not found!"
fi
echo ""

# 8. Current Public IP and Domain
echo "8. NETWORK ADDRESSES:"
echo "--------------------"
PUBLIC_IP=$(curl -4 -s ifconfig.me 2>/dev/null || curl -4 -s icanhazip.com 2>/dev/null)
DOMAIN_IP=$(dig +short phazevpn.duckdns.org A 2>/dev/null | tail -1)
echo "Public IPv4: $PUBLIC_IP"
echo "Domain phazevpn.duckdns.org resolves to: $DOMAIN_IP"
if [ "$DOMAIN_IP" = "$PUBLIC_IP" ] && [ -n "$DOMAIN_IP" ]; then
    echo "✓ Domain matches public IP"
else
    echo "⚠ Domain does NOT match public IP"
fi
echo ""

# 9. Recent Client Configs
echo "9. CLIENT CONFIGS:"
echo "-----------------"
if [ -d "$VPN_DIR/client-configs" ]; then
    echo "Recent configs:"
    ls -lt "$VPN_DIR/client-configs"/*.ovpn 2>/dev/null | head -5 | while read line; do
        filename=$(echo "$line" | awk '{print $NF}')
        basename "$filename"
        # Check remote address
        remote=$(grep "^remote" "$filename" 2>/dev/null | head -1)
        if [ -n "$remote" ]; then
            echo "  → $remote"
        fi
    done
else
    echo "✗ Client configs directory not found!"
fi
echo ""

# 10. Recent Logs
echo "10. RECENT OPENVPN LOGS:"
echo "-----------------------"
if [ -f "$VPN_DIR/logs/server.log" ]; then
    echo "Last 10 lines:"
    tail -10 "$VPN_DIR/logs/server.log" | sed 's/^/  /'
elif journalctl -u secure-vpn -n 10 --no-pager 2>/dev/null | grep -q "."; then
    echo "From systemd:"
    journalctl -u secure-vpn -n 10 --no-pager 2>/dev/null | sed 's/^/  /'
else
    echo "No logs found"
fi
echo ""

# 11. Active Connections
echo "11. ACTIVE CONNECTIONS:"
echo "---------------------"
if [ -f "$VPN_DIR/logs/status.log" ]; then
    echo "Status file exists"
    # Try to parse status log if it exists
    tail -20 "$VPN_DIR/logs/status.log" | head -10
else
    echo "No status log found"
fi
echo ""

# Summary
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
if systemctl is-active --quiet secure-vpn && (netstat -uln 2>/dev/null | grep -q ":1194 " || ss -uln 2>/dev/null | grep -q ":1194 "); then
    echo "✓ VPN service is running and listening"
else
    echo "✗ VPN service has issues - check above"
fi

if [ "$DOMAIN_IP" = "$PUBLIC_IP" ] && [ -n "$DOMAIN_IP" ]; then
    echo "✓ Domain is correctly configured"
    echo "→ Use: phazevpn.duckdns.org"
else
    echo "⚠ Use IP address: $PUBLIC_IP"
fi
echo ""

