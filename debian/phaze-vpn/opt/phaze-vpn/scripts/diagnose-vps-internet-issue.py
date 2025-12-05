#!/usr/bin/env python3
"""
Diagnose why VPS has no internet access
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
        
        # Test basic connectivity
        print("1️⃣  Testing basic internet connectivity...")
        success, ping_result, _ = run_command(ssh, "ping -c 2 8.8.8.8 2>&1 | tail -3")
        print(ping_result)
        
        if '0% packet loss' in ping_result or '2 received' in ping_result:
            print("   ✅ Can reach Google DNS (8.8.8.8) - Internet works!")
        else:
            print("   ❌ Cannot reach Google DNS - No internet!")
        
        print("")
        
        # Check DNS
        print("2️⃣  Testing DNS resolution...")
        success, dns_test, _ = run_command(ssh, "nslookup google.com 8.8.8.8 2>&1 | head -5")
        print(dns_test)
        
        if 'Address:' in dns_test:
            print("   ✅ DNS is working!")
        else:
            print("   ❌ DNS not working!")
        
        print("")
        
        # Check DNS config
        print("3️⃣  Checking DNS configuration...")
        success, dns_config, _ = run_command(ssh, "cat /etc/resolv.conf")
        print(dns_config)
        print("")
        
        # Check network interfaces
        print("4️⃣  Checking network interfaces...")
        success, interfaces, _ = run_command(ssh, "ip addr show | grep -E '^[0-9]+:|inet ' | head -10")
        print(interfaces)
        print("")
        
        # Check routing
        print("5️⃣  Checking routing table...")
        success, routes, _ = run_command(ssh, "ip route show")
        print(routes)
        print("")
        
        # Check if services are blocking
        print("6️⃣  Checking if VPN/email services are blocking...")
        success, services, _ = run_command(ssh, "ss -tuln | grep -E ':(1194|443|8081|587|25|80)' | head -10")
        print("Services listening:")
        print(services or "None found")
        print("")
        
        # Check firewall
        print("7️⃣  Checking firewall rules...")
        success, firewall, _ = run_command(ssh, "ufw status verbose 2>&1 | head -10 || iptables -L OUTPUT -n | head -10")
        print(firewall)
        print("")
        
        # Test HTTP connection
        print("8️⃣  Testing HTTP connection...")
        success, http_test, _ = run_command(ssh, "curl -s -o /dev/null -w '%{http_code}' http://google.com --max-time 5 2>&1 || echo 'FAILED'")
        print(f"HTTP test result: {http_test}")
        
        if http_test and http_test.isdigit():
            print("   ✅ HTTP connections work!")
        else:
            print("   ❌ HTTP connections blocked or DNS not working")
        
        print("")
        
        print("=" * 70)
        print("🔧 FIXING COMMON ISSUES")
        print("=" * 70)
        print("")
        
        # Fix DNS
        print("Fixing DNS configuration...")
        ssh.exec_command("echo 'nameserver 8.8.8.8' > /etc/resolv.conf")
        ssh.exec_command("echo 'nameserver 8.8.4.4' >> /etc/resolv.conf")
        print("   ✅ DNS set to Google DNS")
        
        # Ensure default route exists
        success, default_route, _ = run_command(ssh, "ip route | grep default")
        if not default_route:
            print("   ⚠️  No default route found - this could be the problem!")
            # Get gateway from interface
            success, gateway_info, _ = run_command(ssh, "ip route | grep '15.204.10.1' || ip addr show ens3 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1")
            if gateway_info:
                print(f"   Found gateway info: {gateway_info}")
        
        # Restart network services
        print("\nRestarting network services...")
        run_command(ssh, "systemctl restart NetworkManager 2>&1 || systemctl restart networking 2>&1 || echo 'No network service'")
        
        # Test again
        print("\nTesting connectivity after fixes...")
        success, final_test, _ = run_command(ssh, "ping -c 1 8.8.8.8 2>&1 | tail -1")
        print(final_test)
        
        success, final_dns, _ = run_command(ssh, "nslookup google.com 8.8.8.8 2>&1 | grep 'Address:' | head -1")
        print(f"DNS test: {final_dns}")
        
        print("")
        print("=" * 70)
        print("✅ DIAGNOSIS COMPLETE")
        print("=" * 70)
        print("")
        print("Note: The VPN, email, and web services running on the VPS")
        print("should NOT block internet access. If there's no internet,")
        print("it's likely a network configuration issue, not the services.")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

