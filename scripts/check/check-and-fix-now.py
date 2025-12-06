#!/usr/bin/env python3
"""Quick status check and fix - no waiting"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)

def quick_check(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    try:
        output = stdout.read().decode()
        return output
    except:
        return ""

print("🔍 Quick Status Check:\n")

# Check dh.pem
dh_size = quick_check(f"stat -c%s {VPN_DIR}/certs/dh.pem 2>/dev/null || echo '0'")
if dh_size.strip() == "0":
    print("❌ dh.pem is EMPTY or missing!")
    print("   Starting background generation (2048-bit)...")
    ssh.exec_command(f"cd {VPN_DIR}/certs && nohup openssl dhparam -out dh.pem 2048 >/tmp/dh-gen.log 2>&1 &", timeout=5)
    print("   Running in background - will take 1-2 minutes")
else:
    print(f"✅ dh.pem exists ({int(dh_size.strip())/1024:.1f} KB)")

# Check ta.key
has_ta = quick_check(f"test -f {VPN_DIR}/certs/ta.key && echo 'YES' || echo 'NO'")
if "NO" in has_ta:
    print("❌ ta.key missing - generating...")
    quick_check(f"cd {VPN_DIR}/certs && openvpn --genkey --secret ta.key")
    print("✅ ta.key generated")
else:
    print("✅ ta.key exists")

# Check services
vpn_status = quick_check("systemctl is-active secure-vpn")
dl_status = quick_check("systemctl is-active secure-vpn-download")
print(f"\nVPN Service: {vpn_status.strip()}")
print(f"Download Service: {dl_status.strip()}")

# Check ports
port1194 = quick_check("netstat -tulpn | grep 1194")
port8081 = quick_check("netstat -tulpn | grep 8081")
print(f"\nPort 1194: {'✅ Listening' if port1194.strip() else '❌ Not listening'}")
print(f"Port 8081: {'✅ Listening' if port8081.strip() else '❌ Not listening'}")

# Check VPN logs if not running
if "active" not in vpn_status.lower():
    print("\n📋 Recent VPN errors:")
    logs = quick_check(f"journalctl -u secure-vpn -n 10 --no-pager 2>/dev/null || tail -10 {VPN_DIR}/logs/server.log 2>/dev/null")
    print(logs[:500] if logs else "No logs found")

print(f"\n🌐 Download server: http://{VPS_IP}:8081")
print("\n✅ Status check complete!")
print("\nIf dh.pem is generating, wait 1-2 min then run:")
print("  ssh root@15.204.11.19")
print("  systemctl restart secure-vpn")

ssh.close()

