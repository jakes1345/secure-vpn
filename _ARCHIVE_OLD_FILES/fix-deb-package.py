#!/usr/bin/env python3
"""
Fix and rebuild .deb package properly on VPS
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR_ON_VPS = "/opt/secure-vpn"

print("=" * 70)
print("🔧 FIXING .deb PACKAGE")
print("=" * 70)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Rebuild .deb with proper structure
    print("🔨 Rebuilding .deb package...")
    rebuild_script = f"""
cd {VPN_DIR_ON_VPS}/phazevpn-client
rm -rf deb-build installers/*.deb

# Create proper structure
mkdir -p deb-build/DEBIAN
mkdir -p deb-build/usr/bin
mkdir -p deb-build/usr/share/phazevpn-client
mkdir -p deb-build/usr/share/applications

# Copy client
cp phazevpn-client.py deb-build/usr/share/phazevpn-client/
chmod 755 deb-build/usr/share/phazevpn-client/phazevpn-client.py

# Create launcher
cat > deb-build/usr/bin/phazevpn-client << 'EOF'
#!/bin/bash
python3 /usr/share/phazevpn-client/phazevpn-client.py "$@"
EOF
chmod 755 deb-build/usr/bin/phazevpn-client

# Desktop entry
cat > deb-build/usr/share/applications/phazevpn-client.desktop << 'EOF'
[Desktop Entry]
Name=PhazeVPN Client
Comment=Secure VPN Client
Exec=/usr/bin/phazevpn-client
Icon=network-vpn
Terminal=false
Type=Application
Categories=Network;Security;
EOF

# Control file
cat > deb-build/DEBIAN/control << 'EOF'
Package: phazevpn-client
Version: 1.0.0
Architecture: amd64
Maintainer: PhazeVPN <support@phazevpn.duckdns.org>
Description: PhazeVPN Secure VPN Client
 Professional VPN client with automatic configuration and one-click connectivity.
Depends: python3 (>= 3.6), python3-requests, openvpn
Priority: optional
Section: net
Homepage: https://phazevpn.duckdns.org
EOF

# Postinst
cat > deb-build/DEBIAN/postinst << 'EOF'
#!/bin/bash
set -e
pip3 install --quiet requests 2>/dev/null || true
update-desktop-database /usr/share/applications/ 2>/dev/null || true
echo "PhazeVPN Client installed successfully!"
EOF
chmod 755 deb-build/DEBIAN/postinst

# Fix ALL permissions
chmod 755 deb-build
chmod 755 deb-build/DEBIAN
find deb-build -type d -exec chmod 755 {{}} \\;
find deb-build -type f -exec chmod 644 {{}} \\;
chmod 755 deb-build/usr/bin/phazevpn-client
chmod 755 deb-build/usr/share/phazevpn-client/phazevpn-client.py
chmod 755 deb-build/DEBIAN/postinst

# Verify permissions
echo "DEBIAN permissions:"
stat -c "%a %n" deb-build/DEBIAN

# Build package using -b flag (build binary package)
mkdir -p installers
dpkg-deb -b deb-build installers/phazevpn-client_1.0.0_amd64.deb 2>&1

# Verify package
if [ -f installers/phazevpn-client_1.0.0_amd64.deb ]; then
    echo ""
    echo "✅ Package built!"
    echo "Verifying package:"
    dpkg-deb -I installers/phazevpn-client_1.0.0_amd64.deb
    echo ""
    echo "Testing package install (dry run):"
    dpkg --dry-run -i installers/phazevpn-client_1.0.0_amd64.deb 2>&1 | head -5
else
    echo "❌ Build failed"
    exit 1
fi
"""
    
    stdin, stdout, stderr = ssh.exec_command(rebuild_script)
    output = stdout.read().decode()
    errors = stderr.read().decode()
    
    print(output)
    if errors and "error" in errors.lower():
        print("Errors:", errors)
    
    print("")
    print("=" * 70)
    print("✅ PACKAGE REBUILT")
    print("=" * 70)
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

