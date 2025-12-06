#!/bin/bash
# Deploy Massive Update: Website, Downloads, Installers
# Updates everything for PhazeVPN Protocol

set -e

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="Jakes1328!@"
VPN_DIR="/opt/secure-vpn"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "🚀 DEPLOYING MASSIVE UPDATE"
echo "=========================================="
echo ""
echo "This will deploy:"
echo "  1. Updated web portal (PhazeVPN Protocol priority)"
echo "  2. All platform installers (.deb, .app, .exe)"
echo "  3. Updated download system"
echo "  4. Client management"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Build all installers first
echo "1️⃣ Building all installers..."
bash "$BASE_DIR/create-platform-installers.sh"

# Deploy to VPS
echo ""
echo "2️⃣ Deploying to VPS..."

# Use Python for deployment
python3 << PYTHON_SCRIPT
import paramiko
import os
from pathlib import Path

print("📡 Connecting to VPS...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('$VPS_IP', username='$VPS_USER', password='$VPS_PASS', timeout=30)
sftp = ssh.open_sftp()

# Upload installers
print("3️⃣ Uploading installers...")
installers_dir = "$VPN_DIR/downloads/installers"
ssh.exec_command(f"mkdir -p {installers_dir}")

# Upload .deb
deb_file = Path("$BASE_DIR/build-output/phazevpn-client_1.0.0_amd64.deb")
if deb_file.exists():
    sftp.put(str(deb_file), f"{installers_dir}/phazevpn-client_1.0.0_amd64.deb")
    print("   ✅ Ubuntu .deb uploaded")

# Upload macOS .app (if exists)
macos_app = Path("$BASE_DIR/build-output/PhazeVPN.app")
if macos_app.exists():
    # Create tarball
    import subprocess
    subprocess.run(["tar", "-czf", "$BASE_DIR/build-output/PhazeVPN.app.tar.gz", "-C", str(macos_app.parent), "PhazeVPN.app"])
    sftp.put("$BASE_DIR/build-output/PhazeVPN.app.tar.gz", f"{installers_dir}/PhazeVPN.app.tar.gz")
    print("   ✅ macOS .app uploaded")

# Upload Windows structure (if exists)
win_dir = Path("$BASE_DIR/build-output/phazevpn-client-windows")
if win_dir.exists():
    # Create zip
    import subprocess
    subprocess.run(["zip", "-r", "$BASE_DIR/build-output/phazevpn-client-windows.zip", str(win_dir)])
    sftp.put("$BASE_DIR/build-output/phazevpn-client-windows.zip", f"{installers_dir}/phazevpn-client-windows.zip")
    print("   ✅ Windows installer uploaded")

sftp.close()
ssh.close()

print("✅ Deployment complete!")
PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "✅ MASSIVE UPDATE DEPLOYED!"
echo "=========================================="

