#!/bin/bash
# Setup DDoS Protection for PhazeVPN
# Implements Priority 1 protections: fail2ban and iptables rate limiting

set -e

echo "=========================================="
echo "PhazeVPN DDoS Protection Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "✅ Running as root"
echo ""

# Step 1: Install fail2ban
echo "📦 Step 1: Installing fail2ban..."
if ! command -v fail2ban-server &> /dev/null; then
    apt-get update -qq
    apt-get install -y fail2ban
    echo "✅ fail2ban installed"
else
    echo "✅ fail2ban already installed"
fi

# Step 2: Configure fail2ban for OpenVPN
echo ""
echo "🔧 Step 2: Configuring fail2ban for OpenVPN..."

FAIL2BAN_OPENVPN_CONFIG="/etc/fail2ban/jail.d/openvpn.conf"
OPENVPN_LOG="/opt/secure-vpn/logs/server.log"

# Create fail2ban config directory if it doesn't exist
mkdir -p /etc/fail2ban/jail.d

# Create OpenVPN filter
cat > /etc/fail2ban/filter.d/openvpn.conf << 'EOF'
[Definition]
failregex = ^.*\[.*\] Peer Connection Initiated with \[AF_INET\]<HOST>:\d+$
            ^.*\[.*\] Inactivity timeout \(--ping-restart\), exiting$
            ^.*\[.*\] TLS Error: incoming packet authentication failed from \[AF_INET\]<HOST>:\d+$
            ^.*\[.*\] TLS Error: TLS handshake failed from \[AF_INET\]<HOST>:\d+$
            ^.*\[.*\] SIGTERM\[soft,ping-exit\] received, process exiting$
ignoreregex =
EOF

# Create OpenVPN jail configuration
cat > "$FAIL2BAN_OPENVPN_CONFIG" << EOF
[openvpn]
enabled = true
port = 1194
protocol = udp
filter = openvpn
logpath = $OPENVPN_LOG
maxretry = 5
findtime = 600
bantime = 3600
action = iptables[name=OpenVPN, port=1194, protocol=udp]
EOF

echo "✅ fail2ban configured for OpenVPN"
echo "   - Log path: $OPENVPN_LOG"
echo "   - Max retries: 5"
echo "   - Ban time: 1 hour"

# Step 3: Setup iptables rate limiting
echo ""
echo "🔧 Step 3: Setting up iptables rate limiting..."

# Check if rules already exist
if iptables -C INPUT -p udp --dport 1194 -m state --state NEW -m recent --set --name openvpn 2>/dev/null; then
    echo "⚠️  iptables rules already exist, skipping..."
else
    # Allow established connections
    iptables -I INPUT -p udp --dport 1194 -m state --state ESTABLISHED,RELATED -j ACCEPT
    
    # Rate limit new connections (5 per minute per IP)
    iptables -I INPUT -p udp --dport 1194 -m state --state NEW -m recent --set --name openvpn
    iptables -I INPUT -p udp --dport 1194 -m state --state NEW -m recent --update --seconds 60 --hitcount 5 --name openvpn -j DROP
    
    # Rate limit packets (25/sec, burst 50)
    iptables -I INPUT -p udp --dport 1194 -m limit --limit 25/sec --limit-burst 50 -j ACCEPT
    iptables -I INPUT -p udp --dport 1194 -j DROP
    
    echo "✅ iptables rate limiting configured"
    echo "   - New connections: 5 per minute per IP"
    echo "   - Packet rate: 25/second (burst 50)"
fi

# Step 4: Save iptables rules
echo ""
echo "💾 Step 4: Saving iptables rules..."

# Try to save iptables rules (method depends on distro)
if command -v netfilter-persistent &> /dev/null; then
    netfilter-persistent save
    echo "✅ iptables rules saved (netfilter-persistent)"
elif command -v iptables-save &> /dev/null; then
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || \
    iptables-save > /etc/iptables.rules 2>/dev/null || \
    echo "⚠️  Could not auto-save iptables rules. Save manually with:"
    echo "   iptables-save > /etc/iptables/rules.v4"
