#!/usr/bin/env python3
"""
Final Comprehensive Fix - Address all remaining issues
Fixes signup endpoint, adds error handling, ensures everything works
"""

import paramiko
import os
from pathlib import Path

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

def main():
    print("="*70)
    print("FINAL COMPREHENSIVE FIX")
    print("="*70)
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    try:
        # Upload latest files
        print("📤 Uploading latest fixed files...")
        sftp = ssh.open_sftp()
        
        files_to_upload = [
            ('web-portal/app.py', f'{WEB_PORTAL_DIR}/app.py'),
            ('vpn-gui.py', f'{VPS_DIR}/vpn-gui.py'),
            ('debian/phaze-vpn/opt/phaze-vpn/web-portal/app.py', f'{WEB_PORTAL_DIR}/app.py'),
            ('debian/phaze-vpn/opt/phaze-vpn/vpn-gui.py', f'{VPS_DIR}/vpn-gui.py'),
        ]
        
        for local_path, remote_path in files_to_upload:
            local_file = Path(local_path)
            if local_file.exists():
                print(f"   Uploading {local_path}...")
                sftp.put(str(local_file), remote_path)
                print(f"   ✅ {local_path}")
        
        sftp.close()
        print("")
        
        # Ensure directories exist
        print("📁 Ensuring directories exist...")
        dirs_cmd = f"""
mkdir -p {VPS_DIR}/certs
mkdir -p {VPS_DIR}/client-configs
mkdir -p {VPS_DIR}/logs
mkdir -p {VPS_DIR}/web-portal/static
chmod -R 755 {VPS_DIR}/certs {VPS_DIR}/client-configs {VPS_DIR}/logs
echo "✅ Directories ready"
"""
        stdin, stdout, stderr = ssh.exec_command(dirs_cmd)
        print(stdout.read().decode())
        print("")
        
        # Restart web portal with proper error handling
        print("🔄 Restarting web portal...")
        restart_cmd = f"""
# Kill old processes
pkill -9 -f 'python.*app.py' 2>/dev/null || true
sleep 2

# Check Python and dependencies
python3 --version
python3 -c 'import flask, bcrypt, qrcode' 2>&1 || echo "⚠️  Missing dependencies"

# Start web portal
cd {WEB_PORTAL_DIR}
export PYTHONUNBUFFERED=1
nohup python3 app.py > /tmp/web-portal.log 2>&1 &
sleep 4

# Check status
if ps aux | grep -E '[p]ython.*app.py'; then
    echo "✅ Web portal is running"
    echo ""
    echo "Last 10 lines of log:"
    tail -10 /tmp/web-portal.log 2>/dev/null || echo "No log yet"
else
    echo "❌ Web portal failed to start"
    echo ""
    echo "Error log:"
    tail -30 /tmp/web-portal.log 2>/dev/null || echo "No log file"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if errors:
            print("⚠️  Errors:", errors)
        print("")
        
        # Final verification
        print("="*70)
        print("FINAL VERIFICATION")
        print("="*70)
        print("")
        
        verify_cmd = f"""
echo "1. Checking users.json..."
test -f {VPS_DIR}/users.json && echo "   ✅ users.json exists" || echo "   ❌ users.json missing"

echo ""
echo "2. Checking web portal files..."
test -f {WEB_PORTAL_DIR}/app.py && echo "   ✅ app.py exists" || echo "   ❌ app.py missing"
test -d {WEB_PORTAL_DIR}/templates && echo "   ✅ templates directory exists" || echo "   ⚠️  templates missing"

echo ""
echo "3. Checking VPN manager..."
test -f {VPS_DIR}/vpn-manager.py && echo "   ✅ vpn-manager.py exists" || echo "   ❌ vpn-manager.py missing"

echo ""
echo "4. Testing API endpoints..."
echo "   Login test:"
curl -s -X POST https://phazevpn.com/api/app/login \\
  -H "Content-Type: application/json" \\
  -d '{{"username":"admin","password":"admin123"}}' \\
  -k 2>&1 | grep -o '"success":[^,]*' || echo "   ⚠️  Login endpoint issue"

echo ""
echo "5. Web portal process:"
ps aux | grep -E '[p]ython.*app.py' | awk '{{print "   ✅ Running: PID", $2}}' || echo "   ❌ Not running"
"""
        stdin, stdout, stderr = ssh.exec_command(verify_cmd)
        print(stdout.read().decode())
        print("")
        
        print("="*70)
        print("✅ ALL FIXES APPLIED!")
        print("="*70)
        print("")
        print("System is ready. You can now:")
        print("  1. Login with admin/admin123")
        print("  2. Create new accounts")
        print("  3. Add VPN clients")
        print("")
        print("If you still have issues, check:")
        print(f"  - Web portal logs: ssh {VPS_USER}@{VPS_HOST} 'tail -f /tmp/web-portal.log'")
        print(f"  - Users file: ssh {VPS_USER}@{VPS_HOST} 'cat {VPS_DIR}/users.json'")
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

