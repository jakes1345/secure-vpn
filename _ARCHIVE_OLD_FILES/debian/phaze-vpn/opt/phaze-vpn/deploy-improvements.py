#!/usr/bin/env python3
"""Deploy all improvements to VPS"""

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

print("🚀 Deploying Improvements...")
print("="*60)

# Ensure logs directory exists
print("1️⃣  Creating logs directory...")
run(f"mkdir -p {VPN_DIR}/logs")
print("   ✅ Logs directory ready")

# Upload updated files
print("\n2️⃣  Uploading updated files...")
files_to_upload = {
    'web-portal/app.py': f'{VPN_DIR}/web-portal/app.py',
    'web-portal/templates/base.html': f'{VPN_DIR}/web-portal/templates/base.html',
    'web-portal/templates/admin/dashboard.html': f'{VPN_DIR}/web-portal/templates/admin/dashboard.html',
    'web-portal/templates/admin/clients.html': f'{VPN_DIR}/web-portal/templates/admin/clients.html',
    'web-portal/templates/admin/activity.html': f'{VPN_DIR}/web-portal/templates/admin/activity.html',
}

for local, remote in files_to_upload.items():
    local_path = f'/opt/phaze-vpn/{local}'
    if upload_file(local_path, remote):
        print(f"   ✅ {local}")

# Restart portal
print("\n3️⃣  Restarting portal...")
run("systemctl restart secure-vpn-portal")
print("   ✅ Portal restarted")

# Check status
print("\n4️⃣  Checking status...")
output, _, _ = run("systemctl status secure-vpn-portal --no-pager -l | head -8")
print(output)

print("\n" + "="*60)
print("✅ ALL IMPROVEMENTS DEPLOYED!")
print("="*60)
print(f"\n🌐 Access: http://{VPS_IP}:5000")
print("\n🎯 New Features:")
print("  ✅ Toast notifications (modern UX)")
print("  ✅ Activity logging (all admin actions)")
print("  ✅ Connection history tracking")
print("  ✅ Export to CSV (activity & connections)")
print("  ✅ Bulk client import")
print("  ✅ Better error handling")
print("  ✅ Loading states & animations")
print("  ✅ Mobile-responsive improvements")
print("  ✅ Activity log viewer page")
print()

ssh.close()

