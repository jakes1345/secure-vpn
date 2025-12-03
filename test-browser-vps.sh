#!/bin/bash

# Test PhazeBrowser installation on VPS

VPS_IP="15.204.11.19"
VPS_USER="root"
REMOTE_DIR="/opt/phazebrowser"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     🚀 Testing PhazeBrowser on VPS                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo "VPS: $VPS_USER@$VPS_IP"
echo "Remote directory: $REMOTE_DIR"
echo ""

# Check if we can connect
echo "Testing SSH connection..."
# Use password authentication (prompt for password)
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP "echo 'Connected successfully'" 2>&1 | grep -q "Connected successfully\|Permission denied"; then
    echo "✅ SSH connection works (will prompt for password)"
else
    echo "⚠️  SSH connection test - will prompt for password when connecting"
fi

echo ""
echo "Installing dependencies on VPS..."
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
    echo "Updating package list..."
    apt-get update -qq
    
    echo "Installing PyQt6..."
    apt-get install -y python3-pip python3-qt6 python3-pyqt6 python3-pyqt6.qtwebengine
    
    echo "Verifying installation..."
    python3 -c "import PyQt6; print('✅ PyQt6 installed')" 2>/dev/null || echo "❌ PyQt6 not installed"
ENDSSH

echo ""
echo "Creating remote directory structure..."
ssh $VPS_USER@$VPS_IP "mkdir -p $REMOTE_DIR/{src,ui,vpn}"

echo ""
echo "Uploading browser files..."
scp phazebrowser/src/phazebrowser.py $VPS_USER@$VPS_IP:$REMOTE_DIR/src/
scp phazebrowser/ui/*.py $VPS_USER@$VPS_IP:$REMOTE_DIR/ui/
scp phazebrowser/vpn/*.py $VPS_USER@$VPS_IP:$REMOTE_DIR/vpn/

echo ""
echo "Testing imports on VPS..."
ssh $VPS_USER@$VPS_IP << ENDSSH
    cd $REMOTE_DIR/src
    python3 << 'PYTHON'
import sys
sys.path.insert(0, '/opt/phazebrowser')

try:
    from vpn.vpn_manager import VPNManager
    print('✅ VPN manager imports OK')
except Exception as e:
    print(f'❌ VPN manager: {e}')

try:
    from ui.sidebar import Sidebar
    print('✅ Sidebar imports OK')
except Exception as e:
    print(f'❌ Sidebar: {e}')

try:
    import PyQt6
    print('✅ PyQt6 available')
except ImportError:
    print('❌ PyQt6 not available')
PYTHON
ENDSSH

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run browser (requires X11 forwarding or VNC):"
echo "  ssh -X $VPS_USER@$VPS_IP"
echo "  cd $REMOTE_DIR/src"
echo "  python3 phazebrowser.py"

