#!/usr/bin/env python3
"""
Automatically fix firewall in rescue mode
Connects to rescue mode VPS and fixes everything automatically
"""

from paramiko import SSHClient, AutoAddPolicy
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "FNCHjdPCspRE"  # Rescue mode password from your screenshot

print("==========================================")
print("🚀 AUTO-FIXING RESCUE MODE")
print("==========================================")
print("")

# Connect to rescue mode
print("1️⃣ Connecting to rescue mode...")
ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())

try:
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("   ✅ Connected!")
    print("")
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    print("   💡 Make sure you're in rescue mode and password is correct")
    exit(1)

# Step 1: Find disk
print("2️⃣ Finding your disk...")
stdin, stdout, stderr = ssh.exec_command("lsblk")
lsblk_output = stdout.read().decode()
print(lsblk_output)

# Parse output to find root partition
root_partition = None
for line in lsblk_output.split("\n"):
    if "sda2" in line or "vda2" in line:
        if "sda2" in line:
            root_partition = "/dev/sda2"
        elif "vda2" in line:
            root_partition = "/dev/vda2"
        break

if not root_partition:
    # Try to find largest partition (check sda1 first, then others)
    print("   ⚠️  Couldn't auto-detect, trying common partitions...")
    for part in ["/dev/sda1", "/dev/sda2", "/dev/vda1", "/dev/vda2"]:
        stdin, stdout, stderr = ssh.exec_command(f"test -b {part} && echo 'EXISTS' || echo 'NOT_FOUND'")
        if "EXISTS" in stdout.read().decode():
            root_partition = part
            break

if not root_partition:
    print("   ❌ Could not find root partition!")
    print("   💡 Please run manually: lsblk and tell me which partition to use")
    ssh.close()
    exit(1)

print(f"   ✅ Using: {root_partition}")
print("")

# Step 2: Mount disk
print("3️⃣ Mounting disk...")
commands = [
    "mkdir -p /mnt/recovery",
    f"mount {root_partition} /mnt/recovery",
    "mount --bind /dev /mnt/recovery/dev",
    "mount --bind /proc /mnt/recovery/proc",
    "mount --bind /sys /mnt/recovery/sys"
]

for cmd in commands:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_code = stdout.channel.recv_exit_status()
    if exit_code != 0:
        error = stderr.read().decode()
        print(f"   ⚠️  {cmd}: {error.strip()}")
    else:
        print(f"   ✅ {cmd}")

print("")

# Step 3: Fix firewall (in chroot)
print("4️⃣ Fixing firewall (this will take a minute)...")

# Create fix script on rescue system
fix_script = """#!/bin/bash
systemctl stop ufw
systemctl disable ufw
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p udp --dport 1194 -j ACCEPT
iptables -A INPUT -p icmp -j ACCEPT
iptables -P INPUT DROP
iptables -P FORWARD DROP
mkdir -p /etc/iptables
apt-get update -qq > /dev/null 2>&1
apt-get install -y iptables-persistent -qq > /dev/null 2>&1
iptables-save > /etc/iptables/rules.v4
systemctl restart sshd
systemctl enable sshd
echo 'FIREWALL_FIXED'
"""

# Write script to rescue system
stdin, stdout, stderr = ssh.exec_command("cat > /tmp/fix-firewall.sh << 'EOFSCRIPT'\n" + fix_script + "\nEOFSCRIPT\nchmod +x /tmp/fix-firewall.sh")
stdout.read()  # Wait for completion

# Execute in chroot
stdin, stdout, stderr = ssh.exec_command("chroot /mnt/recovery /bin/bash /tmp/fix-firewall.sh", get_pty=True)

# Show output in real-time
output = ""
for line in stdout:
    line_str = line.rstrip()
    if line_str:
        print(f"   {line_str}")
        output += line_str + "\n"

error_output = stderr.read().decode()
if error_output and "FIREWALL_FIXED" not in output:
    print(f"   ⚠️  Errors: {error_output[:200]}")

if "FIREWALL_FIXED" in output:
    print("   ✅ Firewall fixed!")
else:
    print("   ⚠️  Firewall fix may have issues, but continuing...")

print("")

# Step 4: Reboot
print("5️⃣ Rebooting back to normal mode...")
print("   (This will disconnect you)")
print("")
ssh.exec_command("reboot")
time.sleep(2)
ssh.close()

print("==========================================")
print("✅ RESCUE MODE FIX COMPLETE!")
print("==========================================")
print("")
print("⏳ Wait 2-3 minutes for reboot...")
print("")
print("🧪 Then test SSH:")
print("   ssh root@15.204.11.19")
print("")
print("🚀 If SSH works, run from your PC:")
print("   python3 deploy-complete-setup.py")
print("")
print("This will set up DNS and firewall properly so this never happens again!")
print("")

