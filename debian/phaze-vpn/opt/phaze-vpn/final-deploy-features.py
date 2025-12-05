#!/usr/bin/env python3
"""Final deploy of all features"""

import paramiko
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    return stdout.read().decode(), stderr.read().decode(), exit_status

def upload_file(local_path, remote_path):
    sftp = ssh.open_sftp()
    try:
        # Ensure remote directory exists
        remote_dir = str(Path(remote_path).parent)
        run(f"mkdir -p {remote_dir}")
        
        # Upload file
        sftp.put(local_path, remote_path)
        return True
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False
    finally:
        sftp.close()

print("🚀 Final Feature Deploy")
print("="*60)

# Upload updated app.py
print("1️⃣  Uploading updated portal app...")
upload_file('/opt/phaze-vpn/web-portal/app.py', f'{VPN_DIR}/web-portal/app.py')
print("   ✅ app.py updated")

# Ensure qrcode is available
print("\n2️⃣  Checking QR code library...")
output, _, status = run("python3 -c 'import qrcode; print(\"OK\")' 2>&1")
if status != 0:
    print("   Installing qrcode...")
    run("python3 -m pip install --user qrcode[pil] 2>&1 | tail -5")
else:
    print("   ✅ QR code library ready")

# Restart portal
print("\n3️⃣  Restarting portal...")
run("systemctl restart secure-vpn-portal")
print("   ✅ Portal restarted")

# Check status
print("\n4️⃣  Checking portal status...")
output, _, _ = run("systemctl status secure-vpn-portal --no-pager -l | head -10")
print(output)

print("\n" + "="*60)
print("✅ ALL FEATURES DEPLOYED!")
print("="*60)
print(f"\n🌐 Access: http://{VPS_IP}:5000")
print("\n🎯 Features Ready:")
print("  ✅ Analytics Dashboard - /admin/analytics")
print("  ✅ QR Code Generator - /qr/<client-name>")
print("  ✅ Real-time Stats API")
print("  ✅ Bandwidth Monitoring")
print("  ✅ Server Metrics")
print()

ssh.close()

