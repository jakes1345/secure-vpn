#!/bin/bash
# Tor Integration Setup Script
# Routes VPN traffic through Tor for maximum anonymity
# Creates: Your Device → VPN → Tor → Destination
# Makes it nearly impossible to correlate traffic

set -e

echo "🧅 Setting up Tor Integration..."
echo ""
echo "This routes your VPN traffic through Tor."
echo "Creates: Your Device → VPN → Tor → Destination"
echo ""
echo "Benefits:"
echo "  - Even if VPN is compromised, Tor provides anonymity"
echo "  - Multiple layers of protection"
echo "  - Extremely difficult to correlate traffic"
echo ""

# Check if Tor is installed
if ! command -v tor &> /dev/null; then
    echo "📦 Installing Tor..."
    
    if [ -f /etc/debian_version ]; then
        sudo apt-get update
        sudo apt-get install -y tor
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y tor
    elif [ -f /etc/arch-release ]; then
        sudo pacman -S tor
    else
        echo "⚠️  Please install Tor manually from: https://www.torproject.org/"
    fi
fi

# Create Tor configuration directory
TOR_DIR="$(pwd)/tor-config"
mkdir -p "$TOR_DIR"

# Create Tor configuration for VPN routing
cat > "$TOR_DIR/torrc-vpn" << EOF
# Tor Configuration for VPN Integration
# Routes VPN traffic through Tor

# Tor will listen on this port (VPN will route through it)
SocksPort 127.0.0.1:9050
SocksPolicy accept 127.0.0.1
SocksPolicy reject *

# Don't expose Tor as a relay
ORPort 0
DirPort 0
ExitPolicy reject *:*

# Security settings
SafeLogging 1
DisableDebuggerAttachment 1

# Use bridges for extra anonymity (optional)
# Bridge obfs4 IP:PORT FINGERPRINT [fingerprint]
# Get bridges from: https://bridges.torproject.org/

# Logging (minimal for privacy)
Log notice file /var/log/tor/tor.log
Log notice stdout

# Data directory
DataDirectory /var/lib/tor
EOF

# Create VPN → Tor routing script
cat > "$TOR_DIR/vpn-to-tor.sh" << 'TOREOF'
#!/bin/bash
# Route VPN traffic through Tor
# This makes your VPN exit through Tor, providing double anonymity

set -e

VPN_INTERFACE="${VPN_INTERFACE:-tun0}"
TOR_PORT="${TOR_PORT:-9050}"

echo "🧅 Routing VPN traffic through Tor..."

# Check if Tor is running
if ! pgrep -x tor > /dev/null; then
    echo "Starting Tor..."
    sudo systemctl start tor || sudo tor -f tor-config/torrc-vpn &
    sleep 5
fi

# Check if VPN interface exists
if ! ip link show "$VPN_INTERFACE" > /dev/null 2>&1; then
    echo "❌ VPN interface $VPN_INTERFACE not found"
    echo "   Connect to VPN first, then run this script"
    exit 1
fi

# Get VPN network
VPN_NETWORK=$(ip route | grep "$VPN_INTERFACE" | grep -v default | head -1 | awk '{print $1}')

if [ -z "$VPN_NETWORK" ]; then
    echo "❌ Could not determine VPN network"
    exit 1
fi

echo "VPN Network: $VPN_NETWORK"
echo "Tor SOCKS: 127.0.0.1:$TOR_PORT"

# Install iptables rules to route VPN traffic through Tor
echo "Configuring iptables rules..."

# Create NAT rule to route VPN traffic through Tor
sudo iptables -t nat -A OUTPUT -o "$VPN_INTERFACE" -p tcp --syn -j REDIRECT --to-ports 9040

# Alternative: Use proxychains
if command -v proxychains4 &> /dev/null || command -v proxychains &> /dev/null; then
    echo "Using proxychains for Tor routing..."
    
    # Create proxychains config
    PROXYCHAINS_CONF="/tmp/proxychains-vpn.conf"
    cat > "$PROXYCHAINS_CONF" << PROXYEOF
strict_chain
quiet_mode
proxy_dns
remote_dns_subnet 224
tcp_read_time_out 15000
tcp_connect_time_out 8000

[ProxyList]
socks5 127.0.0.1 $TOR_PORT
PROXYEOF

    echo "✅ Proxychains configured"
    echo ""
    echo "To route applications through VPN→Tor:"
    echo "  proxychains4 -f $PROXYCHAINS_CONF <command>"
else
    echo "⚠️  proxychains not installed"
    echo "   Install: sudo apt-get install proxychains4"
fi

echo ""
echo "✅ VPN→Tor routing configured!"
echo ""
echo "Your traffic flow:"
echo "  Device → VPN ($VPN_INTERFACE) → Tor (127.0.0.1:$TOR_PORT) → Internet"
echo ""
echo "⚠️  Note: This routes ALL VPN traffic through Tor"
echo "   Some applications may need manual Tor configuration"
TOREOF

