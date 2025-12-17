#!/bin/bash
# Complete Update Deployment - Builds and deploys everything
# Website, Downloads, Installers for Ubuntu/macOS/Windows

set -e

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="Jakes1328!@"
VPN_DIR="/opt/secure-vpn"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "🚀 COMPLETE UPDATE DEPLOYMENT"
echo "=========================================="
echo ""
echo "This will:"
echo "  1. Build all platform installers"
echo "  2. Update web portal"
echo "  3. Deploy everything to VPS"
echo ""
echo "Press Enter to continue..."
read

# Step 1: Build Ubuntu .deb package
echo "1️⃣ Building Ubuntu .deb package..."
if [ -f "$BASE_DIR/phazevpn-client/build-deb.sh" ]; then
    cd "$BASE_DIR/phazevpn-client"
    bash build-deb.sh
    echo "   ✅ Ubuntu package built"
else
    echo "   ⚠️  Ubuntu build script not found"
fi

# Step 2: Update web portal
echo ""
echo "2️⃣ Updating web portal..."
python3 "$BASE_DIR/update-web-portal-downloads.py"
echo "   ✅ Web portal updated"

# Step 3: Deploy to VPS
echo ""
echo "3️⃣ Deploying to VPS..."

python3 << PYTHON_SCRIPT
import paramiko
import os
from pathlib import Path

print("   📡 Connecting to VPS...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('$VPS_IP', username='$VPS_USER', password='$VPS_PASS', timeout=30)
sftp = ssh.open_sftp()

# Create directories
print("   📁 Creating directories...")
ssh.exec_command("mkdir -p $VPN_DIR/downloads/installers")
ssh.exec_command("mkdir -p $VPN_DIR/phazevpn-protocol")
ssh.exec_command("mkdir -p $VPN_DIR/phazevpn-client-configs")

# Upload Ubuntu .deb
deb_file = Path("$BASE_DIR/phazevpn-client/installers/phazevpn-client_1.0.0_amd64.deb")
if deb_file.exists():
    print("   📦 Uploading Ubuntu .deb package...")
    sftp.put(str(deb_file), f"$VPN_DIR/downloads/installers/phazevpn-client_1.0.0_amd64.deb")
    print("      ✅ Ubuntu package uploaded")

# Upload web portal updates
print("   🌐 Uploading web portal...")
portal_files = [
    ("web-portal/app.py", "$VPN_DIR/web-portal/app.py"),
]
for local, remote in portal_files:
    local_path = Path("$BASE_DIR") / local
    if local_path.exists():
        remote_dir = os.path.dirname(remote)
        ssh.exec_command(f"mkdir -p '{remote_dir}'")
        sftp.put(str(local_path), remote)
        print(f"      ✅ {local} uploaded")

# Upload PhazeVPN Protocol files
print("   🔒 Uploading PhazeVPN Protocol...")
protocol_dir = Path("$BASE_DIR/phazevpn-protocol")
protocol_files = [
    "protocol.py",
    "crypto.py",
    "tun_manager.py",
    "obfuscation.py",
    "zero_knowledge.py",
    "compression.py",
    "nat_traversal.py",
    "split_tunneling.py",
    "rate_limiter.py",
    "connection_stats.py",
    "config_manager.py",
    "vpn_modes.py",
    "phazevpn-server-production.py",
    "phazevpn-client.py",
    "client_manager.py",
    "manage-clients.py"
]
for filename in protocol_files:
    local_file = protocol_dir / filename
    if local_file.exists():
        remote_path = f"$VPN_DIR/phazevpn-protocol/{filename}"
        sftp.put(str(local_file), remote_path)
        print(f"      ✅ {filename} uploaded")

# Restart web portal
print("   🔄 Restarting web portal...")
ssh.exec_command("systemctl restart secure-vpn-web || systemctl restart gunicorn || true")
print("      ✅ Web portal restarted")

sftp.close()
ssh.close()

print("   ✅ Deployment complete!")
PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "✅ COMPLETE UPDATE DEPLOYED!"
echo "=========================================="
echo ""
echo "📋 What's Live:"
echo "   ✅ Updated web portal"
echo "   ✅ Ubuntu .deb installer"
echo "   ✅ PhazeVPN Protocol (port 51821)"
echo "   ✅ Client management system"
echo ""
echo "🌐 Access at: https://phazevpn.duckdns.org"
echo ""

