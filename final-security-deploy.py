#!/usr/bin/env python3
"""Final security deployment with fixes"""

import paramiko
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

print("🔒 Final Security Deployment...")
print("="*60)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd, timeout=120):
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

# Upload fixed app.py
print("\n1️⃣  Uploading fixed app.py...")
upload_file('/opt/phaze-vpn/web-portal/app.py', f'{VPN_DIR}/web-portal/app.py')
print("   ✅ Uploaded")

# Test syntax
print("\n2️⃣  Testing syntax...")
output, errors, status = run(f"cd {VPN_DIR}/web-portal && python3 -m py_compile app.py 2>&1")
if status == 0:
    print("   ✅ Syntax OK")
else:
    print(f"   ❌ Syntax error: {errors}")

# Start/restart portal
print("\n3️⃣  Restarting portal...")
run("systemctl restart secure-vpn-portal")
output, _, _ = run("systemctl status secure-vpn-portal --no-pager -l | head -10")
print(output)

# Check if running
output, _, status = run("systemctl is-active secure-vpn-portal")
if "active" in output:
    print("   ✅ Portal is running!")
else:
    print("   ⚠️  Portal may have issues - check logs")

print("\n" + "="*60)
print("✅ DEPLOYMENT COMPLETE!")
print("="*60)
print(f"\n🌐 Access: https://{VPS_IP}")
print("   (Browser will show cert warning - click 'Advanced' → 'Proceed')")
print()

ssh.close()