chmod +x "$TOR_DIR/vpn-to-tor.sh"

# Create transparent proxy setup (more advanced)
cat > "$TOR_DIR/setup-transparent-tor.sh" << 'TRANSPARENTEOF'
#!/bin/bash
# Setup Transparent Tor Proxy for VPN
# Makes all VPN traffic automatically route through Tor

set -e

VPN_INTERFACE="${VPN_INTERFACE:-tun0}"
TOR_PORT="${TOR_PORT:-9050}"

echo "🧅 Setting up Transparent Tor Proxy..."

# Check if Tor is running
if ! pgrep -x tor > /dev/null; then
    echo "❌ Tor is not running"
    echo "   Start Tor first: sudo systemctl start tor"
    exit 1
fi

# Get VPN network
VPN_NETWORK=$(ip route | grep "$VPN_INTERFACE" | grep -v default | head -1 | awk '{print $1}')

if [ -z "$VPN_NETWORK" ]; then
    echo "❌ VPN interface $VPN_INTERFACE not found or no network"
    exit 1
fi

echo "VPN Network: $VPN_NETWORK"

# Configure Tor for transparent proxying
# Tor needs to be configured with TransPort
TOR_CONFIG="/etc/tor/torrc"
if [ -f "$TOR_CONFIG" ]; then
    if ! grep -q "TransPort" "$TOR_CONFIG"; then
        echo "Configuring Tor for transparent proxying..."
        echo "TransPort 9040" | sudo tee -a "$TOR_CONFIG"
        echo "DNSPort 5353" | sudo tee -a "$TOR_CONFIG"
        sudo systemctl restart tor
        sleep 3
    fi
fi

# Route VPN traffic through Tor transparent proxy
echo "Configuring iptables..."

# Mark VPN traffic
sudo iptables -t mangle -A OUTPUT -o "$VPN_INTERFACE" -j MARK --set-mark 1

# Route marked traffic through Tor
sudo iptables -t nat -A OUTPUT -p tcp -m mark --mark 1 -d "$VPN_NETWORK" -j RETURN
sudo iptables -t nat -A OUTPUT -p tcp -m mark --mark 1 -j REDIRECT --to-ports 9040

# Route DNS through Tor
sudo iptables -t nat -A OUTPUT -p udp --dport 53 -j REDIRECT --to-ports 5353

echo "✅ Transparent Tor proxy configured!"
echo ""
echo "All VPN traffic now routes through Tor automatically"
TRANSPARENTEOF

chmod +x "$TOR_DIR/setup-transparent-tor.sh"

# Create instructions
cat > "$TOR_DIR/README.md" << EOF
# Tor Integration with VPN

## Overview

This routes your VPN traffic through Tor, creating:
**Device → VPN → Tor → Destination**

This provides multiple layers of anonymity:
- VPN encrypts and hides your real IP
- Tor adds another layer of routing and encryption
- Extremely difficult to correlate traffic

## Setup Methods

### Method 1: Simple Routing (Recommended)

1. Connect to VPN first
2. Start Tor:
   \`\`\`bash
   sudo systemctl start tor
   \`\`\`

3. Run routing script:
   \`\`\`bash
   ./vpn-to-tor.sh
   \`\`\`

### Method 2: Transparent Proxy (Advanced)

1. Configure Tor for transparent proxying:
   \`\`\`bash
   sudo ./setup-transparent-tor.sh
   \`\`\`

2. All VPN traffic automatically routes through Tor

### Method 3: Application-Level (Selective)

Use proxychains for specific applications:
\`\`\`bash
proxychains4 firefox
proxychains4 curl https://example.com
\`\`\`

## Benefits

- ✅ Double anonymity (VPN + Tor)
- ✅ Even if VPN compromised, Tor protects you
- ✅ Multiple routing layers
- ✅ Extremely difficult correlation

## Performance

- Tor adds latency (expect 2-5x slower)
- Some sites may block Tor exit nodes
- Use only when maximum anonymity needed

## Security Notes

- Tor + VPN is very secure but slower
- Use for maximum anonymity scenarios
- Regular VPN is sufficient for most use cases
EOF

echo "✅ Tor integration configuration created!"
echo ""
echo "📁 Files created in: $TOR_DIR"
echo "  - torrc-vpn (Tor configuration)"
echo "  - vpn-to-tor.sh (routing script)"
echo "  - setup-transparent-tor.sh (transparent proxy)"
echo "  - README.md (instructions)"
echo ""
echo "📖 See $TOR_DIR/README.md for setup instructions"
echo ""
echo "⚠️  Note: Tor adds significant latency"
echo "   Use only when maximum anonymity is required"

