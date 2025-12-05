#!/bin/bash
# Build .deb package and deploy to VPS
# Creates a working Linux package that installs properly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🔨 Building PhazeVPN Client .deb Package"
echo "=========================================="
echo ""

# Build the package
if [ -f "build-deb-proper.sh" ]; then
    bash build-deb-proper.sh
else
    echo "❌ build-deb-proper.sh not found"
    exit 1
fi

# Check if package was created
DEB_FILE="installers/phazevpn-client_1.0.0_amd64.deb"
if [ ! -f "$DEB_FILE" ]; then
    echo "❌ Package not created"
    exit 1
fi

echo ""
echo "=========================================="
echo "📤 Deploying to VPS"
echo "=========================================="
echo ""

# Deploy to VPS
python3 << 'PYTHON_EOF'
from paramiko import SSHClient, AutoAddPolicy, SFTPClient
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    
    # Create directory
    ssh.exec_command(f"mkdir -p {VPN_DIR}/phazevpn-client/installers")
    
    # Upload .deb file
    sftp = ssh.open_sftp()
    local_deb = Path("installers/phazevpn-client_1.0.0_amd64.deb")
    remote_deb = f"{VPN_DIR}/phazevpn-client/installers/phazevpn-client_1.0.0_amd64.deb"
    
    if local_deb.exists():
        sftp.put(str(local_deb), remote_deb)
        print(f"✅ Uploaded {local_deb.name}")
    else:
        print(f"❌ {local_deb} not found")
    
    # Upload install script
    local_install = Path("install-linux.sh")
    remote_install = f"{VPN_DIR}/phazevpn-client/install-linux.sh"
    
    if local_install.exists():
        sftp.put(str(local_install), remote_install)
        ssh.exec_command(f"chmod +x {remote_install}")
        print(f"✅ Uploaded install-linux.sh")
    
    sftp.close()
    ssh.close()
    
    print("✅ Deployment complete")
    print(f"   Package: {remote_deb}")
    print(f"   Installer: {remote_install}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
PYTHON_EOF

echo ""
echo "=========================================="
echo "✅ BUILD AND DEPLOY COMPLETE"
echo "=========================================="
echo ""
echo "📦 Package is now available on VPS:"
echo "   /opt/secure-vpn/phazevpn-client/installers/phazevpn-client_1.0.0_amd64.deb"
echo ""
echo "📥 Users can download from:"
echo "   https://phazevpn.duckdns.org/download/client/linux"
echo ""

