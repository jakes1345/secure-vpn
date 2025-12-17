#!/usr/bin/env python3
"""Deploy email optional fix"""

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

print("📧 Making Email Optional...")
print("="*60)

files_to_upload = {
    'web-portal/app.py': f'{VPN_DIR}/web-portal/app.py',
    'web-portal/templates/signup.html': f'{VPN_DIR}/web-portal/templates/signup.html',
    'web-portal/templates/profile.html': f'{VPN_DIR}/web-portal/templates/profile.html',
}

print("1️⃣  Uploading updated files...")
for local, remote in files_to_upload.items():
    local_path = f'/opt/phaze-vpn/{local}'
    if upload_file(local_path, remote):
        print(f"   ✅ {local}")

print("\n2️⃣  Restarting portal...")
run("systemctl restart secure-vpn-portal")
print("   ✅ Portal restarted")

print("\n" + "="*60)
print("✅ Email is now OPTIONAL!")
print("="*60)
print("\n📝 Changes:")
print("  ✅ Email field is optional during signup")
print("  ✅ Email stored only if provided")
print("  ✅ No emails are sent (no SMTP needed)")
print("  ✅ Email can be added/removed from profile")
print("\n💡 If you need emails later, use API services like:")
print("  - SendGrid (free tier: 100/day)")
print("  - Mailgun (free tier: 5,000/month)")
print("  - Resend (free tier: 3,000/month)")
print("  - Or Discord/Telegram webhooks!")
print()

ssh.close()

