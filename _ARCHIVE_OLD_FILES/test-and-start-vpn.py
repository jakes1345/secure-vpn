#!/usr/bin/env python3
"""Test OpenVPN config and start it properly"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)

def get(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    return stdout.read().decode()

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    errors = stderr.read().decode()
    return output, errors, exit_status

print("🔍 Testing OpenVPN config...\n")

# Stop everything first
print("🛑 Stopping services...")
run("systemctl stop secure-vpn")
time.sleep(2)

# Kill any stuck OpenVPN processes
run("pkill -9 openvpn || true")
time.sleep(1)

# Test the config
print("\n🧪 Testing config syntax...")
output, errors, status = run(f"cd {VPN_DIR} && openvpn --config config/server.conf --verb 1 --test-crypto 2>&1")
if status == 0:
    print("✅ Config syntax OK")
else:
    print(f"❌ Config error:\n{errors[:500]}")
    print(f"\n{output[:500]}")

# Try starting OpenVPN directly (not via systemd)
print("\n🚀 Starting OpenVPN directly to test...")
run(f"cd {VPN_DIR} && openvpn --config config/server.conf --daemon --log logs/server.log")
time.sleep(3)

# Check if it's running
port = get("netstat -tulpn | grep 1194")
if port.strip():
    print(f"✅ OpenVPN is running! Port 1194 listening\n{port}")
    
    # Stop the direct instance and use systemd instead
    print("\n🔄 Stopping direct instance, enabling systemd service...")
    run("pkill openvpn")
    time.sleep(1)
    
    # Fix the systemd service to just run openvpn directly
    print("📝 Updating systemd service...")
    service_content = f"""[Unit]
Description=SecureVPN Server
After=network.target

[Service]
Type=forking
ExecStart=/usr/sbin/openvpn --config {VPN_DIR}/config/server.conf --daemon --log {VPN_DIR}/logs/server.log
PIDFile=/var/run/openvpn/server.pid
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target"""

    sftp = ssh.open_sftp()
    file = sftp.file("/etc/systemd/system/secure-vpn.service", "w")
    file.write(service_content)
    file.close()
    sftp.close()
    
    run("systemctl daemon-reload")
    run("systemctl enable secure-vpn")
    run("systemctl start secure-vpn")
    time.sleep(3)
    
    status = get("systemctl is-active secure-vpn")
    print(f"\n✅ Systemd service status: {status.strip()}")
    
else:
    print("❌ OpenVPN didn't start, checking logs...")
    logs = get(f"tail -20 {VPN_DIR}/logs/server.log")
    print(logs[:500])

port_final = get("netstat -tulpn | grep 1194")
if port_final.strip():
    print(f"\n✅ SUCCESS! Port 1194 is listening!\n{port_final}")
    print(f"\n🌐 VPN is running!")
    print(f"🌐 Download server: http://{VPS_IP}:8081")
else:
    print("\n❌ VPN still not running")

ssh.close()

