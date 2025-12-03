#!/bin/bash
# Traffic Obfuscation Setup Script
# Makes VPN traffic look like regular HTTPS to avoid DPI detection
# This prevents governments from identifying you're using a VPN

set -e

echo "🔒 Setting up Traffic Obfuscation..."
echo ""
echo "This makes your VPN traffic look like regular HTTPS."
echo "Deep Packet Inspection (DPI) won't be able to identify VPN usage."
echo ""

# Check if obfsproxy is available
if ! command -v obfsproxy &> /dev/null; then
    echo "📦 Installing obfsproxy..."
    
    # Detect OS
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y obfsproxy python3-pip
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS
        sudo yum install -y obfsproxy
    elif [ -f /etc/arch-release ]; then
        # Arch Linux
        sudo pacman -S obfsproxy
    else
        echo "⚠️  Please install obfsproxy manually:"
        echo "   pip3 install obfsproxy"
        echo "   or install from your package manager"
    fi
fi

# Alternative: Use Shadowsocks (easier to set up)
echo ""
echo "🔧 Setting up Shadowsocks (alternative obfuscation)..."
echo ""

# Create Shadowsocks server config
SHADOWSOCKS_DIR="$(pwd)/shadowsocks"
mkdir -p "$SHADOWSOCKS_DIR"

# Generate random password
SHADOWSOCKS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

cat > "$SHADOWSOCKS_DIR/server-config.json" << EOF
{
    "server": "0.0.0.0",
    "server_port": 8388,
    "password": "$SHADOWSOCKS_PASSWORD",
    "method": "chacha20-ietf-poly1305",
    "plugin": "obfs-server",
    "plugin_opts": "obfs=http",
    "timeout": 300
}
EOF

cat > "$SHADOWSOCKS_DIR/client-config.json" << EOF
{
    "server": "YOUR_SERVER_IP",
    "server_port": 8388,
    "password": "$SHADOWSOCKS_PASSWORD",
    "method": "chacha20-ietf-poly1305",
    "plugin": "obfs-local",
    "plugin_opts": "obfs=http",
    "timeout": 300
}
EOF

# Create setup instructions
cat > "$SHADOWSOCKS_DIR/README.md" << EOF
# Traffic Obfuscation Setup

## Method 1: Shadowsocks (Recommended - Easier)

### Server Setup:
1. Install shadowsocks-libev:
   \`\`\`bash
   sudo apt-get install shadowsocks-libev
   \`\`\`

2. Install obfs plugin:
   \`\`\`bash
   sudo apt-get install simple-obfs
   \`\`\`

3. Start server:
   \`\`\`bash
   sudo ss-server -c server-config.json
   \`\`\`

### Client Setup:
1. Install shadowsocks client
2. Use client-config.json (update server IP)
3. Connect - traffic will look like HTTPS

## Method 2: OpenVPN with Obfsproxy

### Server Setup:
1. Install obfsproxy:
   \`\`\`bash
   pip3 install obfsproxy
   \`\`\`

2. Start obfsproxy on server:
   \`\`\`bash
   obfsproxy --log-level=INFO obfs3 --dest=127.0.0.1:1194 server 0.0.0.0:1195
   \`\`\`

3. Configure OpenVPN to listen on 127.0.0.1:1194

### Client Setup:
1. Start obfsproxy:
   \`\`\`bash
   obfsproxy obfs3 --dest=SERVER_IP:1195 client 127.0.0.1:1194
   \`\`\`

2. Connect OpenVPN to 127.0.0.1:1194

## Benefits:
- VPN traffic looks like regular HTTPS
- DPI cannot identify VPN usage
- Harder to block or throttle
- Makes correlation much more difficult

## Password:
Your Shadowsocks password: $SHADOWSOCKS_PASSWORD
(Keep this secret!)
EOF

echo "✅ Traffic obfuscation configuration created!"
echo ""
echo "📁 Files created in: $SHADOWSOCKS_DIR"
echo "  - server-config.json (Shadowsocks server config)"
echo "  - client-config.json (Shadowsocks client config)"
echo "  - README.md (setup instructions)"
echo ""
echo "🔑 Shadowsocks Password: $SHADOWSOCKS_PASSWORD"
echo "   (Save this - you'll need it for clients)"
echo ""
echo "📖 See $SHADOWSOCKS_DIR/README.md for setup instructions"

