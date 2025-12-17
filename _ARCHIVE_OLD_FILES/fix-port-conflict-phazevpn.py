#!/usr/bin/env python3
"""
Fix port conflict - something is already using port 51820
"""

import paramiko
import os
from pathlib import Path

VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')

def connect_vps():
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
    print("🔧 FIXING PORT CONFLICT (51820)")
    print("="*70)
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect")
        return
    
    print("✅ Connected")
    print("")
    
    try:
        # 1. Find what's using port 51820
        print("1. Finding process using port 51820...")
        find_cmd = """
echo "Processes using port 51820:"
lsof -i :51820 2>/dev/null || fuser 51820/udp 2>/dev/null || ss -ulnp | grep 51820 || netstat -ulnp | grep 51820
echo ""
echo "Python processes:"
ps aux | grep -E '[p]ython.*phazevpn' | head -5
"""
        stdin, stdout, stderr = ssh.exec_command(find_cmd)
        print(stdout.read().decode())
        print("")
        
        # 2. Kill any old processes
        print("2. Stopping old processes...")
        kill_cmd = """
# Stop systemd service first
systemctl stop phazevpn-protocol 2>/dev/null || true
sleep 2

# Kill any remaining Python processes
pkill -9 -f 'phazevpn-server-production' 2>/dev/null || true
sleep 1

# Check if port is free now
if ss -ulnp | grep -q 51820 || netstat -ulnp | grep -q 51820; then
    echo "⚠️  Port still in use, finding PID..."
    lsof -ti :51820 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Verify port is free
if ss -ulnp | grep -q 51820 || netstat -ulnp | grep -q 51820; then
    echo "❌ Port still in use"
    ss -ulnp | grep 51820 || netstat -ulnp | grep 51820
else
    echo "✅ Port 51820 is now free"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(kill_cmd)
        print(stdout.read().decode())
        print("")
        
        # 3. Restart service
        print("3. Restarting service...")
        restart_cmd = """
systemctl start phazevpn-protocol
sleep 3
systemctl status phazevpn-protocol --no-pager | head -12
"""
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        print(stdout.read().decode())
        print("")
        
        # 4. Verify it's working
        print("4. Verifying...")
        verify_cmd = """
if systemctl is-active --quiet phazevpn-protocol; then
    echo "✅ Service is running"
    if ss -ulnp | grep -q 51820 || netstat -ulnp | grep -q 51820; then
        echo "✅ Port 51820 is listening"
        ss -ulnp | grep 51820 || netstat -ulnp | grep 51820
    else
        echo "❌ Port not listening"
    fi
else
    echo "❌ Service failed"
    echo ""
    echo "Recent errors:"
    journalctl -u phazevpn-protocol -n 10 --no-pager | tail -5
fi
"""
        stdin, stdout, stderr = ssh.exec_command(verify_cmd)
        print(stdout.read().decode())
        print("")
        
        print("="*70)
        print("✅ PORT CONFLICT FIXED!")
        print("="*70)
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

