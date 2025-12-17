#!/usr/bin/env python3
"""
Final comprehensive status check
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 60)
print("🔍 FINAL VPS STATUS CHECK")
print("=" * 60)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("✅ SSH Connection: WORKING")
    print("")
    
    # 1. DNS Check
    print("1️⃣ DNS Configuration:")
    stdin, stdout, stderr = ssh.exec_command("cat /etc/resolv.conf | grep -v '^#' | grep nameserver")
    dns = stdout.read().decode().strip()
    if "8.8.8.8" in dns or "1.1.1.1" in dns:
        print(f"   ✅ {dns}")
    else:
        print(f"   ⚠️  {dns}")
    print("")
    
    # 2. Firewall Check
    print("2️⃣ Firewall Status:")
    stdin, stdout, stderr = ssh.exec_command("echo 'UFW:' && ufw status | head -3 && echo '' && echo 'iptables SSH rule:' && (iptables -L INPUT -n | grep 'tcp dpt:22' && echo '✅ SSH allowed' || echo '❌ SSH rule missing')")
    fw = stdout.read().decode().strip()
    print(f"   {fw}")
    print("")
    
    # 3. OpenVPN Config Check
    print("3️⃣ OpenVPN Configuration:")
    stdin, stdout, stderr = ssh.exec_command("grep -E '^#.*up|^#.*down|^up|^down' /opt/secure-vpn/config/server.conf | head -3")
    ovpn_config = stdout.read().decode().strip()
    if "up scripts" in ovpn_config and ovpn_config.startswith("#"):
        print("   ✅ up/down scripts are COMMENTED (safe - won't block SSH)")
    elif "up scripts" in ovpn_config:
        print("   ❌ WARNING: up/down scripts are ACTIVE (will block SSH!)")
    else:
        print("   ✅ No up/down scripts found")
    print("")
    
    # 4. Services Status
    print("4️⃣ Services Status:")
    stdin, stdout, stderr = ssh.exec_command(
        "echo 'OpenVPN:' && (pgrep -x openvpn >/dev/null && echo '   ✅ Running (PID: '$(pgrep -x openvpn)')' || echo '   ❌ Not running') && "
        "echo 'Web Portal:' && (pgrep -f 'app.py' >/dev/null && echo '   ✅ Running (PID: '$(pgrep -f 'app.py')')' || echo '   ❌ Not running')"
    )
    services = stdout.read().decode().strip()
    print(services)
    print("")
    
    # 5. Ports Listening
    print("5️⃣ Listening Ports:")
    stdin, stdout, stderr = ssh.exec_command(
        "echo 'SSH (22):' && (ss -tlnp 2>/dev/null | grep -q ':22 ' && echo '   ✅ Listening' || echo '   ❌ Not listening') && "
        "echo 'OpenVPN (1194):' && (ss -ulnp 2>/dev/null | grep -q ':1194 ' && echo '   ✅ Listening' || echo '   ❌ Not listening') && "
        "echo 'Web Portal (8081):' && (ss -tlnp 2>/dev/null | grep -q ':8081 ' && echo '   ✅ Listening' || echo '   ❌ Not listening')"
    )
    ports = stdout.read().decode().strip()
    print(ports)
    print("")
    
    # 6. Recent Logs
    print("6️⃣ Recent OpenVPN Logs (last 5 lines):")
    stdin, stdout, stderr = ssh.exec_command("tail -5 /opt/secure-vpn/logs/server.log 2>/dev/null || echo 'No logs found'")
    logs = stdout.read().decode().strip()
    print(f"   {logs}")
    print("")
    
    # Summary
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    # Check if everything is good
    stdin, stdout, stderr = ssh.exec_command(
        "CHECK=0; "
        "pgrep -x openvpn >/dev/null && CHECK=$((CHECK+1)); "
        "pgrep -f 'app.py' >/dev/null && CHECK=$((CHECK+1)); "
        "ss -tlnp 2>/dev/null | grep -q ':22 ' && CHECK=$((CHECK+1)); "
        "ss -ulnp 2>/dev/null | grep -q ':1194 ' && CHECK=$((CHECK+1)); "
        "grep -q '^#.*up scripts' /opt/secure-vpn/config/server.conf && CHECK=$((CHECK+1)); "
        "echo $CHECK"
    )
    check_count = int(stdout.read().decode().strip())
    
    if check_count >= 5:
        print("✅ ALL SYSTEMS OPERATIONAL")
        print("")
        print("Everything is working correctly:")
        print("  ✅ SSH is accessible")
        print("  ✅ OpenVPN is running")
        print("  ✅ Web portal is running")
        print("  ✅ All ports are listening")
        print("  ✅ Server config is safe (won't block SSH)")
    elif check_count >= 3:
        print("⚠️  MOSTLY WORKING")
        print("")
        print("Some services may need attention")
    else:
        print("❌ ISSUES DETECTED")
        print("")
        print("Some services are not running properly")
    
    print("")
    print("=" * 60)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error connecting: {e}")
    print("")
    print("If SSH is not working, check:")
    print("  1. OVH Edge Network Firewall")
    print("  2. VPS firewall rules")
    print("  3. VPS boot mode (should be normal, not rescue)")
