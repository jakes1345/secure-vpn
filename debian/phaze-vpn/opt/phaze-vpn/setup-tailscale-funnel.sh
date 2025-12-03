#!/bin/bash
# Setup Tailscale Funnel for public access
# This makes your OpenVPN server accessible WITHOUT clients needing Tailscale

echo "=========================================="
echo "Setting Up Tailscale Funnel for PhazeVPN"
echo "=========================================="
echo ""

# Check if Tailscale is installed and running
if ! command -v tailscale &> /dev/null; then
    echo "❌ Tailscale is not installed"
    echo "Install it first: curl -fsSL https://tailscale.com/install.sh | sh"
    exit 1
fi

if ! tailscale status &> /dev/null; then
    echo "❌ Tailscale is not running"
    echo "Start it first: sudo tailscale up"
    exit 1
fi

TAILSCALE_IP=$(tailscale ip -4 2>/dev/null | head -1)

if [ -z "$TAILSCALE_IP" ]; then
    echo "❌ Could not get Tailscale IP"
    exit 1
fi

echo "✅ Tailscale is running"
echo "✅ Your Tailscale IP: $TAILSCALE_IP"
echo ""

# Check if funnel is already running
if tailscale funnel status 2>/dev/null | grep -q "100.76.207.81:1194"; then
    echo "✅ Funnel is already running!"
    echo ""
    tailscale funnel status
    exit 0
fi

echo "Setting up Tailscale Funnel..."
echo ""
echo "This will expose your OpenVPN server (port 1194) publicly"
echo "Clients won't need Tailscale to connect!"
echo ""

# Start funnel for port 1194
echo "Starting funnel on port 1194..."
sudo tailscale funnel 1194

echo ""
echo "=========================================="
echo "✅ Funnel Started!"
echo "=========================================="
echo ""
echo "Your OpenVPN server is now publicly accessible!"
echo ""
echo "Get your public URL:"
tailscale funnel status
echo ""
echo "Share this URL with clients - they can connect without Tailscale!"
echo ""

