#!/bin/bash
# Install PhazeOS First Boot Wizard to system
# This makes it run automatically on first boot

set -e

echo "Installing PhazeOS First Boot Wizard..."

# Install directory
INSTALL_DIR="/opt/phazeos/first-boot-wizard"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create install directory
sudo mkdir -p "$INSTALL_DIR"
sudo mkdir -p /usr/local/bin

# Copy wizard files
sudo cp "$SCRIPT_DIR/first_boot_wizard.py" "$INSTALL_DIR/"
sudo cp "$SCRIPT_DIR/autostart.sh" "$INSTALL_DIR/"

# Make executable
sudo chmod +x "$INSTALL_DIR/first_boot_wizard.py"
sudo chmod +x "$INSTALL_DIR/autostart.sh"

# Create symlink
sudo ln -sf "$INSTALL_DIR/first_boot_wizard.py" /usr/local/bin/phazeos-wizard

# Install autostart for KDE Plasma
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/phazeos-wizard.desktop" << EOF
[Desktop Entry]
Type=Application
Name=PhazeOS Setup Wizard
Exec=$INSTALL_DIR/autostart.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

# Also add to systemd user service (alternative)
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/phazeos-wizard.service" << EOF
[Unit]
Description=PhazeOS First Boot Wizard
After=graphical.target

[Service]
Type=oneshot
ExecStart=$INSTALL_DIR/autostart.sh
RemainAfterExit=yes

[Install]
WantedBy=default.target
EOF

systemctl --user enable phazeos-wizard.service 2>/dev/null || true

echo "✅ PhazeOS First Boot Wizard installed!"
echo ""
echo "The wizard will run automatically on first login."
echo "To run manually: phazeos-wizard"
