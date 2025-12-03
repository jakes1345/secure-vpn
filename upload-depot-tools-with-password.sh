#!/bin/bash
# Upload depot_tools to VPS with password
# Run this on YOUR LOCAL COMPUTER

set -e

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="Jakes1328!@"
VPS_PATH="/opt"

echo "=========================================="
echo "📤 UPLOADING depot_tools TO VPS"
echo "=========================================="
echo ""

# Check if depot_tools exists locally
if [ -d "/tmp/tmp."*"/depot_tools" ] 2>/dev/null; then
    DEPOT_DIR=$(find /tmp -name "depot_tools" -type d 2>/dev/null | head -1)
    echo "✅ Found depot_tools in: $DEPOT_DIR"
elif [ -d "$HOME/depot_tools" ]; then
    DEPOT_DIR="$HOME/depot_tools"
    echo "✅ Found depot_tools in: $DEPOT_DIR"
else
    echo "📥 Downloading depot_tools..."
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    if git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git 2>&1; then
        DEPOT_DIR="$TEMP_DIR/depot_tools"
        echo "✅ Downloaded to: $DEPOT_DIR"
    else
        echo "❌ Download failed"
        exit 1
    fi
fi

echo ""
echo "📤 Uploading to VPS..."
echo ""

# Use sshpass if available, otherwise use expect
if command -v sshpass &> /dev/null; then
    echo "Using sshpass..."
    sshpass -p "$VPS_PASS" scp -r -o StrictHostKeyChecking=no "$DEPOT_DIR" "$VPS_USER@$VPS_IP:$VPS_PATH/" 2>&1
elif command -v expect &> /dev/null; then
    echo "Using expect..."
    expect << EOF
spawn scp -r -o StrictHostKeyChecking=no "$DEPOT_DIR" $VPS_USER@$VPS_IP:$VPS_PATH/
expect "password:"
send "$VPS_PASS\r"
expect eof
EOF
else
    echo "❌ Need sshpass or expect for password authentication"
    echo ""
    echo "Install one of:"
    echo "  sudo apt install sshpass"
    echo "  sudo apt install expect"
    echo ""
    echo "Or upload manually:"
    echo "  scp -r $DEPOT_DIR $VPS_USER@$VPS_IP:$VPS_PATH/"
    exit 1
fi

if [ $? -eq 0 ]; then
    echo "✅ Uploaded successfully!"
else
    echo "❌ Upload failed"
    exit 1
fi

echo ""
echo "🔧 Setting up on VPS..."
echo ""

# Setup on VPS
if command -v sshpass &> /dev/null; then
    sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" << 'ENDSSH'
chmod +x /opt/depot_tools/*
chmod +x /opt/depot_tools/.cipd_bin/* 2>/dev/null || true
export PATH="/opt/depot_tools:$PATH"
if which fetch > /dev/null 2>&1; then
    echo "✅ fetch command ready!"
    /opt/depot_tools/fetch --help | head -3
else
    echo "✅ depot_tools installed at /opt/depot_tools"
    echo "Use: /opt/depot_tools/fetch"
fi
ENDSSH
elif command -v expect &> /dev/null; then
    expect << 'EOF'
spawn ssh -o StrictHostKeyChecking=no root@15.204.11.19 "chmod +x /opt/depot_tools/* && chmod +x /opt/depot_tools/.cipd_bin/* 2>/dev/null || true && export PATH=\"/opt/depot_tools:\$PATH\" && /opt/depot_tools/fetch --help | head -3"
expect "password:"
send "Jakes1328!@\r"
expect eof
EOF
fi

echo ""
echo "=========================================="
echo "✅ depot_tools INSTALLED ON VPS!"
echo "=========================================="
echo ""
echo "📝 Next steps on VPS:"
echo ""
echo "1. SSH into VPS:"
echo "   ssh $VPS_USER@$VPS_IP"
echo ""
echo "2. Start Chromium fetch:"
echo "   screen -S chromium"
echo "   export PATH=\"/opt/depot_tools:\$PATH\""
echo "   cd /opt/phazebrowser"
echo "   fetch --nohooks chromium"
echo ""
echo "3. Detach: Ctrl+A then D"
echo ""

