#!/usr/bin/env python3
"""
Check which portal service is actually serving the login page
"""

import paramiko
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("🔍 CHECKING WHICH PORTAL IS SERVING LOGIN PAGE")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Check Nginx configuration
        print("1️⃣  Checking Nginx configuration for phazevpn.com...")
        print("")
        
        success, output, _ = run_command(ssh, "grep -A 10 'server_name.*phazevpn.com' /etc/nginx/sites-enabled/* 2>/dev/null | head -20", check=False)
        if output:
            print("   Nginx config:")
            for line in output.split('\n'):
                if line.strip() and not line.strip().startswith('#'):
                    print(f"      {line}")
        print("")
        
        # Check which port/proxy the login page uses
        print("2️⃣  Checking which backend handles the login route...")
        print("")
        
        success, output, _ = run_command(ssh, "grep -B 5 -A 10 'location.*login\|proxy_pass' /etc/nginx/sites-enabled/* 2>/dev/null | head -30", check=False)
        if output:
            print("   Login route config:")
            for line in output.split('\n'):
                if line.strip() and not line.strip().startswith('#'):
                    print(f"      {line}")
        print("")
        
        # Check which services are listening on which ports
        print("3️⃣  Checking which services are listening on ports...")
        print("")
        
        success, output, _ = run_command(ssh, "netstat -tuln | grep -E ':(8081|5000|8000|8080|5001)' || ss -tuln | grep -E ':(8081|5000|8000|8080|5001)'", check=False)
        if output:
            print("   Services listening:")
            for line in output.split('\n'):
                if line.strip():
                    print(f"      {line}")
        print("")
        
        # Check process information for each portal service
        print("4️⃣  Checking each portal service...")
        print("")
        
        services = [
            ("secure-vpn-download", "PhazeVPN Web Portal"),
            ("phazevpn-portal", "PhazeVPN Portal (Gunicorn)"),
            ("phazevpn-unified-portal", "PhazeVPN Unified Portal")
        ]
        
        for service_name, description in services:
            print(f"   {service_name}:")
            success, output, _ = run_command(ssh, f"systemctl status {service_name} --no-pager | head -10", check=False)
            if 'active (running)' in output:
                print(f"      ✅ Running: {description}")
                # Get the actual process and working directory
                success2, output2, _ = run_command(ssh, f"systemctl show {service_name} -p ExecStart -p WorkingDirectory", check=False)
                if output2:
                    for line in output2.split('\n'):
                        if line.strip():
                            print(f"      {line}")
            else:
                print(f"      ⚠️  Not running or inactive")
            print("")
        
        # Test direct access to each portal
        print("5️⃣  Testing direct access to portals...")
        print("")
        
        test_code = '''
import urllib.request
import urllib.error

ports = [8081, 5000, 8000, 8080, 5001]
for port in ports:
    try:
        req = urllib.request.Request(f"http://localhost:{port}/login", method="HEAD")
        urllib.request.urlopen(req, timeout=2)
        print(f"✅ Port {port}: Responding")
    except:
        pass
'''
        
        success, output, _ = run_command(ssh, f"python3 << 'TEST'\n{test_code}\nTEST", check=False)
        if output:
            print(f"   {output}")
        print("")
        
        print("=" * 70)
        print("✅ CHECK COMPLETE")
        print("=" * 70)
        print("")
        print("Based on the config above, identify which service handles:")
        print("   - https://phazevpn.com/login")
        print("")
        print("Then make sure THAT service's users.json is updated!")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

