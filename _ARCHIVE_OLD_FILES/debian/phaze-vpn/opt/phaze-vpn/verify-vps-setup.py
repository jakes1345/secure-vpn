#!/usr/bin/env python3
"""
Verify VPS setup is working correctly
Run this after complete-vps-setup.sh to make sure everything is good
"""

from paramiko import SSHClient, AutoAddPolicy
import socket

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("==========================================")
print("🔍 VERIFYING VPS SETUP")
print("==========================================")
print("")

# Test 1: SSH Connection
print("1️⃣ Testing SSH connection...")
try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("   ✅ SSH connection: WORKING")
    ssh.close()
except Exception as e:
    print(f"   ❌ SSH connection: FAILED ({e})")
    exit(1)

# Test 2: DNS Resolution
print("")
print("2️⃣ Testing DNS resolution...")
try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    stdin, stdout, stderr = ssh.exec_command("nslookup google.com 2>&1")
    dns_output = stdout.read().decode()
    
    if "Name:" in dns_output or "google.com" in dns_output:
        print("   ✅ DNS resolution: WORKING")
    else:
        print("   ❌ DNS resolution: FAILED")
        print(f"      Output: {dns_output[:200]}")
    
    ssh.close()
except Exception as e:
    print(f"   ❌ DNS test failed: {e}")

# Test 3: Firewall Rules
print("")
print("3️⃣ Testing firewall rules...")
try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    # Check SSH rule
    stdin, stdout, stderr = ssh.exec_command("iptables -L INPUT -n | grep 'tcp dpt:22' | wc -l")
    ssh_rule_count = int(stdout.read().decode().strip())
    if ssh_rule_count > 0:
        print("   ✅ SSH rule (port 22): EXISTS")
    else:
        print("   ❌ SSH rule (port 22): MISSING")
    
    # Check DNS rule
    stdin, stdout, stderr = ssh.exec_command("iptables -L INPUT -n | grep 'udp dpt:53' | wc -l")
    dns_rule_count = int(stdout.read().decode().strip())
    if dns_rule_count > 0:
        print("   ✅ DNS rule (port 53): EXISTS")
    else:
        print("   ❌ DNS rule (port 53): MISSING")
    
    # Check HTTPS rule
    stdin, stdout, stderr = ssh.exec_command("iptables -L INPUT -n | grep 'tcp dpt:443' | wc -l")
    https_rule_count = int(stdout.read().decode().strip())
    if https_rule_count > 0:
        print("   ✅ HTTPS rule (port 443): EXISTS")
    else:
        print("   ⚠️  HTTPS rule (port 443): MISSING")
    
    # Check OpenVPN rule
    stdin, stdout, stderr = ssh.exec_command("iptables -L INPUT -n | grep 'udp dpt:1194' | wc -l")
    ovpn_rule_count = int(stdout.read().decode().strip())
    if ovpn_rule_count > 0:
        print("   ✅ OpenVPN rule (port 1194): EXISTS")
    else:
        print("   ⚠️  OpenVPN rule (port 1194): MISSING")
    
    ssh.close()
except Exception as e:
    print(f"   ❌ Firewall test failed: {e}")

# Test 4: Services
print("")
print("4️⃣ Testing services...")
try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    # Check SSH service
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active sshd")
    ssh_status = stdout.read().decode().strip()
    if ssh_status == "active":
        print("   ✅ SSH service: RUNNING")
    else:
        print(f"   ❌ SSH service: {ssh_status}")
    
    # Check if UFW is disabled
    stdin, stdout, stderr = ssh.exec_command("systemctl is-enabled ufw 2>&1")
    ufw_status = stdout.read().decode().strip()
    if "disabled" in ufw_status or "not-found" in ufw_status:
        print("   ✅ UFW: DISABLED (good, no conflicts)")
    else:
        print(f"   ⚠️  UFW: {ufw_status} (might cause conflicts)")
    
    # Check systemd-resolved
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active systemd-resolved 2>&1")
    resolved_status = stdout.read().decode().strip()
    if "inactive" in resolved_status or "not-found" in resolved_status:
        print("   ✅ systemd-resolved: STOPPED (good, no conflicts)")
    else:
        print(f"   ⚠️  systemd-resolved: {resolved_status} (might override DNS)")
    
    ssh.close()
except Exception as e:
    print(f"   ❌ Services test failed: {e}")

# Test 5: HTTPS Connectivity (Mailjet API)
print("")
print("5️⃣ Testing HTTPS connectivity (Mailjet API)...")
try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    stdin, stdout, stderr = ssh.exec_command("curl -s --max-time 5 -I https://api.mailjet.com 2>&1 | head -1")
    https_test = stdout.read().decode().strip()
    
    if "200" in https_test or "301" in https_test or "302" in https_test:
        print("   ✅ HTTPS connectivity: WORKING")
    elif "timeout" in https_test.lower() or "Connection refused" in https_test:
        print("   ⚠️  HTTPS connectivity: FAILED (might be firewall)")
    else:
        print(f"   ⚠️  HTTPS connectivity: {https_test[:50]}")
    
    ssh.close()
except Exception as e:
    print(f"   ⚠️  HTTPS test failed: {e}")

# Test 6: DNS Configuration
print("")
print("6️⃣ Checking DNS configuration...")
try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    # Check resolv.conf
    stdin, stdout, stderr = ssh.exec_command("cat /etc/resolv.conf")
    resolv_conf = stdout.read().decode()
    
    if "8.8.8.8" in resolv_conf or "1.1.1.1" in resolv_conf:
        print("   ✅ /etc/resolv.conf: CONFIGURED")
        print(f"      {resolv_conf.strip()[:100]}")
    else:
        print("   ⚠️  /etc/resolv.conf: Might not be configured correctly")
    
    ssh.close()
except Exception as e:
    print(f"   ❌ DNS config check failed: {e}")

print("")
print("==========================================")
print("✅ VERIFICATION COMPLETE")
print("==========================================")
print("")
print("📋 Summary:")
print("   If all tests passed, your VPS is configured correctly!")
print("   DNS and firewall should work without conflicts.")
print("")
print("💡 If any tests failed:")
print("   1. Run: python3 deploy-complete-setup.py")
print("   2. Or manually run: /root/complete-vps-setup.sh on VPS")
print("")

