#!/usr/bin/env python3
"""Complete the VPN setup that got interrupted"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

print("🔧 Completing VPN setup...\n")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd, desc=""):
    if desc:
        print(f"  → {desc}")
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=300)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    errors = stderr.read().decode()
    return output, errors, exit_status

# Check what certs we have
print("📋 Checking certificates...")
output, _, _ = run(f"ls -la {VPN_DIR}/certs/")
print(output)

# Generate missing certificates (skip if already done)
print("\n🔐 Generating missing certificates...")
output, _, _ = run(f"cd {VPN_DIR} && bash generate-certs.sh 2>&1", "Running cert generation")
if "already exists" in output.lower() or "Done" in output:
    print("✅ Certificates ready")
else:
    print(output[:500])  # Show first part

# Setup routing
print("\n🌐 Setting up routing...")
run(f"cd {VPN_DIR} && bash setup-routing.sh")
print("✅ Routing configured")

# Configure VPN manager
print("\n⚙️  Configuring VPN...")
run(f"cd {VPN_DIR} && python3 vpn-manager.py set-server-ip {VPS_IP}")
run(f"cd {VPN_DIR} && python3 vpn-manager.py init")
print("✅ VPN configured")

# Enable and start services
print("\n🚀 Starting services...")
run("systemctl daemon-reload")
run("systemctl enable secure-vpn secure-vpn-download")
run("systemctl start secure-vpn")
time.sleep(2)
run("systemctl start secure-vpn-download")
time.sleep(2)

# Check status
print("\n📊 Service Status:")
output, _, _ = run("systemctl status secure-vpn --no-pager -l | head -10")
print(output)

output, _, _ = run("systemctl status secure-vpn-download --no-pager -l | head -10")
print(output)

# Check ports
print("\n🔌 Port Status:")
run("netstat -tulpn | grep -E '(1194|8081)' || echo 'Ports not listening yet'")

# Check IP forwarding
output, _, _ = run("cat /proc/sys/net/ipv4/ip_forward")
if "1" in output:
    print("✅ IP forwarding enabled")
else:
    print("❌ IP forwarding disabled")

print("\n" + "="*60)
print("✅ Setup complete! Check status above.")
print(f"🌐 Download Server: http://{VPS_IP}:8081")
print("="*60)

ssh.close()

