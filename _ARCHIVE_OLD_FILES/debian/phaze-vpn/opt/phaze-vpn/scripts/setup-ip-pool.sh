#!/bin/bash
# Setup Multiple Exit IPs for VPN Clients
# Each VPN user gets their own unique public IP address

set -e

VPN_DIR="/opt/secure-vpn"
SCRIPTS_DIR="$VPN_DIR/scripts"
LOGS_DIR="$VPN_DIR/logs"

echo "=========================================="
echo "🌐 Setting Up Multiple Exit IP Pool"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (sudo $0)"
    exit 1
fi

# Step 1: Get exit IPs from user
echo "📝 Step 1: Configure Exit IP Addresses"
echo ""
echo "Enter your exit IP addresses (one per line, press Enter twice when done):"
echo "Example:"
echo "  15.204.11.19"
echo "  15.204.11.20"
echo "  15.204.11.21"
echo ""

EXIT_IPS=()
while IFS= read -r line; do
    if [ -z "$line" ]; then
        break
    fi
    EXIT_IPS+=("$line")
done

if [ ${#EXIT_IPS[@]} -eq 0 ]; then
    echo "⚠️  No IPs entered. Exiting."
    exit 1
fi

echo ""
echo "✅ Configured ${#EXIT_IPS[@]} exit IPs:"
for ip in "${EXIT_IPS[@]}"; do
    echo "   - $ip"
done
echo ""

# Step 2: Create directories
echo "📁 Step 2: Creating directories..."
mkdir -p "$SCRIPTS_DIR"
mkdir -p "$LOGS_DIR"
touch "$LOGS_DIR/ip-assignments.log"
echo "✅ Directories created"
echo ""

# Step 3: Create client-connect script
echo "📝 Step 3: Creating client-connect script..."

# Build IP array string for script
IP_ARRAY_STRING=$(printf '"%s" ' "${EXIT_IPS[@]}" | sed 's/ $//')

cat > "$SCRIPTS_DIR/client-connect-ip-pool.sh" << 'SCRIPT'
#!/bin/bash
# Assign random exit IP to VPN client

VPN_CLIENT_IP="$ifconfig_pool_remote_ip"
CLIENT_NAME="$common_name"

# Exit IP pool (configured by setup script)
EXIT_IPS=(EXIT_IP_LIST_PLACEHOLDER)

# Pick random IP from pool
RANDOM_IP=${EXIT_IPS[$RANDOM % ${#EXIT_IPS[@]}]}

# Assign SNAT rule
if [ -n "$VPN_CLIENT_IP" ] && [ -n "$RANDOM_IP" ]; then
    iptables -t nat -A POSTROUTING -s "$VPN_CLIENT_IP" -o eth0 -j SNAT --to-source "$RANDOM_IP" 2>/dev/null || \
    iptables -t nat -A POSTROUTING -s "$VPN_CLIENT_IP" -j SNAT --to-source "$RANDOM_IP" 2>/dev/null || true
    
    echo "$(date '+%Y-%m-%d %H:%M:%S'): Client $CLIENT_NAME ($VPN_CLIENT_IP) → Exit IP $RANDOM_IP" >> /opt/secure-vpn/logs/ip-assignments.log
fi

exit 0
SCRIPT

# Replace placeholder with actual IPs
sed -i "s|EXIT_IP_LIST_PLACEHOLDER|${IP_ARRAY_STRING}|" "$SCRIPTS_DIR/client-connect-ip-pool.sh"
chmod +x "$SCRIPTS_DIR/client-connect-ip-pool.sh"
echo "✅ Client-connect script created"
echo ""

# Step 4: Create client-disconnect script
echo "📝 Step 4: Creating client-disconnect script..."

cat > "$SCRIPTS_DIR/client-disconnect-ip-pool.sh" << 'SCRIPT'
#!/bin/bash
# Remove SNAT rules when client disconnects

VPN_CLIENT_IP="$ifconfig_pool_remote_ip"
CLIENT_NAME="$common_name"

# Exit IP pool
EXIT_IPS=(EXIT_IP_LIST_PLACEHOLDER)

# Remove SNAT rules for all possible exit IPs
for EXIT_IP in "${EXIT_IPS[@]}"; do
    iptables -t nat -D POSTROUTING -s "$VPN_CLIENT_IP" -o eth0 -j SNAT --to-source "$EXIT_IP" 2>/dev/null || \
    iptables -t nat -D POSTROUTING -s "$VPN_CLIENT_IP" -j SNAT --to-source "$EXIT_IP" 2>/dev/null || true
done

echo "$(date '+%Y-%m-%d %H:%M:%S'): Client $CLIENT_NAME ($VPN_CLIENT_IP) disconnected" >> /opt/secure-vpn/logs/ip-assignments.log

exit 0
SCRIPT

# Replace placeholder
sed -i "s|EXIT_IP_LIST_PLACEHOLDER|${IP_ARRAY_STRING}|" "$SCRIPTS_DIR/client-disconnect-ip-pool.sh"
chmod +x "$SCRIPTS_DIR/client-disconnect-ip-pool.sh"
echo "✅ Client-disconnect script created"
echo ""

# Step 5: Create management script
echo "📝 Step 5: Creating management script..."

cat > "$SCRIPTS_DIR/show-ip-assignments.sh" << 'EOF'
#!/bin/bash
# Show current IP assignments

echo "=========================================="
echo "🌐 Current IP Assignments"
echo "=========================================="
echo ""
echo "Active SNAT Rules:"
iptables -t nat -L POSTROUTING -n -v | grep SNAT || echo "  No active assignments"
echo ""
echo "Recent Assignments (from log):"
tail -20 /opt/secure-vpn/logs/ip-assignments.log 2>/dev/null || echo "  No log entries yet"
echo ""
EOF

chmod +x "$SCRIPTS_DIR/show-ip-assignments.sh"
echo "✅ Management script created"
echo ""

# Step 6: Update OpenVPN config
echo "📝 Step 6: Updating OpenVPN configuration..."

CONFIG_FILE="$VPN_DIR/config/server.conf"

if [ -f "$CONFIG_FILE" ]; then
    # Backup config
    cp "$CONFIG_FILE" "${CONFIG_FILE}.backup-$(date +%Y%m%d-%H%M%S)"
    
    # Remove old client-connect/disconnect lines
    sed -i '/client-connect.*ip-pool/d' "$CONFIG_FILE"
    sed -i '/client-disconnect.*ip-pool/d' "$CONFIG_FILE"
    
    # Add new lines before the last line
    sed -i "\$a\\
# IP Pool - Multiple Exit IPs\\
client-connect $SCRIPTS_DIR/client-connect-ip-pool.sh\\
client-disconnect $SCRIPTS_DIR/client-disconnect-ip-pool.sh\\
script-security 2" "$CONFIG_FILE"
    
    echo "✅ OpenVPN config updated"
else
    echo "⚠️  Config file not found at $CONFIG_FILE"
    echo "   Manually add to server.conf:"
    echo "   client-connect $SCRIPTS_DIR/client-connect-ip-pool.sh"
    echo "   client-disconnect $SCRIPTS_DIR/client-disconnect-ip-pool.sh"
    echo "   script-security 2"
fi
echo ""

# Step 7: Test configuration
echo "🧪 Step 7: Testing configuration..."

# Check if IPs are configured on system
echo "Checking configured IPs on system:"
ip addr show | grep "inet " | grep -v "127.0.0.1" || echo "  Run 'ip addr show' to see all IPs"
echo ""

# Summary
echo "=========================================="
echo "✅ IP Pool Setup Complete!"
echo "=========================================="
echo ""
echo "Exit IPs configured:"
for ip in "${EXIT_IPS[@]}"; do
    echo "   ✅ $ip"
done
echo ""
echo "Next steps:"
echo "1. Make sure all exit IPs are added to your VPS network interface"
echo "2. Restart OpenVPN service:"
echo "   systemctl restart openvpn@server"
echo "   # or"
echo "   systemctl restart secure-vpn"
echo ""
echo "3. View current assignments:"
echo "   $SCRIPTS_DIR/show-ip-assignments.sh"
echo ""
echo "4. Check logs:"
echo "   tail -f $LOGS_DIR/ip-assignments.log"
echo ""
echo "Each VPN client will now get a random exit IP from your pool! 🎉"
echo ""

