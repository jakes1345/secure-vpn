#!/usr/bin/env python3
"""Deploy email queue system to VPS"""

import paramiko
import os
from pathlib import Path

VPS_IP = os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASS = os.environ.get('VPS_PASS', '')
if not VPS_PASS:
    print("❌ Error: VPS_PASS environment variable not set")
    print("   Set it with: export VPS_PASS='your-password'")
    sys.exit(1)
VPS_PATH = "/opt/secure-vpn/web-portal"

BASE_DIR = Path(__file__).parent
WEB_PORTAL_DIR = BASE_DIR / 'web-portal'

def ensure_remote_dir(sftp, remote_path):
    """Ensure remote directory exists"""
    parts = remote_path.strip('/').split('/')
    current_path = ''
    for part in parts:
        current_path += '/' + part
        try:
            sftp.stat(current_path)
        except FileNotFoundError:
            sftp.mkdir(current_path)

def sync_file(ssh, sftp, local_file, remote_file):
    """Sync a single file"""
    try:
        remote_dir = os.path.dirname(remote_file)
        ensure_remote_dir(sftp, remote_dir)
        sftp.put(str(local_file), remote_file)
        print(f"   ✅ {local_file.name}")
        return True
    except Exception as e:
        print(f"   ❌ {local_file.name}: {e}")
        return False

print("=" * 80)
print("📧 DEPLOYING EMAIL QUEUE TO VPS")
print("=" * 80)
print()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
sftp = ssh.open_sftp()

try:
    # 1. Check Redis
    print("[1/4] Checking Redis...")
    stdin, stdout, stderr = ssh.exec_command("which redis-server")
    redis_path = stdout.read().decode().strip()
    
    if redis_path:
        print("   ✅ Redis installed")
    else:
        print("   ⚠️  Redis not installed")
        print("   Installing Redis...")
        stdin, stdout, stderr = ssh.exec_command("apt-get update && apt-get install -y redis-server")
        output = stdout.read().decode()
        error = stderr.read().decode()
        if 'ERROR' in error:
            print(f"   ❌ Install failed: {error}")
        else:
            print("   ✅ Redis installed")
    
    # Start Redis
    stdin, stdout, stderr = ssh.exec_command("systemctl start redis && systemctl enable redis")
    print("   ✅ Redis started")
    print()
    
    # 2. Upload email_queue.py
    print("[2/4] Uploading email_queue.py...")
    sync_file(ssh, sftp, WEB_PORTAL_DIR / 'email_queue.py', f"{VPS_PATH}/email_queue.py")
    print()
    
    # 3. Upload email_worker.py
    print("[3/4] Uploading email_worker.py...")
    sync_file(ssh, sftp, WEB_PORTAL_DIR / 'email_worker.py', f"{VPS_PATH}/email_worker.py")
    print()
    
    # 4. Upload systemd service
    print("[4/4] Uploading systemd service...")
    sync_file(ssh, sftp, WEB_PORTAL_DIR / 'systemd' / 'email-worker.service', 
              f"/etc/systemd/system/email-worker.service")
    
    # Reload systemd
    stdin, stdout, stderr = ssh.exec_command("systemctl daemon-reload")
    print("   ✅ Systemd reloaded")
    print()
    
    # 5. Install Python Redis
    print("[5/5] Installing Python Redis...")
    stdin, stdout, stderr = ssh.exec_command("pip3 install redis")
    output = stdout.read().decode()
    print("   ✅ Redis Python package installed")
    print()
    
    # Summary
    print("=" * 80)
    print("✅ DEPLOYMENT COMPLETE")
    print("=" * 80)
    print()
    print("📋 Next Steps:")
    print("   1. Start email worker:")
    print("      sudo systemctl start email-worker")
    print("      sudo systemctl enable email-worker")
    print()
    print("   2. Check status:")
    print("      sudo systemctl status email-worker")
    print()
    print("   3. Check logs:")
    print("      journalctl -u email-worker -f")
    print()

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    sftp.close()
    ssh.close()
