#!/usr/bin/env python3
"""Wait for dh.pem to generate then restart VPN"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)

def check(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    return stdout.read().decode().strip()

print("⏳ Waiting for dh.pem to generate...")
print("   (Checking every 10 seconds, max 3 minutes)\n")

for i in range(18):  # 3 minutes max
    size = check(f"stat -c%s {VPN_DIR}/certs/dh.pem 2>/dev/null || echo '0'")
    size_int = int(size) if size.isdigit() else 0
    
    if size_int > 100:  # dh.pem should be several KB
        print(f"✅ dh.pem is ready! ({size_int/1024:.1f} KB)")
        break
    else:
        print(f"   Still generating... ({i*10}s elapsed)")
        time.sleep(10)
else:
    print("⚠️  Still generating after 3 minutes, checking if process is running...")
    proc = check("ps aux | grep 'openssl dhparam' | grep -v grep")
    if proc:
        print("   Process still running, may take longer...")
    else:
        print("   Process not found, may have failed")

print("\n🔄 Restarting VPN service...")
check("systemctl stop secure-vpn")
time.sleep(2)
check("systemctl start secure-vpn")
time.sleep(3)

print("📊 Status:")
vpn_status = check("systemctl is-active secure-vpn")
print(f"VPN Service: {vpn_status}")

port = check("netstat -tulpn | grep 1194")
if port:
    print(f"✅ Port 1194 listening!\n{port[:100]}")
else:
    print("❌ Port 1194 not listening")
    print("\nErrors:")
    logs = check("journalctl -u secure-vpn -n 15 --no-pager | tail -10")
    print(logs)

print(f"\n🌐 Download server: http://{VPS_IP}:8081 ✅")

ssh.close()