else
    echo "⚠️  iptables-save not found. Rules will be lost on reboot."
    echo "   Install netfilter-persistent: apt-get install netfilter-persistent"
fi

# Step 5: Start and enable fail2ban
echo ""
echo "🚀 Step 5: Starting fail2ban..."
systemctl enable fail2ban
systemctl restart fail2ban
sleep 2

# Check fail2ban status
if systemctl is-active --quiet fail2ban; then
    echo "✅ fail2ban is running"
else
    echo "❌ Warning: fail2ban failed to start. Check logs: journalctl -u fail2ban"
fi

# Step 6: Verify configuration
echo ""
echo "🔍 Step 6: Verifying configuration..."

# Check fail2ban jails
echo ""
echo "Active fail2ban jails:"
fail2ban-client status 2>/dev/null | grep "Jail list" || echo "   (No jails active yet)"

# Check iptables rules
echo ""
echo "iptables rules for port 1194:"
iptables -L INPUT -n -v | grep -A 5 "1194" || echo "   (No rules found - this may be normal if UFW is managing rules)"

# Step 7: Create monitoring script
echo ""
echo "📊 Step 7: Creating monitoring script..."

MONITOR_SCRIPT="/opt/secure-vpn/scripts/monitor-ddos.sh"
mkdir -p /opt/secure-vpn/scripts

cat > "$MONITOR_SCRIPT" << 'EOF'
#!/bin/bash
# Quick DDoS monitoring script

echo "=== PhazeVPN DDoS Protection Status ==="
echo ""

# fail2ban status
echo "📋 fail2ban Status:"
if systemctl is-active --quiet fail2ban; then
    echo "   ✅ Running"
    echo ""
    echo "   Banned IPs:"
    fail2ban-client status openvpn 2>/dev/null | grep "Banned IP list" || echo "   (None)"
else
    echo "   ❌ Not running"
fi

echo ""

# Connection stats
echo "📊 Current Connections:"
if [ -f /opt/secure-vpn/logs/status.log ]; then
    echo "   Active clients: $(grep -c "^CLIENT_LIST" /opt/secure-vpn/logs/status.log 2>/dev/null || echo "0")"
else
    echo "   (Status log not found)"
fi

echo ""

# Network stats
echo "🌐 Network Statistics (port 1194):"
if command -v ss &> /dev/null; then
    ss -un | grep ":1194" | wc -l | xargs echo "   UDP connections:"
elif command -v netstat &> /dev/null; then
    netstat -un | grep ":1194" | wc -l | xargs echo "   UDP connections:"
else
    echo "   (ss/netstat not available)"
fi

echo ""

# System resources
echo "💻 System Resources:"
echo "   CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "   Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
EOF

chmod +x "$MONITOR_SCRIPT"
echo "✅ Monitoring script created: $MONITOR_SCRIPT"

# Summary
echo ""
echo "=========================================="
echo "✅ DDoS Protection Setup Complete!"
echo "=========================================="
echo ""
echo "📋 What was configured:"
echo "   ✅ fail2ban installed and configured"
echo "   ✅ iptables rate limiting rules added"
echo "   ✅ Monitoring script created"
echo ""
echo "🔍 To check status, run:"
echo "   $MONITOR_SCRIPT"
echo ""
echo "📊 To view fail2ban status:"
echo "   fail2ban-client status openvpn"
echo ""
echo "⚠️  Important Notes:"
echo "   1. Test your VPN connection to ensure rate limits don't block legitimate users"
echo "   2. Adjust rate limits in this script if needed (lines 50-55)"
echo "   3. Monitor logs: tail -f /opt/secure-vpn/logs/server.log"
echo "   4. Check banned IPs: fail2ban-client status openvpn"
echo ""
echo "🔄 To unban an IP:"
echo "   fail2ban-client set openvpn unbanip <IP_ADDRESS>"
echo ""

