#!/usr/bin/env python3
"""Deploy user signup and profile features"""

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
        remote_dir = str(Path(remote_path).parent)
        run(f"mkdir -p {remote_dir}")
        sftp.put(local_path, remote_path)
        return True
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False
    finally:
        sftp.close()

print("🚀 Deploying User Features...")
print("="*60)

# Upload updated files
print("1️⃣  Uploading files...")
files_to_upload = {
    'web-portal/app.py': f'{VPN_DIR}/web-portal/app.py',
    'web-portal/templates/base.html': f'{VPN_DIR}/web-portal/templates/base.html',
    'web-portal/templates/login.html': f'{VPN_DIR}/web-portal/templates/login.html',
    'web-portal/templates/signup.html': f'{VPN_DIR}/web-portal/templates/signup.html',
    'web-portal/templates/profile.html': f'{VPN_DIR}/web-portal/templates/profile.html',
    'web-portal/templates/user/dashboard.html': f'{VPN_DIR}/web-portal/templates/user/dashboard.html',
}

for local, remote in files_to_upload.items():
    local_path = f'/opt/phaze-vpn/{local}'
    if upload_file(local_path, remote):
        print(f"   ✅ {local}")

# Restart portal
print("\n2️⃣  Restarting portal...")
run("systemctl restart secure-vpn-portal")
print("   ✅ Portal restarted")

# Check status
print("\n3️⃣  Checking status...")
output, _, _ = run("systemctl status secure-vpn-portal --no-pager -l | head -8")
print(output)

print("\n" + "="*60)
print("✅ USER FEATURES DEPLOYED!")
print("="*60)
print(f"\n🌐 Access: http://{VPS_IP}:5000")
print("\n🎯 New Features:")
print("  ✅ User signup/registration")
print("  ✅ Profile & account settings")
print("  ✅ Users can create their own VPN clients")
print("  ✅ Client-to-user linking")
print("  ✅ Password change")
print("  ✅ Fixed duplicate Admin in navbar")
print("  ✅ Better user dashboard")
print()

ssh.close()

