# PhazeOS First Boot Wizard

**NO TERMINAL NEEDED!** Beautiful GUI wizard that runs automatically after installation.

## What It Does

When users first boot into PhazeOS (after installation), they see a beautiful GUI wizard that:

1. **Welcome Screen** - Introduces PhazeOS
2. **Privacy Setup** - Configure VPN, MAC randomization, kill switch
3. **Software Selection** - Install gaming, dev, hacking tools with checkboxes
4. **Appearance** - Choose theme (dark/light)
5. **Setup Progress** - Shows progress bars (no terminal output)
6. **Complete** - "Your system is ready!"

**All visual. Zero terminal commands.**

## Installation

### On the ISO (for build):
```bash
cd phazeos-first-boot-wizard
sudo ./install-wizard.sh
```

This will:
- Install wizard to `/opt/phazeos/first-boot-wizard`
- Create autostart entry
- Make it run on first login

### To add to PhazeOS ISO build:

Add to `phazeos-build/entrypoint.sh`:
```bash
# Copy First Boot Wizard
mkdir -p /work/profile/airootfs/opt/phazeos/first-boot-wizard
cp -r /build/phazeos-first-boot-wizard/* /work/profile/airootfs/opt/phazeos/first-boot-wizard/
chmod +x /work/profile/airootfs/opt/phazeos/first-boot-wizard/*.py
chmod +x /work/profile/airootfs/opt/phazeos/first-boot-wizard/*.sh

# Install autostart
mkdir -p /work/profile/airootfs/etc/skel/.config/autostart
cat > /work/profile/airootfs/etc/skel/.config/autostart/phazeos-wizard.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=PhazeOS Setup Wizard
Exec=/opt/phazeos/first-boot-wizard/autostart.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
```

## Dependencies

```bash
sudo pacman -S python-pyqt6
```

## How It Works

1. User installs PhazeOS (normal Arch install)
2. User reboots into PhazeOS
3. Desktop loads
4. Wizard automatically starts
5. User clicks through GUI screens
6. System configures itself (no terminal visible)
7. Done!

## Manual Run

```bash
phazeos-wizard
```

Or:
```bash
python3 /opt/phazeos/first-boot-wizard/first_boot_wizard.py
```

## The Result

**Users never see a terminal.** They just:
- Click buttons
- Select checkboxes
- See progress bars
- Done!

That's the PhazeOS way. 🚀
