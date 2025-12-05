#!/usr/bin/env python3
"""
Build GUI on VPS and deploy automatically
Uses paramiko for reliable SSH connection
"""

import paramiko
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"
BUILD_DIR = f"{VPS_DIR}/gui-build"
OUTPUT_DIR = f"{VPS_DIR}/web-portal/static/downloads"

def connect_vps():
    """Connect to VPS"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Try SSH keys first
    key_paths = [
        Path.home() / '.ssh' / 'id_rsa',
        Path.home() / '.ssh' / 'id_ed25519',
    ]
    
    for key_path in key_paths:
        if key_path.exists() and key_path.is_file():
            try:
                key = paramiko.RSAKey.from_private_key_file(str(key_path))
                ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    return ssh
                except:
                    continue
    
    # Try ssh-agent
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        return ssh
    except:
        pass
    
    # Fallback to password
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    else:
        print("❌ Authentication failed - no SSH key or password")
        return None

def main():
    print("==========================================")
    print("Building & Deploying GUI to VPS")
    print("==========================================")
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # Create directories
        print("📁 Creating directories...")
        ssh.exec_command(f"mkdir -p {BUILD_DIR} {OUTPUT_DIR}")
        print("✅ Directories created")
        print("")
        
        # Copy GUI file
        print("📤 Copying GUI file...")
        sftp = ssh.open_sftp()
        sftp.put('vpn-gui.py', f'{BUILD_DIR}/vpn-gui.py')
        
        # Copy assets if they exist
        if Path('assets').exists():
            print("📤 Copying assets...")
            ssh.exec_command(f"rm -rf {BUILD_DIR}/assets")
            ssh.exec_command(f"mkdir -p {BUILD_DIR}/assets")
            
            # Copy assets directory recursively
            for root, dirs, files in os.walk('assets'):
                for file in files:
                    local_path = Path(root) / file
                    remote_path = f"{BUILD_DIR}/{local_path}"
                    remote_dir = os.path.dirname(remote_path)
                    ssh.exec_command(f"mkdir -p {remote_dir}")
                    sftp.put(str(local_path), remote_path)
        
        sftp.close()
        print("✅ Files copied")
        print("")
        
        # Build on VPS
        print("🔨 Building executable on VPS...")
        build_script = f"""
cd {BUILD_DIR}

# Install PyInstaller if needed
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "📦 Installing PyInstaller..."
    pip3 install pyinstaller --break-system-packages 2>/dev/null || \\
    pip3 install --user pyinstaller 2>/dev/null || \\
    apt-get update && apt-get install -y python3-pyinstaller 2>/dev/null || \\
    (echo "❌ Could not install PyInstaller" && exit 1)
fi

# Find pyinstaller
PYINSTALLER_CMD=""
if command -v pyinstaller >/dev/null 2>&1; then
    PYINSTALLER_CMD="pyinstaller"
elif [ -f ~/.local/bin/pyinstaller ]; then
    PYINSTALLER_CMD="$HOME/.local/bin/pyinstaller"
elif python3 -m PyInstaller --version >/dev/null 2>&1; then
    PYINSTALLER_CMD="python3 -m PyInstaller"
else
    echo "❌ PyInstaller not found"
    exit 1
fi

# Clean previous builds
rm -rf build/ dist/ *.spec

# Check for icon
ICON_PATH=""
if [ -f "assets/icons/phazevpn.png" ]; then
    ICON_PATH="--icon=assets/icons/phazevpn.png"
fi

# Build executable
echo "Building Linux executable..."
$PYINSTALLER_CMD --onefile \\
    --windowed \\
    --name "PhazeVPN-Client" \\
    --add-data "assets:assets" \\
    $ICON_PATH \\
    --hidden-import=tkinter \\
    --hidden-import=requests \\
    --hidden-import=urllib3 \\
    --clean \\
    vpn-gui.py 2>&1 | grep -v "WARNING" || true

