#!/usr/bin/env python3
"""
Restart web portal on VPS using paramiko
"""
import paramiko
from pathlib import Path
import os
import time

# Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', 'phazevpn.com')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_WEB_PORTAL_DIR = "/opt/phaze-vpn/web-portal"

def connect_vps():
    """Connect to VPS using SSH keys or password"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key_paths = [
        Path.home() / '.ssh' / 'id_rsa',
        Path.home() / '.ssh' / 'id_ed25519',
    ]
    
    for key_path in key_paths:
        if key_path.exists() and key_path.is_file():
            try:
                key = paramiko.RSAKey.from_private_key_file(str(key_path))
                ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    return ssh
                except:
                    continue
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        return ssh
    except:
        pass
    
    if VPS_PASSWORD:
        try:
            ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
            return ssh
        except:
            pass
    
    return None

print("=" * 60)
print("Restarting Web Portal on VPS")
print("=" * 60)
print()

ssh = connect_vps()
if not ssh:
    print("❌ Could not connect to VPS")
    exit(1)

try:
    # Kill existing processes
    print("[1/3] Stopping existing web portal...")
    ssh.exec_command("pkill -9 -f 'python.*app.py' || true")
    ssh.exec_command("pkill -9 -f flask || true")
    ssh.exec_command("lsof -ti:5000 | xargs kill -9 2>/dev/null || true")
    time.sleep(2)
    print("   ✅ Stopped")
    
    # Start web portal
    print("\n[2/3] Starting web portal...")
    stdin, stdout, stderr = ssh.exec_command(
        f"cd {VPS_WEB_PORTAL_DIR} && "
        f"nohup python3 app.py > /tmp/web.log 2>&1 &"
    )
    time.sleep(3)
    print("   ✅ Started")
    
    # Verify it's running
    print("\n[3/3] Verifying web portal is running...")
    stdin, stdout, stderr = ssh.exec_command("pgrep -f 'python.*app.py'")
    pid = stdout.read().decode().strip()
    if pid:
        print(f"   ✅ Web portal running (PID: {pid})")
        
        # Check logs for errors
        stdin, stdout, stderr = ssh.exec_command("tail -20 /tmp/web.log")
        logs = stdout.read().decode()
        if logs:
            print("\n   Recent logs:")
            print("   " + "\n   ".join(logs.split('\n')[-5:]))
    else:
        print("   ⚠️  Web portal might not be running")
        print("   Check /tmp/web.log for errors")
    
    print()
    print("=" * 60)
    print("✅ Web Portal Restarted!")
    print("=" * 60)
    print()
    print("Try logging in with admin/admin123 now!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    ssh.close()

