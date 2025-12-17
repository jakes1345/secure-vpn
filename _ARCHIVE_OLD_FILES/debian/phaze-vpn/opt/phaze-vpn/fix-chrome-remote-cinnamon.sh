#!/bin/bash
# Fix Chrome Remote Desktop for Cinnamon desktop environment

echo "=========================================="
echo "Fixing Chrome Remote Desktop for Cinnamon"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs sudo privileges"
    echo "Please run: sudo ./fix-chrome-remote-cinnamon.sh"
    exit 1
fi

USERNAME=$(logname || echo $SUDO_USER || whoami)
echo "Configuring for user: $USERNAME"
echo ""

# Create Chrome Remote Desktop config directory
CONFIG_DIR="/home/$USERNAME/.config/chrome-remote-desktop"
mkdir -p "$CONFIG_DIR"
chown -R "$USERNAME:$USERNAME" "$CONFIG_DIR"

# Create X session configuration for Cinnamon
echo "Creating X session configuration..."
cat > "$CONFIG_DIR/xsession" << 'EOF'
#!/bin/bash
# Chrome Remote Desktop X session for Cinnamon

# Set display
export DISPLAY=:20

# Start Cinnamon session
exec /usr/bin/cinnamon-session
EOF

chmod +x "$CONFIG_DIR/xsession"
chown "$USERNAME:$USERNAME" "$CONFIG_DIR/xsession"

# Create systemd user service override (if needed)
SYSTEMD_USER_DIR="/home/$USERNAME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR/chrome-remote-desktop@$USERNAME.service.d"
chown -R "$USERNAME:$USERNAME" "$SYSTEMD_USER_DIR"

# Alternative: Set environment variable
echo "Setting environment variables..."
if ! grep -q "CHROME_REMOTE_DESKTOP_SESSION" /home/$USERNAME/.bashrc; then
    echo "" >> /home/$USERNAME/.bashrc
    echo "# Chrome Remote Desktop for Cinnamon" >> /home/$USERNAME/.bashrc
    echo "export CHROME_REMOTE_DESKTOP_SESSION=cinnamon" >> /home/$USERNAME/.bashrc
fi

# Install required packages if missing
echo "Checking for required packages..."
apt-get install -y xserver-xorg-video-dummy x11vnc > /dev/null 2>&1 || true

echo ""
echo "✅ Configuration updated!"
echo ""
echo "📝 Next steps:"
echo "1. Log out and log back in (or restart)"
echo "2. Run the setup command again:"
echo "   sudo ./run-chrome-remote-setup.sh"
echo ""
echo "💡 If it still doesn't work, try:"
echo "   - Switch to a different desktop session (XFCE, MATE) temporarily"
echo "   - Or use RustDesk instead (open source alternative)"
echo ""

