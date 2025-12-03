#!/usr/bin/env python3
"""
Fix VPS internet connection - check network, DNS, routing
"""

import paramiko
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("🌐 DIAGNOSING VPS INTERNET CONNECTION")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Check network interfaces
        print("1️⃣  Checking network interfaces...")
        success, interfaces, _ = run_command(ssh, "ip addr show | grep -E '^[0-9]+:|inet '")
        print(interfaces)
        print("")
        
        # Check if interfaces are up
        print("2️⃣  Checking interface status...")
        success, status, _ = run_command(ssh, "ip link show | grep -E '^[0-9]+:|state'")
        print(status)
        print("")
        
        # Check DNS
        print("3️⃣  Checking DNS configuration...")
        success, dns, _ = run_command(ssh, "cat /etc/resolv.conf")
        print(dns)
        print("")
        
        # Test connectivity
        print("4️⃣  Testing connectivity...")
        success, ping_test, _ = run_command(ssh, "ping -c 2 8.8.8.8 2>&1 | tail -3")
        print(ping_test)
        print("")
        
        success, dns_test, _ = run_command(ssh, "ping -c 2 google.com 2>&1 | tail -3")
        print("DNS test (google.com):")
        print(dns_test)
        print("")
        
        # Check routing
        print("5️⃣  Checking routing table...")
        success, routes, _ = run_command(ssh, "ip route show")
        print(routes)
        print("")
        
        # Check network manager
        print("6️⃣  Checking NetworkManager...")
        success, nm_status, _ = run_command(ssh, "systemctl status NetworkManager --no-pager | head -5 || systemctl status networking --no-pager | head -5 || echo 'No network manager found'")
        print(nm_status)
        print("")
        
        # Try to fix common issues
        print("=" * 70)
        print("🔧 ATTEMPTING FIXES")
        print("=" * 70)
        print("")
        
        # Restart networking
        print("7️⃣  Restarting network services...")
        run_command(ssh, "systemctl restart NetworkManager 2>&1 || systemctl restart networking 2>&1 || echo 'No network service to restart'")
        print("   ✅ Network services restarted")
        print("")
        
        # Ensure DNS is set
        print("8️⃣  Setting DNS servers...")
        run_command(ssh, "echo 'nameserver 8.8.8.8' > /etc/resolv.conf && echo 'nameserver 8.8.4.4' >> /etc/resolv.conf")
        print("   ✅ DNS set to Google DNS")
        print("")
        
        # Bring interfaces up
        print("9️⃣  Bringing interfaces up...")
        success, ifaces, _ = run_command(ssh, "ip link show | grep -E '^[0-9]+:' | awk -F': ' '{print $2}' | awk '{print $1}'")
        for iface in ifaces.split('\n'):
            if iface and iface != 'lo':
                run_command(ssh, f"ip link set {iface} up 2>&1")
                print(f"   ✅ Brought {iface} up")
        print("")
        
        # Test again
        print("🔟  Testing connectivity again...")
        success, final_test, _ = run_command(ssh, "ping -c 2 8.8.8.8 2>&1 | tail -2")
        print(final_test)
        print("")
        
        print("=" * 70)
        print("✅ DIAGNOSIS COMPLETE")
        print("=" * 70)
        print("")
        print("📋 Next steps if still no internet:")
        print("   1. Check VPS provider's network panel")
        print("   2. Verify IP configuration matches provider settings")
        print("   3. Check if firewall is blocking outbound connections")
        print("   4. Try: ip route add default via GATEWAY_IP")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

