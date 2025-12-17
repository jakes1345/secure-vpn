#!/bin/bash
# Deploy Ghost Mode to VPS (Server Side)
# This sets up all the server-side ghost mode features on your VPS

set -e

echo "🚀 Deploying Ghost Mode to VPS (Server Side)"
echo ""
echo "This will configure your VPN SERVER on the VPS with:"
echo "  ✅ Zero logging (no connection history)"
echo "  ✅ 4096-bit Perfect Forward Secrecy"
echo "  ✅ Traffic obfuscation server setup"
echo "  ✅ DNS over HTTPS server"
echo "  ✅ Enhanced privacy configuration"
echo ""

# VPS connection details
VPS_IP="${VPS_IP:-}"
VPS_USER="${VPS_USER:-root}"
VPS_SSH_KEY="${VPS_SSH_KEY:-}"

if [ -z "$VPS_IP" ]; then
    read -p "Enter VPS IP address: " VPS_IP
fi

if [ -z "$VPS_USER" ]; then
    read -p "Enter VPS username [root]: " VPS_USER
    VPS_USER=${VPS_USER:-root}
fi

echo ""
echo "📋 VPS Details:"
echo "   IP: $VPS_IP"
echo "   User: $VPS_USER"
echo ""

# Test SSH connection
echo "🔌 Testing SSH connection..."
if [ -n "$VPS_SSH_KEY" ]; then
    SSH_CMD="ssh -i $VPS_SSH_KEY $VPS_USER@$VPS_IP"
else
    SSH_CMD="ssh $VPS_USER@$VPS_IP"
fi

if ! $SSH_CMD "echo 'Connection successful'" 2>/dev/null; then
    echo "❌ Failed to connect to VPS"
    echo "   Make sure SSH is configured and you have access"
    exit 1
fi

echo "✅ Connected to VPS"
echo ""

# Base directory on VPS
VPS_VPN_DIR="/opt/phaze-vpn"
if [ "$VPS_USER" != "root" ]; then
    VPS_VPN_DIR="$HOME/phaze-vpn"
fi

echo "📦 Step 1: Uploading Ghost Mode configuration files..."

# Create directories on VPS
$SSH_CMD "mkdir -p $VPS_VPN_DIR/{config,certs,scripts,logs}"

# Upload server ghost mode config
if [ -f "config/server-ghost-mode.conf" ]; then
    scp config/server-ghost-mode.conf $VPS_USER@$VPS_IP:$VPS_VPN_DIR/config/
    echo "   ✅ Uploaded server-ghost-mode.conf"
fi

# Upload updated server.conf (with zero logging)
if [ -f "config/server.conf" ]; then
    scp config/server.conf $VPS_USER@$VPS_IP:$VPS_VPN_DIR/config/
    echo "   ✅ Uploaded server.conf (with zero logging)"
fi

# Upload scripts
scp scripts/generate-dh4096.sh $VPS_USER@$VPS_IP:$VPS_VPN_DIR/scripts/ 2>/dev/null || true
scp scripts/setup-traffic-obfuscation.sh $VPS_USER@$VPS_IP:$VPS_VPN_DIR/scripts/ 2>/dev/null || true
scp scripts/setup-dns-over-https.sh $VPS_USER@$VPS_IP:$VPS_VPN_DIR/scripts/ 2>/dev/null || true

echo ""
echo "🔐 Step 2: Generating 4096-bit DH Parameters on VPS..."
echo "   This takes 10-20 minutes but is essential"
read -p "   Generate now? (y/N): " GEN_DH

if [ "$GEN_DH" = "y" ] || [ "$GEN_DH" = "Y" ]; then
    echo "   Generating 4096-bit DH (this will take 10-20 minutes)..."
    $SSH_CMD "cd $VPS_VPN_DIR && chmod +x scripts/generate-dh4096.sh && ./scripts/generate-dh4096.sh" &
    DH_PID=$!
    echo "   ⏳ Running in background (PID: $DH_PID)"
    echo "   You can check progress with: ssh $VPS_USER@$VPS_IP 'ps aux | grep generate-dh4096'"
    echo "   Or wait for it to complete..."
else
    echo "   ⚠️  Skipping - run manually on VPS:"
    echo "      ssh $VPS_USER@$VPS_IP 'cd $VPS_VPN_DIR && ./scripts/generate-dh4096.sh'"
fi

echo ""
echo "🔧 Step 3: Setting up Traffic Obfuscation Server..."
read -p "   Setup traffic obfuscation server? (y/N): " SETUP_OBFS

if [ "$SETUP_OBFS" = "y" ] || [ "$SETUP_OBFS" = "Y" ]; then
    $SSH_CMD "cd $VPS_VPN_DIR && chmod +x scripts/setup-traffic-obfuscation.sh && ./scripts/setup-traffic-obfuscation.sh" || {
        echo "   ⚠️  Setup failed - may need to install dependencies on VPS"
    }
fi

echo ""
echo "🔧 Step 4: Setting up DNS over HTTPS Server..."
read -p "   Setup DoH server? (y/N): " SETUP_DOH

if [ "$SETUP_DOH" = "y" ] || [ "$SETUP_DOH" = "Y" ]; then
    $SSH_CMD "cd $VPS_VPN_DIR && chmod +x scripts/setup-dns-over-https.sh && ./scripts/setup-dns-over-https.sh" || {
        echo "   ⚠️  Setup failed - may need to install dependencies on VPS"
    }
fi

echo ""
echo "🔧 Step 5: Updating Server Configuration..."

# Backup existing config on VPS
$SSH_CMD "cd $VPS_VPN_DIR && [ -f config/server.conf ] && cp config/server.conf config/server.conf.backup.$(date +%Y%m%d) || true"

# Use ghost mode config
$SSH_CMD "cd $VPS_VPN_DIR && [ -f config/server-ghost-mode.conf ] && cp config/server-ghost-mode.conf config/server.conf || echo 'Using existing server.conf'"

echo "   ✅ Server configuration updated"

echo ""
echo "🔧 Step 6: Installing dependencies on VPS..."

# Install required packages
$SSH_CMD "apt-get update && apt-get install -y openvpn openssl iptables || yum install -y openvpn openssl iptables || true"

echo ""
echo "✅ Ghost Mode deployed to VPS!"
echo ""
echo "📋 Next Steps on VPS:"
echo ""
echo "1. Wait for 4096-bit DH to finish generating (if started):"
echo "   ssh $VPS_USER@$VPS_IP 'ls -lh $VPS_VPN_DIR/certs/dh4096.pem'"
echo ""
echo "2. Restart VPN server:"
echo "   ssh $VPS_USER@$VPS_IP 'systemctl restart openvpn@server'"
echo "   or"
echo "   ssh $VPS_USER@$VPS_IP 'cd $VPS_VPN_DIR && ./vpn-manager.py restart'"
echo ""
echo "3. Verify zero logging is active:"
echo "   ssh $VPS_USER@$VPS_IP 'grep -E \"verb|status|log\" $VPS_VPN_DIR/config/server.conf'"
echo ""
echo "4. Check VPN status:"
echo "   ssh $VPS_USER@$VPS_IP 'systemctl status openvpn@server'"
echo ""
echo "🔒 Your VPS is now configured with Ghost Mode!"

