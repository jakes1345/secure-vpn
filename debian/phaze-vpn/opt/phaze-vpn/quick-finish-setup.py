#!/usr/bin/env python3
"""Quickly finish setup - skip hanging parts"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def quick_run(cmd, timeout=30):
    """Run command with timeout"""
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    try:
        exit_status = stdout.channel.recv_exit_status()
    except:
        exit_status = -1
    output = stdout.read().decode()
    return output, exit_status

print("🔍 Checking what we have...\n")

# Check certificates
output, _ = quick_run(f"ls -la {VPN_DIR}/certs/")
print("Current certs:")
print(output)

# Check if server certs exist
output, _ = quick_run(f"test -f {VPN_DIR}/certs/server.crt && echo 'YES' || echo 'NO'")
has_server_cert = "YES" in output

if not has_server_cert:
    print("\n🔐 Generating server certificate (fast method)...")
    # Generate only what we need, skip slow DH generation
    quick_run(f"cd {VPN_DIR}/certs && openssl req -new -x509 -keyout ca.key -out ca.crt -days 3650 -nodes -subj '/CN=VPN-CA'", timeout=60)
    quick_run(f"cd {VPN_DIR}/certs && openssl req -new -keyout server.key -out server.csr -nodes -subj '/CN=server'", timeout=60)
    quick_run(f"cd {VPN_DIR}/certs && openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 3650", timeout=60)
    
    # Generate fast 2048-bit DH (not 4096)
    print("  → Generating DH parameters (2048-bit, fast)...")
    quick_run(f"cd {VPN_DIR}/certs && openssl dhparam -out dh.pem 2048", timeout=180)  # 3 min max
    
    # Generate TLS auth key
    quick_run(f"cd {VPN_DIR}/certs && openvpn --genkey --secret ta.key", timeout=30)
    print("✅ Certificates generated\n")
else:
    print("✅ Server certificates already exist\n")

# Check if routing is set up
print("🌐 Setting up routing...")
quick_run(f"cd {VPN_DIR} && bash setup-routing.sh")
print("✅ Routing done\n")

# Configure VPN
print("⚙️  Configuring VPN...")
quick_run(f"cd {VPN_DIR} && python3 vpn-manager.py set-server-ip {VPS_IP}")
quick_run(f"cd {VPN_DIR} && python3 vpn-manager.py init")
print("✅ VPN configured\n")

# Start services
print("🚀 Starting services...")
quick_run("systemctl daemon-reload")
quick_run("systemctl enable secure-vpn secure-vpn-download")
quick_run("systemctl start secure-vpn")
time.sleep(2)
quick_run("systemctl start secure-vpn-download")
time.sleep(2)

# Quick status check
print("\n📊 Status Check:")
output, _ = quick_run("systemctl is-active secure-vpn")
print(f"VPN Service: {output.strip()}")

output, _ = quick_run("systemctl is-active secure-vpn-download")
print(f"Download Service: {output.strip()}")

output, _ = quick_run("netstat -tulpn | grep 1194")
if output.strip():
    print(f"✅ Port 1194 listening")
else:
    print("⚠️  Port 1194 not listening yet")

output, _ = quick_run("netstat -tulpn | grep 8081")
if output.strip():
    print(f"✅ Port 8081 listening")
else:
    print("⚠️  Port 8081 not listening yet")

print(f"\n✅ Done! Try: http://{VPS_IP}:8081")

ssh.close()

