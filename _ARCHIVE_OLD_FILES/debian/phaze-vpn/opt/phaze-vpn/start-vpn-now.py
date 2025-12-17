#!/usr/bin/env python3
"""Start OpenVPN now and keep it running"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    exit_status = stdout.channel.recv_exit_status()
    return stdout.read().decode(), stderr.read().decode(), exit_status

def get(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    return stdout.read().decode()

print("🚀 Starting OpenVPN now...\n")

# Kill any existing OpenVPN
print("🛑 Stopping any existing OpenVPN...")
run("pkill -9 openvpn || true")
run("systemctl stop secure-vpn || true")

# Start OpenVPN directly
print("▶️  Starting OpenVPN...")
output, errors, status = run(f"cd {VPN_DIR} && openvpn --config config/server.conf --daemon --log logs/server.log")
print(f"Exit status: {status}")

import time
time.sleep(3)

# Check if it's running
port = get("netstat -tulpn | grep 1194")
proc = get("ps aux | grep openvpn | grep -v grep")

if port.strip():
    print(f"\n✅ SUCCESS! OpenVPN is running!")
    print(f"Port 1194 listening:\n{port}")
    print(f"\nProcess:\n{proc[:200]}")
    
    print(f"\n" + "="*60)
    print("✅ VPN SERVER IS RUNNING!")
    print(f"🌐 Server IP: {VPS_IP}")
    print(f"🌐 VPN Port: 1194/udp")
    print(f"🌐 Download Server: http://{VPS_IP}:8081")
    print("="*60)
    print("\n📝 Next steps:")
    print(f"   1. SSH to VPS: ssh {VPS_USER}@{VPS_IP}")
    print(f"   2. Create client: cd {VPN_DIR} && python3 vpn-manager.py add-client test-client")
    print(f"   3. Download config: http://{VPS_IP}:8081/download?name=test-client")
else:
    print("\n❌ OpenVPN didn't start")
    logs = get(f"tail -15 {VPN_DIR}/logs/server.log")
    print(f"Logs:\n{logs}")

ssh.close()

