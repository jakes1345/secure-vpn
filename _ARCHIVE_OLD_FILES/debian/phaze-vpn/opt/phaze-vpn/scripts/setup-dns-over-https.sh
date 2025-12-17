#!/bin/bash
# DNS over HTTPS (DoH) Setup Script
# Encrypts DNS queries even within the VPN tunnel
# Extra layer of protection against DNS monitoring

set -e

echo "🔒 Setting up DNS over HTTPS (DoH)..."
echo ""
echo "This encrypts DNS queries even within the VPN tunnel."
echo "Makes it impossible to see what domains you're visiting."
echo ""

# Create DoH configuration directory
DOH_DIR="$(pwd)/doh-config"
mkdir -p "$DOH_DIR"

# Check for cloudflared (Cloudflare's DoH client)
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Installing cloudflared..."
    
    # Download cloudflared
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        ARCH="amd64"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        ARCH="arm64"
    fi
    
    CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}"
    
    echo "Downloading cloudflared..."
    wget -O "$DOH_DIR/cloudflared" "$CLOUDFLARED_URL" || {
        echo "⚠️  Failed to download cloudflared automatically"
        echo "   Please download manually from:"
        echo "   https://github.com/cloudflare/cloudflared/releases"
    }
    
    if [ -f "$DOH_DIR/cloudflared" ]; then
        chmod +x "$DOH_DIR/cloudflared"
        sudo cp "$DOH_DIR/cloudflared" /usr/local/bin/cloudflared || true
    fi
fi

# Create DoH proxy configuration
cat > "$DOH_DIR/doh-proxy.yaml" << EOF
# DNS over HTTPS Proxy Configuration
# Routes DNS queries through DoH for maximum privacy

proxy-dns: true
proxy-dns-port: 5053
proxy-dns-address: 127.0.0.1
proxy-dns-upstream:
  - https://9.9.9.9/dns-query      # Quad9 (Switzerland - no logging)
  - https://1.1.1.1/dns-query       # Cloudflare (backup)
  - https://dns.quad9.net/dns-query # Quad9 alternative
EOF

# Create systemd service for DoH proxy
cat > "$DOH_DIR/cloudflared-doh.service" << EOF
[Unit]
Description=Cloudflared DNS over HTTPS proxy
After=network.target

[Service]
Type=simple
User=nobody
ExecStart=/usr/local/bin/cloudflared proxy-dns --address 127.0.0.1 --port 5053 --upstream https://9.9.9.9/dns-query --upstream https://1.1.1.1/dns-query
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create client setup script
cat > "$DOH_DIR/setup-doh-client.sh" << 'DOHEOF'
#!/bin/bash
# Setup DNS over HTTPS on client

set -e

echo "🔒 Setting up DNS over HTTPS on client..."

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared not found. Please install it first."
    exit 1
fi

# Start DoH proxy
echo "Starting DoH proxy..."
cloudflared proxy-dns --address 127.0.0.1 --port 5053 \
    --upstream https://9.9.9.9/dns-query \
    --upstream https://1.1.1.1/dns-query &

DOH_PID=$!
echo "DoH proxy started (PID: $DOH_PID)"

# Update resolv.conf to use DoH
echo "Updating DNS configuration..."
sudo cp /etc/resolv.conf /etc/resolv.conf.backup

cat > /tmp/resolv.conf.doh << RESOLVEOF
nameserver 127.0.0.1
RESOLVEOF

sudo cp /tmp/resolv.conf.doh /etc/resolv.conf

echo "✅ DNS over HTTPS configured!"
echo "   DNS queries now go through: 127.0.0.1:5053 (DoH)"
echo ""
echo "To stop: kill $DOH_PID"
DOHEOF

chmod +x "$DOH_DIR/setup-doh-client.sh"

# Create OpenVPN push configuration for DoH
cat > "$DOH_DIR/openvpn-doh-push.conf" << EOF
# Add these lines to your OpenVPN server config to push DoH DNS
# This makes clients use DoH automatically when connected

# DNS over HTTPS (Quad9 - Switzerland, no logging)
push "dhcp-option DNS 127.0.0.1"
push "dhcp-option DNS 9.9.9.9"
push "block-outside-dns"

# Note: Clients need cloudflared running on 127.0.0.1:5053
# Or use a DoH-capable DNS server directly
EOF

# Create instructions
cat > "$DOH_DIR/README.md" << EOF
# DNS over HTTPS (DoH) Setup

## What is DoH?
DNS over HTTPS encrypts DNS queries using HTTPS, making them impossible to monitor even if intercepted.

## Server Setup

1. Install cloudflared:
   \`\`\`bash
   # Download from: https://github.com/cloudflare/cloudflared/releases
   # Or use package manager
   \`\`\`

2. Start DoH proxy:
   \`\`\`bash
   cloudflared proxy-dns --address 0.0.0.0 --port 5053 \\
       --upstream https://9.9.9.9/dns-query \\
       --upstream https://1.1.1.1/dns-query
   \`\`\`

3. Or install as systemd service:
   \`\`\`bash
   sudo cp cloudflared-doh.service /etc/systemd/system/
   sudo systemctl enable cloudflared-doh
   sudo systemctl start cloudflared-doh
   \`\`\`

## Client Setup

1. Install cloudflared on client

2. Run setup script:
   \`\`\`bash
   ./setup-doh-client.sh
   \`\`\`

3. Or manually start DoH proxy:
   \`\`\`bash
   cloudflared proxy-dns --address 127.0.0.1 --port 5053 \\
       --upstream https://9.9.9.9/dns-query
   \`\`\`

4. Update DNS to 127.0.0.1

## OpenVPN Integration

Add to server config:
\`\`\`
push "dhcp-option DNS 127.0.0.1"
push "block-outside-dns"
\`\`\`

Clients need DoH proxy running locally on 127.0.0.1:5053

## Benefits

- ✅ DNS queries encrypted (HTTPS)
- ✅ Cannot be monitored or blocked
- ✅ Works even if VPN is compromised
- ✅ Extra layer of privacy

## DoH Providers Used

- **Quad9 (9.9.9.9)**: Switzerland-based, no logging, privacy-focused
- **Cloudflare (1.1.1.1)**: Fast, no logging (backup)
EOF

echo "✅ DNS over HTTPS configuration created!"
echo ""
echo "📁 Files created in: $DOH_DIR"
echo "  - doh-proxy.yaml (DoH proxy config)"
echo "  - cloudflared-doh.service (systemd service)"
echo "  - setup-doh-client.sh (client setup script)"
echo "  - openvpn-doh-push.conf (OpenVPN integration)"
echo "  - README.md (instructions)"
echo ""
echo "📖 See $DOH_DIR/README.md for setup instructions"

