#!/usr/bin/env python3
"""
Restart services on VPS after deployment
"""

import time
from paramiko import SSHClient, AutoAddPolicy

# VPS Configuration
VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("==========================================")
print("🔄 RESTARTING SERVICES ON VPS")
print("==========================================")
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Restart OpenVPN
    print("1️⃣ Restarting OpenVPN...")
    stdin, stdout, stderr = ssh.exec_command("pkill -x openvpn; sleep 2; cd /opt/secure-vpn && nohup openvpn --config config/server.conf --log logs/server.log --daemon > /dev/null 2>&1; sleep 2; pgrep -x openvpn && echo '✅ OpenVPN restarted' || echo '❌ Failed'")
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    print(output)
    if error:
        print(f"   ⚠️  {error}")
    print("")
    
    # Restart Web Portal
    print("2️⃣ Restarting Web Portal...")
    stdin, stdout, stderr = ssh.exec_command("pkill -f 'app.py'; sleep 2; cd /opt/secure-vpn/web-portal && nohup python3 app.py > /dev/null 2>&1 &; sleep 2; pgrep -f 'app.py' && echo '✅ Web portal restarted' || echo '❌ Failed'")
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    print(output)
    if error:
        print(f"   ⚠️  {error}")
    print("")
    
    # Verify Services
    print("3️⃣ Verifying Services...")
    stdin, stdout, stderr = ssh.exec_command("echo 'OpenVPN:' && (pgrep -x openvpn >/dev/null && echo '✅ Running' || echo '❌ Not running') && echo 'Web Portal:' && (pgrep -f 'app.py' >/dev/null && echo '✅ Running' || echo '❌ Not running')")
    output = stdout.read().decode().strip()
    print(output)
    print("")
    
    # Check Ports
    print("4️⃣ Checking Listening Ports...")
    stdin, stdout, stderr = ssh.exec_command("echo 'OpenVPN (1194):' && (ss -ulnp 2>/dev/null | grep -q 1194 && echo '✅ Listening' || echo '❌ Not listening') && echo 'Web Portal (8081):' && (ss -tlnp 2>/dev/null | grep -q 8081 && echo '✅ Listening' || echo '❌ Not listening')")
    output = stdout.read().decode().strip()
    print(output)
    print("")
    
    print("==========================================")
    print("✅ SERVICES RESTARTED")
    print("==========================================")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

