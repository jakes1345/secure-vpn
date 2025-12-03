#!/bin/bash
# Build .deb package directly on VPS (where filesystem permissions are correct)

echo "=========================================="
echo "🔨 Building .deb Package on VPS"
echo "=========================================="
echo ""

python3 << 'PYTHON_EOF'
from paramiko import SSHClient, AutoAddPolicy, SFTPClient
from pathlib import Path
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    
    # Upload build script and client files
    sftp = ssh.open_sftp()
    
    # Upload client script
    local_client = Path("phazevpn-client.py")
    if local_client.exists():
        remote_client = f"{VPN_DIR}/phazevpn-client/phazevpn-client.py"
        sftp.put(str(local_client), remote_client)
        print("✅ Uploaded phazevpn-client.py")
    
    # Upload build script
    build_script = """
#!/bin/bash
set -e
cd /tmp
rm -rf deb-build
mkdir -p deb-build/DEBIAN
mkdir -p deb-build/usr/bin
mkdir -p deb-build/usr/share/phazevpn-client
mkdir -p deb-build/usr/share/applications

# Copy client
cp /opt/secure-vpn/phazevpn-client/phazevpn-client.py deb-build/usr/share/phazevpn-client/
chmod 755 deb-build/usr/share/phazevpn-client/phazevpn-client.py

# Create launcher
cat > deb-build/usr/bin/phazevpn-client << 'LAUNCHER_EOF'
#!/bin/bash
python3 /usr/share/phazevpn-client/phazevpn-client.py "$@"
LAUNCHER_EOF
chmod 755 deb-build/usr/bin/phazevpn-client

# Create desktop entry
cat > deb-build/usr/share/applications/phazevpn-client.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Name=PhazeVPN Client
Comment=Secure VPN Client
Exec=/usr/bin/phazevpn-client
Icon=network-vpn
Terminal=false
Type=Application
Categories=Network;Security;
DESKTOP_EOF
chmod 644 deb-build/usr/share/applications/phazevpn-client.desktop

# Create control
cat > deb-build/DEBIAN/control << 'CONTROL_EOF'
Package: phazevpn-client
Version: 1.0.0
Architecture: amd64
Maintainer: PhazeVPN
Description: PhazeVPN Secure VPN Client
Depends: python3, python3-requests, openvpn
Priority: optional
Section: net
CONTROL_EOF

# Create postinst
cat > deb-build/DEBIAN/postinst << 'POSTINST_EOF'
#!/bin/bash
pip3 install --quiet requests 2>/dev/null || true
update-desktop-database /usr/share/applications/ 2>/dev/null || true
POSTINST_EOF
chmod 755 deb-build/DEBIAN/postinst

# Set permissions
chmod 755 deb-build/DEBIAN
chmod 644 deb-build/DEBIAN/control

# Build package
mkdir -p /opt/secure-vpn/phazevpn-client/installers
fakeroot dpkg-deb --build deb-build /opt/secure-vpn/phazevpn-client/installers/phazevpn-client_1.0.0_amd64.deb

echo "✅ Package built: /opt/secure-vpn/phazevpn-client/installers/phazevpn-client_1.0.0_amd64.deb"
"""
    
    # Write build script to VPS
    with sftp.file(f"{VPN_DIR}/build-deb-on-vps.sh", 'w') as f:
        f.write(build_script)
    sftp.close()
    
    # Make executable and run
    ssh.exec_command(f"chmod +x {VPN_DIR}/build-deb-on-vps.sh")
    stdin, stdout, stderr = ssh.exec_command(f"bash {VPN_DIR}/build-deb-on-vps.sh")
    output = stdout.read().decode()
    errors = stderr.read().decode()
    
    print(output)
    if errors and "error" in errors.lower():
        print(f"⚠️  Errors: {errors[:200]}")
    
    # Download the built package
    sftp = ssh.open_sftp()
    remote_deb = f"{VPN_DIR}/phazevpn-client/installers/phazevpn-client_1.0.0_amd64.deb"
    local_deb = Path("installers/phazevpn-client_1.0.0_amd64.deb")
    local_deb.parent.mkdir(exist_ok=True)
    
    try:
        sftp.get(remote_deb, str(local_deb))
        print(f"✅ Downloaded package to {local_deb}")
    except Exception as e:
        print(f"⚠️  Could not download: {e}")
        print(f"   Package is on VPS at: {remote_deb}")
    
    sftp.close()
    ssh.close()
    
    print("✅ Build complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
PYTHON_EOF

echo ""
echo "=========================================="
echo "✅ Done!"
echo "=========================================="

