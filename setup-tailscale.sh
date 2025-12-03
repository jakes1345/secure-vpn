#!/bin/bash
# Setup Tailscale for PhazeVPN
# This makes your OpenVPN server accessible without router port forwarding

echo "=========================================="
echo "Setting Up Tailscale for PhazeVPN"
echo "=========================================="
echo ""

# Check if Tailscale is installed
if ! command -v tailscale &> /dev/null; then
    echo "Tailscale is not installed."
    echo ""
    echo "📥 Installing Tailscale..."
    echo ""
    
    # Check if we can use the official install script
    if command -v curl &> /dev/null; then
        echo "Downloading Tailscale install script..."
        curl -fsSL https://tailscale.com/install.sh | sh
    else
        echo "Please install Tailscale manually:"
        echo "  1. Go to: https://tailscale.com/download/linux"
        echo "  2. Follow installation instructions"
        echo "  3. Or run: curl -fsSL https://tailscale.com/install.sh | sh"
        exit 1
    fi
fi

echo "✅ Tailscale is installed"
echo ""

# Check if Tailscale is running
if ! tailscale status &> /dev/null; then
    echo "⚠️  Tailscale is not running"
    echo ""
    echo "Starting Tailscale..."
    echo ""
    echo "You'll need to authenticate:"
    echo "  1. Run: sudo tailscale up"
    echo "  2. Follow the link to sign in"
    echo "  3. Authorize this device"
    echo ""
    echo "Or run this script with sudo to start it automatically"
    exit 1
fi

# Get Tailscale IP
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null | head -1)

if [ -z "$TAILSCALE_IP" ]; then
    echo "❌ Could not get Tailscale IP"
    echo "Make sure Tailscale is running: sudo tailscale up"
    exit 1
fi

echo "✅ Tailscale is running"
echo "✅ Your Tailscale IP: $TAILSCALE_IP"
echo ""

# Update client configs to use Tailscale IP
echo "Updating client configs to use Tailscale IP..."
CONFIG_DIR="client-configs"
UPDATED=0

if [ -d "$CONFIG_DIR" ]; then
    for config in "$CONFIG_DIR"/*.ovpn; do
        if [ -f "$config" ]; then
            # Backup original
            cp "$config" "${config}.backup"
            
            # Update remote IP to Tailscale IP
            sed -i "s/^remote .* 1194/remote $TAILSCALE_IP 1194/" "$config"
            
            echo "  ✓ Updated: $(basename $config)"
            UPDATED=$((UPDATED + 1))
        fi
    done
fi

echo ""
echo "=========================================="
echo "✅ Tailscale Setup Complete!"
echo "=========================================="
echo ""
echo "Your OpenVPN server is now accessible via Tailscale!"
echo ""
echo "Server Details:"
echo "  Tailscale IP: $TAILSCALE_IP"
echo "  VPN Port: 1194"
echo "  Connection: $TAILSCALE_IP:1194"
echo ""
echo "Client Configs:"
if [ $UPDATED -gt 0 ]; then
    echo "  ✅ Updated $UPDATED config(s) to use Tailscale IP"
    echo "  📝 Backups saved as .backup files"
else
    echo "  ⚠️  No configs found to update"
    echo "  New clients will use Tailscale IP automatically"
fi
echo ""
echo "To share with clients:"
echo "  1. They download config from: https://your-tunnel-url.com/download?name=CLIENT"
echo "  2. Config will connect to: $TAILSCALE_IP:1194"
echo "  3. They connect and get internet access!"
echo ""
echo "Note: Clients don't need Tailscale - they just connect to your Tailscale IP"
echo ""

