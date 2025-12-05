#!/usr/bin/env python3
"""
Fix DNS and verify firewall after restore
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("==========================================")
print("🔧 FIXING DNS AND FIREWALL")
print("==========================================")
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("✅ Connected")
    print("")
    
    # Fix DNS
    print("1️⃣ Fixing DNS...")
    stdin, stdout, stderr = ssh.exec_command(
        "systemctl stop systemd-resolved 2>/dev/null; "
        "chattr -i /etc/resolv.conf 2>/dev/null; "
        "rm -f /etc/resolv.conf; "
        "echo 'nameserver 8.8.8.8' > /etc/resolv.conf; "
        "echo 'nameserver 8.8.4.4' >> /etc/resolv.conf; "
        "echo 'nameserver 1.1.1.1' >> /etc/resolv.conf; "
        "chattr +i /etc/resolv.conf 2>/dev/null; "
        "cat /etc/resolv.conf && echo '✅ DNS fixed'"
    )
    output = stdout.read().decode().strip()
    print(output)
    print("")
    
    # Check and fix firewall
    print("2️⃣ Checking firewall...")
    stdin, stdout, stderr = ssh.exec_command("iptables -L INPUT -n | grep 'tcp dpt:22' || echo 'SSH rule missing'")
    fw_check = stdout.read().decode().strip()
    print(fw_check)
    
    if "SSH rule missing" in fw_check:
        print("   Adding SSH rule to firewall...")
        stdin, stdout, stderr = ssh.exec_command(
            "iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT && "
            "iptables-save > /etc/iptables/rules.v4 2>/dev/null && "
            "echo '✅ SSH rule added'"
        )
        output = stdout.read().decode().strip()
        print(output)
    else:
        print("   ✅ SSH rule exists")
    print("")
    
    # Verify UFW status
    print("3️⃣ Checking UFW status...")
    stdin, stdout, stderr = ssh.exec_command("ufw status | head -5")
    ufw_status = stdout.read().decode().strip()
    print(ufw_status)
    if "Status: active" in ufw_status:
        print("   ✅ UFW is active (may be handling SSH)")
    print("")
    
    # Final verification
    print("4️⃣ Final verification...")
    stdin, stdout, stderr = ssh.exec_command(
        "echo 'DNS:' && cat /etc/resolv.conf | grep nameserver && "
        "echo 'SSH Rule:' && (iptables -L INPUT -n | grep -q 'tcp dpt:22' && echo '✅ Exists' || echo '❌ Missing') && "
        "echo 'SSH Port:' && (ss -tlnp 2>/dev/null | grep -q ':22 ' && echo '✅ Listening' || echo '❌ Not listening')"
    )
    verification = stdout.read().decode().strip()
    print(verification)
    print("")
    
    print("==========================================")
    print("✅ DNS AND FIREWALL FIXED")
    print("==========================================")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")

