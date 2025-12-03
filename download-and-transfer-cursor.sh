#!/bin/bash
# Download Cursor on local machine and transfer to VPS

VPS_IP="15.204.11.19"
VPS_USER="root"

echo "Downloading Cursor on your local machine..."
cd /tmp

# Try to download Cursor .deb
curl -L "https://www.cursor.sh/api/download/linux" -o cursor.deb 2>&1

# Or if that doesn't work, download from alternative source
if [ ! -f cursor.deb ] || [ $(stat -f%z cursor.deb 2>/dev/null || stat -c%s cursor.deb 2>/dev/null) -lt 1000000 ]; then
    echo "Trying alternative download method..."
    # Download from GitHub releases or alternative source
    curl -L "https://github.com/getcursor/cursor/releases/download/latest/cursor_amd64.deb" -o cursor.deb 2>&1 || \
    wget "https://github.com/getcursor/cursor/releases/latest/download/cursor_amd64.deb" -O cursor.deb 2>&1
fi

if [ -f cursor.deb ] && [ $(stat -f%z cursor.deb 2>/dev/null || stat -c%s cursor.deb 2>/dev/null) -gt 1000000 ]; then
    echo "✅ Downloaded! Transferring to VPS..."
    scp cursor.deb ${VPS_USER}@${VPS_IP}:/tmp/
    
    echo "Installing on VPS..."
    ssh ${VPS_USER}@${VPS_IP} "dpkg -i /tmp/cursor.deb 2>&1 || apt-get install -f -y"
    
    echo "✅ Cursor installed on VPS!"
    echo "SSH in and run: cursor"
else
    echo "❌ Could not download Cursor"
    echo "Please download it manually from: https://cursor.sh"
    echo "Then run: scp cursor.deb root@15.204.11.19:/tmp/"
    echo "Then SSH in and: dpkg -i /tmp/cursor.deb"
fi
