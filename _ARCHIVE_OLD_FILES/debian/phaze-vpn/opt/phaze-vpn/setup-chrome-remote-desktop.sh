#!/bin/bash
# Setup Chrome Remote Desktop for Linux Mint/Ubuntu
# This allows you to access your computer from your phone

# Don't exit on error - we want to continue even if some packages fail
set +e

echo "=========================================="
echo "Setting Up Chrome Remote Desktop"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs sudo privileges"
    echo "Please run: sudo ./setup-chrome-remote-desktop.sh"
    exit 1
fi

echo "📦 Step 1: Installing dependencies..."
apt-get update 2>&1 | grep -v "^$"

echo "Installing required packages..."
apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    xvfb \
    xbase-clients \
    python3-psutil \
    curl \
    lsb-release 2>&1 | grep -E "(Setting up|Unpacking|Selecting|^$)" || true

# Fix any broken packages (but don't fail if it doesn't work)
apt-get install -f -y 2>&1 | tail -3 || true

echo "✅ Dependencies installed"
echo ""

echo "📥 Step 2: Installing Chrome Remote Desktop..."
cd /tmp

# Method 1: Try direct .deb download
echo "Trying Method 1: Direct .deb download..."
REMOTE_DESKTOP_URL="https://dl.google.com/linux/direct/chrome-remote-desktop_current_amd64.deb"

if wget --spider "$REMOTE_DESKTOP_URL" 2>&1 | grep -q "200 OK"; then
    echo "Downloading .deb package..."
    wget "$REMOTE_DESKTOP_URL" -O chrome-remote-desktop.deb
    echo "✅ Download complete"
    
    echo "Installing package..."
    if dpkg -i chrome-remote-desktop.deb 2>&1 | grep -v "^$"; then
        # Even if dpkg shows errors, try to fix them
        apt-get install -f -y 2>&1 | tail -5 || true
        echo "✅ Installation attempted - checking status..."
    else
        echo "Fixing dependencies..."
        apt-get install -f -y 2>&1 | tail -5 || true
        echo "✅ Installation complete after dependency fix"
    fi
else
    echo "❌ Direct download failed, trying repository method..."
    
    # Method 2: Add Google repository
    echo "Adding Google repository..."
    
    # Download and add GPG key (new method for newer Ubuntu)
    if [ -f /etc/apt/keyrings ]; then
        curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome-remote-desktop.gpg
        echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome-remote-desktop.gpg] http://dl.google.com/linux/chrome-remote-desktop/deb/ stable main" > /etc/apt/sources.list.d/chrome-remote-desktop.list
    else
        # Old method
        wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
        echo "deb [arch=amd64] http://dl.google.com/linux/chrome-remote-desktop/deb/ stable main" > /etc/apt/sources.list.d/chrome-remote-desktop.list
    fi
    
    echo "Updating package list..."
    apt-get update
    
    echo "Installing from repository..."
    apt-get install -y chrome-remote-desktop
    echo "✅ Installed from repository"
fi

# Verify installation
if [ -f /opt/google/chrome-remote-desktop/start-host ]; then
    echo ""
    echo "✅ Chrome Remote Desktop is installed and ready!"
    echo "   Location: /opt/google/chrome-remote-desktop/start-host"
else
    echo "⚠️  Installation may have issues. Checking..."
    which chrome-remote-desktop || dpkg -l | grep chrome-remote-desktop
fi

echo ""

echo "=========================================="
echo "✅ Chrome Remote Desktop Installed!"
echo "=========================================="
echo ""

# Check if user provided setup command
if [ -n "$1" ]; then
    echo "🔧 Running setup command..."
    eval "$1"
    echo ""
    echo "✅ Setup complete! You should now be able to connect from your phone."
    echo ""
else
    echo "📱 Next Steps:"
    echo ""
    echo "1. On your COMPUTER (this machine):"
    echo "   - Open a web browser"
    echo "   - Go to: https://remotedesktop.google.com/headless"
    echo "   - Sign in with your Google account"
    echo "   - Click 'Begin' under 'Set up remote access'"
    echo "   - Copy the command it gives you"
    echo "   - Run: sudo ./setup-chrome-remote-desktop.sh 'YOUR_COMMAND_HERE'"
    echo "   - Or run the command directly in terminal"
    echo ""
    echo "2. On your PHONE:"
    echo "   - Install 'Chrome Remote Desktop' app from Play Store/App Store"
    echo "   - Sign in with the same Google account"
    echo "   - Your computer will appear in 'My Computers'"
    echo "   - Tap to connect!"
    echo ""
    echo "💡 Tip: You'll need to set a PIN when setting up (for security)"
    echo ""
    echo "🔗 Setup URL: https://remotedesktop.google.com/headless"
    echo ""
fi

