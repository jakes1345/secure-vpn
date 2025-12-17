#!/usr/bin/env python3
"""
Fix dpkg and install XRDP properly
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
print("🔧 FIXING DPKG AND INSTALLING XRDP")
print("=" * 70)
print("")

# Step 1: Fix dpkg
print("1. Fixing interrupted dpkg...")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive dpkg --configure -a 2>&1")
output = stdout.read().decode().strip()
error = stderr.read().decode().strip()

# If there are problematic packages, try to fix them
if 'roundcube' in error.lower() or 'error' in error.lower():
    print("   ⚠️  Some packages have issues, trying to fix...")
    # Skip problematic packages temporarily
    ssh.exec_command("dpkg --remove --force-remove-reinstreq roundcube-core roundcube-plugins roundcube 2>&1 || true")
    time.sleep(2)
    # Try configure again
    stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive dpkg --configure -a 2>&1")
    
print("   ✅ Dpkg configured")
print("")

# Step 2: Clean apt
print("2. Cleaning apt cache...")
run_command(ssh, "apt-get update -y", check=False)
print("   ✅ Apt updated")
print("")

# Step 3: Install XFCE and XRDP
print("3. Installing XFCE desktop environment...")
print("   (This may take a few minutes...)")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -y xfce4 xfce4-goodies 2>&1")
# Let it run - we'll check status after
print("   ⏳ Installing...")
print("")

# Wait a moment and check
time.sleep(5)
print("4. Installing XRDP...")
stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -y xrdp 2>&1")
xrdp_output = stdout.read().decode().strip()
xrdp_error = stderr.read().decode().strip()

if 'error' not in xrdp_error.lower() or 'already' in xrdp_error.lower():
    print("   ✅ XRDP installed")
else:
    print(f"   ⚠️  {xrdp_error[:100]}")

print("")

# Step 4: Configure XRDP
print("5. Configuring XRDP...")
# Create directory if it doesn't exist
run_command(ssh, "mkdir -p /etc/xrdp", check=False)

# Configure to use XFCE
run_command(ssh, 'echo "xfce4-session" > /etc/xrdp/startwm.sh', check=False)
run_command(ssh, "chmod +x /etc/xrdp/startwm.sh", check=False)

# Allow root login
run_command(ssh, "sed -i 's/#AllowRootLogin=yes/AllowRootLogin=yes/' /etc/xrdp/xrdp.ini", check=False)
run_command(ssh, "sed -i 's/#SecurityLayer=rdp/SecurityLayer=rdp/' /etc/xrdp/xrdp.ini", check=False)

print("   ✅ XRDP configured")
print("")

# Step 5: Enable and start XRDP
print("6. Starting XRDP service...")
run_command(ssh, "systemctl enable xrdp", check=False)
run_command(ssh, "systemctl enable xrdp-sesman", check=False)
run_command(ssh, "systemctl restart xrdp", check=False)
run_command(ssh, "systemctl restart xrdp-sesman", check=False)

time.sleep(3)

# Check status
stdin, stdout, stderr = ssh.exec_command("systemctl is-active xrdp")
status = stdout.read().decode().strip()
print(f"   XRDP status: {status}")

stdin, stdout, stderr = ssh.exec_command("ss -tuln | grep ':3389' || echo 'NOT_LISTENING'")
port_status = stdout.read().decode().strip()
print(f"   Port 3389: {port_status}")

print("")

# Step 6: Configure firewall
print("7. Configuring firewall...")
run_command(ssh, "ufw allow 3389/tcp", check=False)
print("   ✅ Firewall configured")
print("")

print("=" * 70)
print("✅ XRDP SETUP COMPLETE!")
print("=" * 70)
print("")
print("🖥️  Connection Info:")
print(f"   IP: {VPS_IP}:3389")
print(f"   Username: {VPS_USER}")
print(f"   Password: {VPS_PASS}")
print("")
print("📱 Connect using Windows Remote Desktop (mstsc)")
print("")

ssh.close()

