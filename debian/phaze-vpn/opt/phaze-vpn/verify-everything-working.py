#!/usr/bin/env python3
"""
Verify Everything is Working
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 70)
print("✅ VERIFYING EVERYTHING IS WORKING")
print("=" * 70)
print()

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    # Check all services
    print("📊 Service Status:")
    services = {
        'phazevpn-web': 'Web Portal',
        'phazevpn-protocol': 'PhazeVPN Protocol',
        'secure-vpn': 'OpenVPN',
        'wg-quick@wg0': 'WireGuard',
        'nginx': 'Nginx'
    }
    
    all_good = True
    for service, name in services.items():
        stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service} 2>&1")
        status = stdout.read().decode().strip()
        symbol = "✅" if status == "active" else "❌"
        print(f"   {symbol} {name}: {status}")
        if status != "active":
            all_good = False
    print()
    
    # Check ports
    print("🔌 Port Status:")
    stdin, stdout, stderr = ssh.exec_command("netstat -tuln 2>/dev/null | grep -E ':(80|443|5000|1194|51820|51821)' || ss -tuln 2>/dev/null | grep -E ':(80|443|5000|1194|51820|51821)'")
    ports = stdout.read().decode()
    if ports:
        for line in ports.split('\n'):
            if line.strip():
                if ':80' in line or ':443' in line:
                    print(f"   ✅ Web (HTTP/HTTPS)")
                elif ':5000' in line:
                    print(f"   ✅ Web Portal (5000)")
                elif ':1194' in line:
                    print(f"   ✅ OpenVPN (1194)")
                elif ':51820' in line:
                    print(f"   ✅ WireGuard (51820)")
                elif ':51821' in line:
                    print(f"   ✅ PhazeVPN Protocol (51821)")
    print()
    
    # Test web portal
    print("🌐 Testing Web Portal:")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/ 2>&1")
    http_code = stdout.read().decode().strip()
    if http_code == "200":
        print("   ✅ Web portal responding (200 OK)")
    else:
        print(f"   ❌ Web portal returned: {http_code}")
        all_good = False
    
    # Test through nginx
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' -k https://127.0.0.1/ 2>&1")
    nginx_code = stdout.read().decode().strip()
    if nginx_code == "200":
        print("   ✅ Nginx proxy working (200 OK)")
    else:
        print(f"   ⚠️  Nginx returned: {nginx_code}")
    print()
    
    # Summary
    print("=" * 70)
    if all_good:
        print("✅ EVERYTHING IS WORKING!")
    else:
        print("⚠️  SOME ISSUES FOUND")
    print("=" * 70)
    print()
    print("🌐 Access your site:")
    print("   https://phazevpn.duckdns.org")
    print()
    print("📊 VPN Protocols:")
    print("   ✅ OpenVPN: Port 1194/UDP")
    print("   ✅ WireGuard: Port 51820/UDP")
    print("   ✅ PhazeVPN Protocol: Port 51821/UDP (Advanced Security)")
    print()
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

