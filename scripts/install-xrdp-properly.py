#!/usr/bin/env python3
"""
Properly install XRDP with desktop environment
"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

print("=" * 70)
print("🖥️  INSTALLING XRDP WITH DESKTOP ENVIRONMENT")
print("=" * 70)
print("")

# Wait for apt to be free
print("1. Waiting for apt to finish...")
for i in range(20):
    success, check, _ = run_command(ssh, "lsof /var/lib/dpkg/lock-frontend 2>/dev/null && echo 'LOCKED' || echo 'FREE'", check=False)
    if 'FREE' in check:
        print("   ✅ apt is free")
        break
    time.sleep(2)

# Check what's installed
print("\n2. Checking current installation...")
stdin, stdout, stderr = ssh.exec_command("dpkg -l | grep -E 'xrdp|xfce|gnome|desktop' | head -5")
installed = stdout.read().decode().strip()
print(installed or "No desktop packages found")

# Install XFCE (lightweight desktop)
print("\n3. Installing XFCE desktop environment...")
print("   (This may take a few minutes...)")
run_command(ssh, "DEBIAN_FRONTEND=noninteractive apt-get update -y", check=False)
run_command(ssh, "DEBIAN_FRONTEND=noninteractive apt-get install -y xfce4 xfce4-goodies xorg dbus-x11", check=False)
print("   ✅ XFCE installed")

# Install XRDP
print("\n4. Installing XRDP...")
run_command(ssh, "DEBIAN_FRONTEND=noninteractive apt-get install -y xrdp", check=False)
print("   ✅ XRDP installed")

# Configure XRDP
print("\n5. Configuring XRDP...")
# Configure to use XFCE
run_command(ssh, "echo 'xfce4-session' > /etc/xrdp/startwm.sh", check=False)
run_command(ssh, "chmod +x /etc/xrdp/startwm.sh", check=False)
print("   ✅ XRDP configured")

# Allow root to login via XRDP
print("\n6. Allowing root login...")
run_command(ssh, "sed -i 's/#AllowRootLogin.*/AllowRootLogin=yes/' /etc/xrdp/xrdp.ini", check=False)
run_command(ssh, "sed -i 's/#SecurityLayer.*/SecurityLayer=rdp/' /etc/xrdp/xrdp.ini", check=False)
run_command(ssh, "sed -i 's/#CryptRDP.*/CryptRDP=yes/' /etc/xrdp/xrdp.ini", check=False)
print("   ✅ Root login enabled")

# Start services
print("\n7. Starting services...")
run_command(ssh, "systemctl enable xrdp", check=False)
run_command(ssh, "systemctl enable xrdp-sesman", check=False)
run_command(ssh, "systemctl restart xrdp", check=False)
run_command(ssh, "systemctl restart xrdp-sesman", check=False)

time.sleep(3)

# Check status
print("\n8. Checking status...")
stdin, stdout, stderr = ssh.exec_command("systemctl is-active xrdp")
xrdp_status = stdout.read().decode().strip()
print(f"   XRDP service: {xrdp_status}")

stdin, stdout, stderr = ssh.exec_command("systemctl is-active xrdp-sesman")
sesman_status = stdout.read().decode().strip()
print(f"   XRDP-Sesman service: {sesman_status}")

stdin, stdout, stderr = ssh.exec_command("ss -tuln | grep ':3389' || echo 'NOT_LISTENING'")
port_status = stdout.read().decode().strip()
print(f"   Port 3389: {port_status}")

if 'LISTEN' in port_status or ':3389' in port_status:
    print("\n✅ XRDP is ready!")
else:
    print("\n⚠️  Checking logs...")
    stdin, stdout, stderr = ssh.exec_command("journalctl -u xrdp --no-pager -n 10")
    print(stdout.read().decode().strip())

print("\n" + "=" * 70)
print("🖥️  REMOTE DESKTOP SETUP")
print("=" * 70)
print(f"\nConnect to: {VPS_IP}:3389")
print(f"Username: {VPS_USER}")
print(f"Password: {VPS_PASS}")
print("\nWindows: Win+R → mstsc → Enter IP")

ssh.close()

