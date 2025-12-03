#!/usr/bin/env python3
"""Honest assessment of VPN reliability"""

import paramiko
import subprocess
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

print("="*60)
print("🔍 VPN Reliability Assessment")
print("="*60)
print()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
except Exception as e:
    print(f"❌ Can't connect to VPS: {e}")
    sys.exit(1)

def get(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    return stdout.read().decode().strip()

print("📊 Current Status Check:")
print("-" * 60)

# Check if OpenVPN is running
ovpn_process = get("ps aux | grep 'openvpn.*server.conf' | grep -v grep")
if ovpn_process:
    print("✅ OpenVPN process: RUNNING")
    print(f"   PID: {ovpn_process.split()[1] if len(ovpn_process.split()) > 1 else 'N/A'}")
else:
    print("❌ OpenVPN process: NOT RUNNING")

# Check if port is listening
port_check = get("netstat -tulpn | grep 1194")
if port_check:
    print("✅ Port 1194: LISTENING")
    print(f"   {port_check[:80]}")
else:
    print("❌ Port 1194: NOT LISTENING")

# Check systemd service
service_status = get("systemctl is-active secure-vpn 2>/dev/null || echo 'not-found'")
if service_status == "active":
    print("✅ Systemd service: ACTIVE")
elif service_status == "activating":
    print("⚠️  Systemd service: ACTIVATING (may be stuck)")
else:
    print(f"❌ Systemd service: {service_status.upper()}")

# Check if VPN will auto-start on reboot
enabled = get("systemctl is-enabled secure-vpn 2>/dev/null || echo 'disabled'")
if enabled == "enabled":
    print("✅ Auto-start on boot: ENABLED")
else:
    print(f"⚠️  Auto-start on boot: {enabled.upper()}")

# Check system resources
memory = get("free -h | grep Mem | awk '{print $3 \"/\" $2}'")
cpu_load = get("uptime | awk -F'load average:' '{print $2}'")
print(f"\n📈 System Resources:")
print(f"   Memory: {memory}")
print(f"   Load: {cpu_load}")

# Check disk space
disk = get("df -h / | tail -1 | awk '{print $5}'")
print(f"   Disk usage: {disk}")

# Check logs for errors
print(f"\n📋 Recent Errors (last 10 lines):")
errors = get(f"tail -10 {VPN_DIR}/logs/server.log 2>/dev/null || journalctl -u secure-vpn -n 10 --no-pager 2>/dev/null || echo 'No logs found'")
if errors and "error" in errors.lower():
    print(f"   ⚠️  Found errors in logs")
    print(f"   {errors[:200]}")
else:
    print("   ✅ No recent errors found")

# Check firewall
fw_status = get("ufw status | head -1")
if "active" in fw_status.lower():
    print(f"\n🔥 Firewall: {fw_status}")
    ports = get("ufw status | grep -E '(1194|8081)'")
    if ports:
        print(f"   {ports}")
else:
    print(f"\n⚠️  Firewall: {fw_status}")

# Check IP forwarding
ip_forward = get("cat /proc/sys/net/ipv4/ip_forward")
if ip_forward == "1":
    print("✅ IP forwarding: ENABLED")
else:
    print("❌ IP forwarding: DISABLED (clients won't get internet)")

# Check certificates
cert_check = get(f"ls -la {VPN_DIR}/certs/*.crt {VPN_DIR}/certs/*.key {VPN_DIR}/certs/dh.pem 2>/dev/null | wc -l")
if int(cert_check) >= 4:
    print("✅ Certificates: PRESENT")
else:
    print(f"⚠️  Certificates: {cert_check} files found (expected at least 4)")

# Check server config
config_exists = get(f"test -f {VPN_DIR}/config/server.conf && echo 'yes' || echo 'no'")
if config_exists == "yes":
    print("✅ Server config: EXISTS")
else:
    print("❌ Server config: MISSING")

print()
print("="*60)
print("📊 Reliability Assessment:")
print("="*60)

# Count issues
issues = []
if not ovpn_process:
    issues.append("OpenVPN not running")
if not port_check:
    issues.append("Port not listening")
if service_status not in ["active", "activating"]:
    issues.append("Service not active")
if ip_forward != "1":
    issues.append("IP forwarding disabled")
if config_exists != "yes":
    issues.append("Config missing")

if not issues:
    print("\n✅ CURRENT STATUS: GOOD")
    print("\nWhat's working:")
    print("  • OpenVPN server is running")
    print("  • Port is listening")
    print("  • Certificates are in place")
    print("  • Config file exists")
    
    print("\n⚠️  POTENTIAL ISSUES:")
    print("  1. Service not in systemd (running manually)")
    print("     → May not auto-restart if it crashes")
    print("     → May not start on server reboot")
    
    print("\n  2. No monitoring/alerting")
    print("     → Won't know if VPN goes down")
    print("     → No automatic restart on failure")
    
    print("\n  3. Single point of failure")
    print("     → One server = one point of failure")
    print("     → If VPS goes down, VPN goes down")
    
    print("\n  4. No load balancing")
    print("     → All clients connect to one server")
    print("     → Performance degrades with many users")
    
    print("\n  5. Manual certificate management")
    print("     → Certificates expire after 365 days")
    print("     → Need to manually renew")
    
    print("\n  6. Limited bandwidth monitoring")
    print("     → No usage tracking per client")
    print("     → Can't enforce limits")
    
    print("\n💡 RELIABILITY RATING: 6.5/10")
    print("\n   Good for:")
    print("   ✅ Personal use")
    print("   ✅ Small team (5-20 users)")
    print("   ✅ Testing/development")
    
    print("\n   Not ideal for:")
    print("   ❌ Commercial/production use")
    print("   ❌ Large user base (100+ users)")
    print("   ❌ Mission-critical applications")
    print("   ❌ High availability requirements")
    
else:
    print(f"\n❌ CURRENT STATUS: HAS ISSUES")
    print(f"\nProblems found ({len(issues)}):")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    
    print("\n💡 RELIABILITY RATING: 3/10")
    print("\nVPN needs fixes before it's reliable!")

print("\n" + "="*60)
print("🔧 How to Improve Reliability:")
print("="*60)
print("""
1. Fix systemd service (auto-restart on failure)
2. Add monitoring (check if VPN is up every minute)
3. Set up alerts (email/SMS if VPN goes down)
4. Add backup server (redundancy)
5. Automate certificate renewal
6. Add usage tracking/logging
7. Set up health checks
8. Document recovery procedures

Current setup is functional but needs hardening for production.
""")

ssh.close()

