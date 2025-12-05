#!/usr/bin/env python3
"""Fix the empty dh.pem and get VPN running"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

print("🔧 Fixing dh.pem and starting VPN...\n")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd, timeout=180):
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    errors = stderr.read().decode()
    return output, errors, exit_status

# Check dh.pem size
print("📋 Checking dh.pem...")
output, _, _ = run(f"ls -lh {VPN_DIR}/certs/dh.pem")
print(output)

# Check if it's empty
output, _, _ = run(f"test -s {VPN_DIR}/certs/dh.pem && echo 'HAS_SIZE' || echo 'EMPTY'")
if "EMPTY" in output:
    print("\n❌ dh.pem is empty! Generating new one (2048-bit, fast)...")
    print("   This will take 1-2 minutes...")
    
    # Generate 2048-bit DH (faster than 4096)
    output, errors, status = run(f"cd {VPN_DIR}/certs && openssl dhparam -out dh.pem 2048", timeout=300)
    
    if status == 0:
        # Check it worked
        output, _, _ = run(f"ls -lh {VPN_DIR}/certs/dh.pem")
        print(f"✅ dh.pem generated!\n{output}")
    else:
        print(f"❌ Failed: {errors}")
else:
    print("✅ dh.pem exists\n")

# Check if ta.key exists
output, _, _ = run(f"test -f {VPN_DIR}/certs/ta.key && echo 'EXISTS' || echo 'MISSING'")
if "MISSING" in output:
    print("🔐 Generating TLS auth key...")
    run(f"cd {VPN_DIR}/certs && openvpn --genkey --secret ta.key")
    print("✅ ta.key generated\n")

# Stop VPN service first
print("🛑 Stopping VPN service...")
run("systemctl stop secure-vpn")
time.sleep(2)

# Check VPN config
print("📝 Checking VPN config...")
output, _, _ = run(f"cat {VPN_DIR}/config/server.conf | grep -E '(dh|server\.crt|ca\.crt)' | head -5")
print(output if output.strip() else "Config file may need fixing")

# Start VPN service
print("\n🚀 Starting VPN service...")
run("systemctl start secure-vpn")
time.sleep(5)

# Check status
print("\n📊 Service Status:")
output, _, _ = run("systemctl status secure-vpn --no-pager -l | head -15")
print(output)

# Check if port is listening
output, _, _ = run("netstat -tulpn | grep 1194")
if output.strip():
    print(f"✅ Port 1194 is listening!\n{output}")
else:
    print("❌ Port 1194 not listening")
    print("\nChecking logs...")
    output, _, _ = run(f"tail -20 {VPN_DIR}/logs/server.log 2>/dev/null || journalctl -u secure-vpn -n 20 --no-pager")
    print(output)

print(f"\n🌐 Download server: http://{VPS_IP}:8081")
print("✅ Setup check complete!")

ssh.close()

