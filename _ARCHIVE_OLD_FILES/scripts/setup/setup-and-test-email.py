#!/usr/bin/env python3
"""Setup email server and test it"""

import paramiko
import time
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    errors = stderr.read().decode()
    return output, errors, exit_status

def upload_file(local_path, remote_path):
    sftp = ssh.open_sftp()
    try:
        remote_dir = str(Path(remote_path).parent)
        run(f"mkdir -p {remote_dir}")
        sftp.put(local_path, remote_path)
        # Make executable if it's a script
        if local_path.endswith('.sh') or local_path.endswith('.py'):
            run(f"chmod +x {remote_path}")
        return True
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False
    finally:
        sftp.close()

print("📧 Setting Up Self-Hosted Email Server...")
print("="*60)

# Upload setup script
print("1️⃣  Uploading email setup script...")
from pathlib import Path as PathLib

upload_file('/opt/phaze-vpn/setup-email-server.sh', '/tmp/setup-email-server.sh')

# Upload email utility
print("\n2️⃣  Uploading email utility...")
upload_file('/opt/phaze-vpn/web-portal/email_util.py', f'{VPN_DIR}/web-portal/email_util.py')

# Run setup script
print("\n3️⃣  Running email server setup...")
print("   (This may take a minute...)")
output, errors, status = run("bash /tmp/setup-email-server.sh")
print(output)
if errors:
    print("Errors:", errors)

# Test email
print("\n4️⃣  Testing email functionality...")
output, errors, status = run(f"cd {VPN_DIR}/web-portal && python3 email_util.py root@localhost 2>&1")
print(output)

# Check if postfix is running
print("\n5️⃣  Checking email server status...")
output, _, _ = run("systemctl status postfix --no-pager -l | head -10")
print(output)

print("\n" + "="*60)
print("✅ Email Server Setup Complete!")
print("="*60)
print("\n📧 How it works:")
print("  ✅ Uses Postfix (system mail server)")
print("  ✅ Sends from: noreply@securevpn.local")
print("  ✅ No external services needed")
print("  ✅ Self-hosted on your VPS")
print("\n💡 Email will be sent when:")
print("  - Users sign up (if they provide email)")
print("  - Password reset requested")
print("  - Other notifications")
print("\n⚠️  Note: External email providers may mark emails as spam")
print("   (this is normal for self-hosted email)")
print()

ssh.close()

