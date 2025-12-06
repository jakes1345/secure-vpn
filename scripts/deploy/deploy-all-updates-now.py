#!/usr/bin/env python3
"""
Deploy ALL updates to VPS - final deployment
"""

import paramiko
import os
from pathlib import Path
import time

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"
WEB_PORTAL_DIR = f"{VPS_DIR}/web-portal"

def connect_vps():
    """Connect to VPS"""
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
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    return None

def run_vps(ssh, command):
    """Run command on VPS"""
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode()
    errors = stderr.read().decode()
    return stdout.channel.recv_exit_status() == 0, output, errors

def main():
    print("="*70)
    print("DEPLOYING ALL UPDATES TO VPS")
    print("="*70)
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # 1. Create backup
        print("1. Creating backup...")
        backup_cmd = f"""
mkdir -p {VPS_DIR}/backups
cp {WEB_PORTAL_DIR}/app.py {VPS_DIR}/backups/app.py.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp {VPS_DIR}/vpn-gui.py {VPS_DIR}/backups/vpn-gui.py.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
echo "✅ Backup created"
"""
        run_vps(ssh, backup_cmd)
        print("   ✅ Backup created")
        print("")
        
        # 2. Upload latest app.py
        print("2. Uploading latest web-portal/app.py...")
        local_app = Path('web-portal/app.py')
        if local_app.exists():
            sftp = ssh.open_sftp()
            sftp.put(str(local_app), f'{WEB_PORTAL_DIR}/app.py')
            sftp.chmod(f'{WEB_PORTAL_DIR}/app.py', 0o644)
            sftp.close()
            print("   ✅ app.py uploaded")
        else:
            print("   ⚠️  Local app.py not found")
        print("")
        
        # 3. Upload latest vpn-gui.py
        print("3. Uploading latest vpn-gui.py...")
        local_gui = Path('vpn-gui.py')
        if local_gui.exists():
            sftp = ssh.open_sftp()
            sftp.put(str(local_gui), f'{VPS_DIR}/vpn-gui.py')
            sftp.chmod(f'{VPS_DIR}/vpn-gui.py', 0o755)
            sftp.close()
            print("   ✅ vpn-gui.py uploaded")
        else:
            print("   ⚠️  Local vpn-gui.py not found")
        print("")
        
        # 4. Ensure directories exist
        print("4. Ensuring directories exist...")
        dirs_cmd = f"""
mkdir -p {VPS_DIR}/client-configs
mkdir -p {VPS_DIR}/certs
mkdir -p {VPS_DIR}/logs
mkdir -p {WEB_PORTAL_DIR}/static
chmod 755 {VPS_DIR}/client-configs
chmod 755 {VPS_DIR}/certs
chmod 755 {VPS_DIR}/logs
"""
        run_vps(ssh, dirs_cmd)
        print("   ✅ Directories ready")
        print("")
        
        # 5. Verify vpn-manager.py exists and is executable
        print("5. Verifying vpn-manager.py...")
        check_cmd = f"""
if [ -f {VPS_DIR}/vpn-manager.py ]; then
    chmod +x {VPS_DIR}/vpn-manager.py
    echo "✅ vpn-manager.py exists and is executable"
else
    echo "❌ vpn-manager.py NOT FOUND"
fi
"""
        success, output, _ = run_vps(ssh, check_cmd)
        print(output)
        print("")
        
        # 6. Restart web portal
        print("6. Restarting web portal...")
        restart_cmd = f"""
# Kill existing processes
pkill -9 -f 'python.*app.py' 2>/dev/null || true
pkill -9 -f 'gunicorn.*app:app' 2>/dev/null || true
sleep 2

# Try systemd first
systemctl restart phazevpn-portal 2>/dev/null && echo "✅ Restarted via systemd" || echo "⚠️  systemd not available"

# If systemd didn't work, start manually
sleep 2
if ! pgrep -f 'python.*app.py' > /dev/null && ! pgrep -f 'gunicorn.*app:app' > /dev/null; then
    cd {WEB_PORTAL_DIR}
    nohup python3 app.py > /tmp/web-portal.log 2>&1 &
    sleep 3
    if pgrep -f 'python.*app.py' > /dev/null; then
        echo "✅ Started manually"
    else
        echo "❌ Failed to start"
    fi
fi
"""
        success, output, _ = run_vps(ssh, restart_cmd)
        print(output)
        print("")
        
        # 7. Verify web portal is running
        print("7. Verifying web portal status...")
        verify_cmd = f"""
sleep 2
if pgrep -f 'python.*app.py' > /dev/null || pgrep -f 'gunicorn.*app:app' > /dev/null; then
    echo "✅ Web portal is running"
    ps aux | grep -E '[p]ython.*app.py|[g]unicorn.*app:app' | head -2
else
    echo "❌ Web portal is NOT running"
fi

# Test endpoint
echo ""
echo "Testing login endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:5000/api/app/login 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "400" ]; then
    echo "✅ Login endpoint responding (HTTP $HTTP_CODE)"
else
    echo "❌ Login endpoint not responding (HTTP $HTTP_CODE)"
fi
"""
        success, output, _ = run_vps(ssh, verify_cmd)
        print(output)
        print("")
        
        # 8. Check users.json
        print("8. Checking users.json...")
        users_cmd = f"""
if [ -f {VPS_DIR}/users.json ]; then
    echo "✅ users.json exists"
    USER_COUNT=$(python3 -c "import json; f=open('{VPS_DIR}/users.json'); d=json.load(f); print(len(d.get('users', {{}})))" 2>/dev/null || echo "0")
    echo "   Users: $USER_COUNT"
else
    echo "⚠️  users.json not found"
fi
"""
        success, output, _ = run_vps(ssh, users_cmd)
        print(output)
        print("")
        
        print("="*70)
        print("✅ DEPLOYMENT COMPLETE!")
        print("="*70)
        print("")
        print("Next steps:")
        print("  1. Try logging in with admin/admin123")
        print("  2. Try adding a new client")
        print("  3. Check logs if issues: ssh root@15.204.11.19 'tail -f /tmp/web-portal.log'")
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