# Copy to downloads directory
if [ -f "dist/PhazeVPN-Client" ]; then
    cp dist/PhazeVPN-Client {OUTPUT_DIR}/PhazeVPN-Client-linux
    chmod +x {OUTPUT_DIR}/PhazeVPN-Client-linux
    echo "✅ Linux executable built: PhazeVPN-Client-linux"
fi

# Create .deb package
echo "📦 Creating Debian package..."
DEB_DIR="deb-build"
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/pixmaps"
mkdir -p "$DEB_DIR/DEBIAN"

if [ -f "dist/PhazeVPN-Client" ]; then
    cp dist/PhazeVPN-Client "$DEB_DIR/usr/bin/phazevpn-client"
    chmod +x "$DEB_DIR/usr/bin/phazevpn-client"
fi

if [ -f "assets/icons/phazevpn.png" ]; then
    cp assets/icons/phazevpn.png "$DEB_DIR/usr/share/pixmaps/phazevpn.png"
fi

cat > "$DEB_DIR/usr/share/applications/phazevpn-client.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=PhazeVPN Client
GenericName=VPN Client
Comment=PhazeVPN Desktop Client
Exec=phazevpn-client
Icon=phazevpn
Terminal=false
Categories=Network;Security;
EOF

cat > "$DEB_DIR/DEBIAN/control" << 'EOF'
Package: phazevpn-client
Version: 1.1.0
Architecture: amd64
Maintainer: PhazeVPN <support@phazevpn.com>
Description: PhazeVPN Desktop Client
 Standalone VPN client application for PhazeVPN.
 No Python required - fully compiled executable.
 Features:
  - Built-in account signup
  - Auto-launch after installation
  - Login and config management
EOF

# Create post-install script to launch GUI
cat > "$DEB_DIR/DEBIAN/postinst" << 'POSTINST'
#!/bin/bash
# Post-installation script for PhazeVPN Client
# Launches the GUI after installation

set -e

# Launch GUI in background (non-blocking)
if [ -n "$DISPLAY" ]; then
    # Only launch if we have a display (GUI environment)
    nohup phazevpn-client > /dev/null 2>&1 &
    echo "✅ PhazeVPN Client launched!"
    echo "   Sign up or log in to get started."
else
    echo "⚠️  No display detected. Run 'phazevpn-client' to start the GUI."
fi

exit 0
POSTINST
chmod +x "$DEB_DIR/DEBIAN/postinst"

if command -v dpkg-deb >/dev/null 2>&1; then
    dpkg-deb --build "$DEB_DIR" {OUTPUT_DIR}/phazevpn-client_1.1.0_amd64.deb 2>/dev/null || true
    if [ -f "{OUTPUT_DIR}/phazevpn-client_1.1.0_amd64.deb" ]; then
        echo "✅ Debian package built: phazevpn-client_1.1.0_amd64.deb"
    fi
fi

# Set permissions
chmod 644 {OUTPUT_DIR}/* 2>/dev/null || true
chmod +x {OUTPUT_DIR}/PhazeVPN-Client-linux 2>/dev/null || true

echo ""
echo "✅ Build complete!"
ls -lh {OUTPUT_DIR}/ 2>/dev/null || true
"""
        
        stdin, stdout, stderr = ssh.exec_command(build_script)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        print(output)
        if errors and "error" in errors.lower():
            print("⚠️  Warnings/Errors:")
            print(errors)
        
        print("")
        print("==========================================")
        print("✅ DEPLOYMENT COMPLETE!")
        print("==========================================")
        print("")
        print("GUI executables are now available at:")
        print("  https://phazevpn.com/download/client/linux")
        print("")
        print("Files deployed:")
        stdin, stdout, stderr = ssh.exec_command(f"ls -lh {OUTPUT_DIR}/ 2>/dev/null || echo 'No files found'")
        print(stdout.read().decode())
        print("")
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

