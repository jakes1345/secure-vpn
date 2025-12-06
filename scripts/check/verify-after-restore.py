#!/usr/bin/env python3
"""
Verify VPS after restore - check everything is working
"""

from paramiko import SSHClient, AutoAddPolicy
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("==========================================")
print("🔍 VERIFYING VPS AFTER RESTORE")
print("==========================================")
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("✅ SSH connection working")
    print("")
    
    # Check DNS
    print("1️⃣ Checking DNS...")
    stdin, stdout, stderr = ssh.exec_command("cat /etc/resolv.conf")
    dns_output = stdout.read().decode().strip()
    print(dns_output)
    if "8.8.8.8" in dns_output or "1.1.1.1" in dns_output:
        print("   ✅ DNS configured")
    else:
        print("   ⚠️  DNS may need fixing")
    print("")
    
    # Check firewall
    print("2️⃣ Checking firewall (SSH rule)...")
    stdin, stdout, stderr = ssh.exec_command("iptables -L INPUT -n | grep 'tcp dpt:22' || echo 'SSH rule missing!'")
    fw_output = stdout.read().decode().strip()
    print(fw_output)
    if "tcp dpt:22" in fw_output:
        print("   ✅ SSH rule exists")
    else:
        print("   ❌ SSH rule missing - firewall may block SSH!")
    print("")
    
    # Check OpenVPN config
    print("3️⃣ Checking OpenVPN config...")
    stdin, stdout, stderr = ssh.exec_command("grep -E '^up|^down|^script-security' /opt/secure-vpn/config/server.conf 2>/dev/null || echo 'Config not found or scripts commented'")
    ovpn_output = stdout.read().decode().strip()
    print(ovpn_output)
    if "up scripts" in ovpn_output and not ovpn_output.startswith("#"):
        print("   ⚠️  WARNING: up/down scripts are NOT commented - will block SSH!")
    else:
        print("   ✅ up/down scripts are commented (safe)")
    print("")
    
    # Check services
    print("4️⃣ Checking services...")
    stdin, stdout, stderr = ssh.exec_command("echo 'OpenVPN:' && (pgrep -x openvpn >/dev/null && echo '✅ Running' || echo '❌ Not running') && echo 'Web Portal:' && (pgrep -f 'app.py' >/dev/null && echo '✅ Running' || echo '❌ Not running')")
    services = stdout.read().decode().strip()
    print(services)
    print("")
    
    # Check ports
    print("5️⃣ Checking listening ports...")
    stdin, stdout, stderr = ssh.exec_command("echo 'SSH (22):' && (ss -tlnp 2>/dev/null | grep -q ':22 ' && echo '✅ Listening' || echo '❌ Not listening') && echo 'OpenVPN (1194):' && (ss -ulnp 2>/dev/null | grep -q ':1194 ' && echo '✅ Listening' || echo '❌ Not listening') && echo 'Web Portal (8081):' && (ss -tlnp 2>/dev/null | grep -q ':8081 ' && echo '✅ Listening' || echo '❌ Not listening')")
    ports = stdout.read().decode().strip()
    print(ports)
    print("")
    
    print("==========================================")
    print("✅ VERIFICATION COMPLETE")
    print("==========================================")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("")
    print("If SSH is not working, you may need to:")
    print("1. Check OVH Edge Network Firewall")
    print("2. Put VPS in rescue mode")
    print("3. Run fix-ssh-in-rescue-now.txt commands")

