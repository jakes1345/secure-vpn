#!/bin/bash
# Complete PhazeVPN Website Deployment Script

set -e

echo "=========================================="
echo "🚀 PhazeVPN Complete Deployment"
echo "=========================================="
echo ""

VPS="15.204.11.19"
PASS="<VPS_PASSWORD_REMOVED>"

# Step 1: Build Go backend
echo "📦 Building Go backend..."
cd /media/jack/Liunux/secure-vpn/phazevpn-web-go
go build -o phazevpn-web .
echo "✅ Build complete"
echo ""

# Step 2: Package everything
echo "📦 Packaging..."
tar czf phazevpn-web-complete.tar.gz phazevpn-web templates/ static/
echo "✅ Package created"
echo ""

# Step 3: Upload to VPS
echo "📤 Uploading to VPS..."
sshpass -p "$PASS" scp phazevpn-web-complete.tar.gz root@$VPS:/opt/
echo "✅ Upload complete"
echo ""

# Step 4: Deploy on VPS
echo "🚀 Deploying on VPS..."
sshpass -p "$PASS" ssh root@$VPS 'bash -s' << 'EOFDEPLOY'
# Stop old server
pkill phazevpn-web || true

# Extract new version
cd /opt/phazevpn
tar xzf ../phazevpn-web-complete.tar.gz

# Start server
nohup ./phazevpn-web > /var/log/phazevpn-web.log 2>&1 &

sleep 3

# Check if running
if ps aux | grep -v grep | grep phazevpn-web > /dev/null; then
    echo "✅ Server started successfully"
else
    echo "❌ Server failed to start"
    tail -20 /var/log/phazevpn-web.log
    exit 1
fi
EOFDEPLOY

echo "✅ Deployment complete"
echo ""

# Step 5: Test endpoints
echo "🧪 Testing endpoints..."
sleep 2

test_endpoint() {
    local url=$1
    local name=$2
    local code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [ "$code" = "200" ] || [ "$code" = "303" ]; then
        echo "  ✅ $name: $code"
    else
        echo "  ❌ $name: $code"
    fi
}

test_endpoint "https://phazevpn.com" "Home"
test_endpoint "https://phazevpn.com/pricing" "Pricing"
test_endpoint "https://phazevpn.com/download" "Download"
test_endpoint "https://phazevpn.com/login" "Login"
test_endpoint "https://phazevpn.com/signup" "Signup"
test_endpoint "https://phazevpn.com/dashboard" "Dashboard"
test_endpoint "https://phazevpn.com/static/css/style.css" "CSS"

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "🌐 Website: https://phazevpn.com"
echo "📊 Features:"
echo "  - Password hashing (bcrypt)"
echo "  - VPN key generation (WireGuard, OpenVPN, PhazeVPN)"
echo "  - Config downloads"
echo "  - Modern animated UI"
echo "  - All pages functional"
echo ""
echo "📋 Next steps:"
echo "  1. Test signup/login flow"
echo "  2. Generate VPN keys"
echo "  3. Download and test configs"
echo "  4. Build client binaries"
echo ""
