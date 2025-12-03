#!/usr/bin/env python3
"""
Build .deb package on VPS where permissions are correct
"""

from paramiko import SSHClient, AutoAddPolicy, SFTPClient
from pathlib import Path
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR_ON_VPS = "/opt/secure-vpn"
BASE_DIR = Path(__file__).parent

print("=" * 70)
print("🔨 BUILDING .deb PACKAGE ON VPS")
print("=" * 70)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Upload client file
    print("📤 Uploading client file...")
    sftp = ssh.open_sftp()
    sftp.put(
        str(BASE_DIR / 'phazevpn-client' / 'phazevpn-client.py'),
        f'{VPN_DIR_ON_VPS}/phazevpn-client/phazevpn-client.py'
    )
    sftp.close()
    print("   ✅ Uploaded")
    print("")
    
    # Build .deb package on VPS
    print("🔨 Building .deb package on VPS...")
    build_script = f"""
cd {VPN_DIR_ON_VPS}/phazevpn-client
mkdir -p deb-build/DEBIAN
mkdir -p deb-build/usr/bin
mkdir -p deb-build/usr/share/phazevpn-client
mkdir -p deb-build/usr/share/applications

# Copy files
cp phazevpn-client.py deb-build/usr/share/phazevpn-client/
chmod 755 deb-build/usr/share/phazevpn-client/phazevpn-client.py

# Create launcher
cat > deb-build/usr/bin/phazevpn-client << 'EOF'
#!/bin/bash
python3 /usr/share/phazevpn-client/phazevpn-client.py "$@"
EOF
chmod 755 deb-build/usr/bin/phazevpn-client

# Create desktop entry
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

# Create control
cat > deb-build/DEBIAN/control << 'EOF'
Package: phazevpn-client
Version: 1.0.0
Architecture: amd64
Maintainer: PhazeVPN <support@phazevpn.duckdns.org>
Description: PhazeVPN Secure VPN Client
 Professional VPN client with automatic configuration.
Depends: python3 (>= 3.6), python3-requests, openvpn
Priority: optional
Section: net
Homepage: https://phazevpn.duckdns.org
EOF

# Create postinst
cat > deb-build/DEBIAN/postinst << 'EOF'
#!/bin/bash
pip3 install --quiet requests 2>/dev/null || true
update-desktop-database /usr/share/applications/ 2>/dev/null || true
EOF
chmod 755 deb-build/DEBIAN/postinst

# Fix permissions
chmod 755 deb-build/DEBIAN
chmod 755 deb-build

# Build package
mkdir -p installers
dpkg-deb --build deb-build installers/phazevpn-client_1.0.0_amd64.deb 2>&1

if [ -f installers/phazevpn-client_1.0.0_amd64.deb ]; then
    echo "✅ .deb created successfully"
    ls -lh installers/phazevpn-client_1.0.0_amd64.deb
    dpkg -I installers/phazevpn-client_1.0.0_amd64.deb | head -10
else
    echo "❌ .deb build failed"
fi
"""
    
    stdin, stdout, stderr = ssh.exec_command(build_script)
    output = stdout.read().decode()
    errors = stderr.read().decode()
    
    print(output)
    if errors:
        print("Errors:", errors)
    print("")
    
    # Download .deb if created
    print("📥 Downloading .deb package...")
    stdin, stdout, stderr = ssh.exec_command(f"test -f {VPN_DIR_ON_VPS}/phazevpn-client/installers/phazevpn-client_1.0.0_amd64.deb && echo 'EXISTS' || echo 'MISSING'")
    exists = stdout.read().decode().strip()
    
    if exists == "EXISTS":
        sftp = ssh.open_sftp()
        sftp.get(
            f'{VPN_DIR_ON_VPS}/phazevpn-client/installers/phazevpn-client_1.0.0_amd64.deb',
            str(BASE_DIR / 'phazevpn-client' / 'installers' / 'phazevpn-client_1.0.0_amd64.deb')
        )
        sftp.close()
        print("   ✅ Downloaded .deb package")
        print("")
        print("📦 Package location:")
        print(f"   {BASE_DIR / 'phazevpn-client' / 'installers' / 'phazevpn-client_1.0.0_amd64.deb'}")
    else:
        print("   ⚠️  .deb not created on VPS")
    
    print("")
    print("=" * 70)
    print("✅ BUILD COMPLETE")
    print("=" * 70)
    print("")
    print("🌐 .deb package available at:")
    print(f"   {VPN_DIR_ON_VPS}/phazevpn-client/installers/phazevpn-client_1.0.0_amd64.deb")
    print("")
    print("📥 Download URL:")
    print("   https://phazevpn.duckdns.org/download/client/linux")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

