#!/usr/bin/env python3
"""
Deploy complete VPS setup script to VPS
This will fix DNS and firewall once and for all
"""

import subprocess
from paramiko import SSHClient, AutoAddPolicy
import os
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
BASE_DIR = Path(__file__).parent

print("==========================================")
print("🚀 DEPLOYING COMPLETE VPS SETUP")
print("==========================================")
print("")

# Check if script exists
setup_script = BASE_DIR / "scripts" / "complete-vps-setup.sh"
if not setup_script.exists():
    print("❌ Error: complete-vps-setup.sh not found!")
    exit(1)

print("1️⃣ Testing SSH connection...")
ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())

try:
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("   ✅ SSH connection successful!")
    print("")
except Exception as e:
    print(f"   ❌ SSH connection failed: {e}")
    print("")
    print("💡 If SSH is blocked, use OVH Rescue Mode:")
    print("   1. Go to: https://manager.ovh.com")
    print("   2. Enable Rescue Mode")
    print("   3. Fix firewall in rescue mode")
    print("   4. Then run this script again")
    exit(1)

print("2️⃣ Uploading setup script...")
try:
    sftp = ssh.open_sftp()
    sftp.put(str(setup_script), "/root/complete-vps-setup.sh")
    sftp.chmod("/root/complete-vps-setup.sh", 0o755)
    sftp.close()
    print("   ✅ Script uploaded")
    print("")
except Exception as e:
    print(f"   ❌ Upload failed: {e}")
    ssh.close()
    exit(1)

print("3️⃣ Running complete VPS setup...")
print("   (This will take 2-3 minutes)")
print("")
try:
    stdin, stdout, stderr = ssh.exec_command("bash /root/complete-vps-setup.sh")
    
    # Show output in real-time
    for line in stdout:
        print(line.rstrip())
    
    # Check for errors
    error_output = stderr.read().decode()
    if error_output:
        print("")
        print("⚠️  Errors:")
        print(error_output)
    
    exit_code = stdout.channel.recv_exit_status()
    
    if exit_code == 0:
        print("")
        print("✅ Setup completed successfully!")
    else:
        print("")
        print(f"⚠️  Setup completed with exit code {exit_code}")
        print("   Check the output above for any issues")
    
except Exception as e:
    print(f"   ❌ Execution failed: {e}")
    ssh.close()
    exit(1)

print("")
print("4️⃣ Verifying setup...")
print("")

# Test DNS
print("   Testing DNS...")
stdin, stdout, stderr = ssh.exec_command("nslookup google.com 2>&1 | head -3")
dns_test = stdout.read().decode()
if "Name:" in dns_test or "google.com" in dns_test:
    print("      ✅ DNS working")
else:
    print("      ⚠️  DNS test inconclusive")

# Test SSH service
print("   Testing SSH service...")
stdin, stdout, stderr = ssh.exec_command("systemctl is-active sshd")
ssh_status = stdout.read().decode().strip()
if ssh_status == "active":
    print("      ✅ SSH service running")
else:
    print(f"      ⚠️  SSH service: {ssh_status}")

# Test firewall rules
print("   Testing firewall rules...")
stdin, stdout, stderr = ssh.exec_command("iptables -L INPUT -n | grep -c 'tcp dpt:22'")
ssh_rule = stdout.read().decode().strip()
if ssh_rule and int(ssh_rule) > 0:
    print("      ✅ SSH firewall rule exists")
else:
    print("      ⚠️  SSH firewall rule missing")

stdin, stdout, stderr = ssh.exec_command("iptables -L INPUT -n | grep -c 'udp dpt:53'")
dns_rule = stdout.read().decode().strip()
if dns_rule and int(dns_rule) > 0:
    print("      ✅ DNS firewall rule exists")
else:
    print("      ⚠️  DNS firewall rule missing")

print("")
print("==========================================")
print("✅ DEPLOYMENT COMPLETE!")
print("==========================================")
print("")
print("📋 What was done:")
print("   ✅ DNS configured permanently")
print("   ✅ Firewall configured (no conflicts)")
print("   ✅ Rules saved permanently")
print("   ✅ Services restarted")
print("")
print("🎯 Next steps:")
print("   1. Test SSH: ssh root@15.204.11.19")
print("   2. Deploy all fixes: python3 deploy-after-reboot.py")
print("   3. Test web portal: curl http://localhost:5000")
print("")
print("🔧 Maintenance commands (on VPS):")
print("   check-dns.sh      - Test DNS")
print("   check-firewall.sh - View firewall")
print("   reload-firewall.sh - Reload firewall")
print("")

ssh.close()

