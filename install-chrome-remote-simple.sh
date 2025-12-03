#!/bin/bash
# Simple Chrome Remote Desktop installer that ignores unrelated errors

echo "Installing Chrome Remote Desktop..."
echo ""

cd /tmp

# Install the downloaded package, ignoring opera-stable errors
dpkg -i chrome-remote-desktop.deb 2>&1 | grep -v "opera-stable" || true

# Fix any dependencies
apt-get install -f -y 2>&1 | grep -v "opera-stable" || true

# Verify installation
if [ -f /opt/google/chrome-remote-desktop/start-host ]; then
    echo ""
    echo "✅ Chrome Remote Desktop installed successfully!"
    echo ""
    echo "Now run the setup command:"
    echo "sudo ./run-chrome-remote-setup.sh"
else
    echo ""
    echo "⚠️  Installation may need manual intervention"
    echo "Try: sudo apt-get install -f -y"
    echo "Then: sudo dpkg -i /tmp/chrome-remote-desktop.deb"
fi

