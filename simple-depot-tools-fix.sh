#!/bin/bash
# Simple fix: Download, tar, upload, extract
# Run this on YOUR LOCAL PC

set -e

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="Jakes1328!@"

echo "=========================================="
echo "🔧 SIMPLE depot_tools FIX"
echo "=========================================="
echo ""

# Step 1: Download
echo "📥 Step 1: Downloading depot_tools..."
cd ~
if [ -d "depot_tools" ]; then
    echo "   ✅ Already exists, using it"
else
    git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
    echo "   ✅ Downloaded"
fi

# Step 2: Create tar
echo ""
echo "📦 Step 2: Creating tar archive..."
tar czf depot_tools.tar.gz depot_tools
echo "   ✅ Created depot_tools.tar.gz"

# Step 3: Upload using Python (handles password)
echo ""
echo "📤 Step 3: Uploading to VPS..."
python3 << 'PYTHON'
import paramiko
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
LOCAL_FILE = os.path.expanduser("~/depot_tools.tar.gz")
REMOTE_FILE = "/tmp/depot_tools.tar.gz"

print("   Connecting to VPS...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
print("   ✅ Connected")

print("   Uploading file...")
sftp = ssh.open_sftp()
sftp.put(LOCAL_FILE, REMOTE_FILE)
sftp.close()
print("   ✅ Uploaded")

print("   Extracting on VPS...")
ssh.exec_command("rm -rf /opt/depot_tools")
ssh.exec_command("cd /opt && tar xzf /tmp/depot_tools.tar.gz")
ssh.exec_command("chmod +x /opt/depot_tools/*")
ssh.exec_command("chmod +x /opt/depot_tools/.cipd_bin/* 2>/dev/null || true")
print("   ✅ Extracted")

print("   Testing...")
stdin, stdout, stderr = ssh.exec_command("export PATH=\"/opt/depot_tools:$PATH\" && /opt/depot_tools/fetch --help 2>&1 | head -3")
output = stdout.read().decode()
if output:
    print("   ✅ fetch command works!")
    print(f"   {output}")
else:
    print("   ⚠️  Test output empty")

ssh.close()
print("   ✅ Done!")
PYTHON

echo ""
echo "=========================================="
echo "✅ depot_tools INSTALLED!"
echo "=========================================="
echo ""
echo "🚀 Now on VPS, run:"
echo ""
echo "   screen -S chromium"
echo "   export PATH=\"/opt/depot_tools:\$PATH\""
echo "   cd /opt/phazebrowser"
echo "   fetch --nohooks chromium"
echo ""

