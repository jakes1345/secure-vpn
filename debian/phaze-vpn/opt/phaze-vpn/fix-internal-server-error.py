#!/usr/bin/env python3
"""
Fix internal server error - check logs and fix issues
"""

import paramiko
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

def run_command(ssh, command, check=True):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("🔍 DIAGNOSING INTERNAL SERVER ERROR")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Check service status
        print("1️⃣  Checking web portal service status...")
        print("")
        
        success, status, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -10", check=False)
        if status:
            print(status)
        print("")
        
        # Check for Python errors
        print("2️⃣  Checking for Python syntax errors...")
        print("")
        
        success, syntax_check, _ = run_command(ssh, f"python3 -m py_compile {VPN_DIR}/web-portal/app.py 2>&1", check=False)
        if not success or syntax_check:
            print("   ❌ Syntax errors found:")
            print(f"   {syntax_check}")
        else:
            print("   ✅ No syntax errors")
        print("")
        
        # Check recent errors in journal
        print("3️⃣  Checking recent errors in logs...")
        print("")
        
        success, errors, _ = run_command(ssh, "journalctl -u secure-vpn-download --no-pager -n 50 | grep -i 'error\\|exception\\|traceback\\|failed' | tail -20", check=False)
        if errors:
            print("   Recent errors:")
            for line in errors.split('\n')[:15]:
                if line.strip():
                    print(f"   {line[:120]}")
        else:
            print("   ℹ️  No obvious errors in journal")
        print("")
        
        # Check full traceback
        print("4️⃣  Getting full error traceback...")
        print("")
        
        success, traceback_output, _ = run_command(ssh, "journalctl -u secure-vpn-download --no-pager -n 100 | grep -A 30 'Traceback\\|Error\\|Exception' | tail -40", check=False)
        if traceback_output:
            print("   Error traceback:")
            for line in traceback_output.split('\n'):
                if line.strip():
                    print(f"   {line[:120]}")
        print("")
        
        # Check if service is actually running
        print("5️⃣  Checking if service is running...")
        print("")
        
        success, is_active, _ = run_command(ssh, "systemctl is-active secure-vpn-download 2>&1", check=False)
        print(f"   Service status: {is_active}")
        
        # Check if port is listening
        success, port_check, _ = run_command(ssh, "netstat -tuln | grep :8081 || ss -tuln | grep :8081", check=False)
        if port_check:
            print(f"   ✅ Port 8081 is listening: {port_check[:100]}")
        else:
            print("   ❌ Port 8081 is NOT listening - service crashed!")
        print("")
        
        # Check what page is causing the error
        print("6️⃣  Testing which page causes error...")
        print("")
        
        test_pages = [
            ("/", "Home page"),
            ("/login", "Login page"),
            ("/download", "Download page"),
            ("/admin", "Admin dashboard")
        ]
        
        for path, name in test_pages:
            test_code = f'''
import urllib.request
try:
    req = urllib.request.Request("http://localhost:8081{path}")
    response = urllib.request.urlopen(req, timeout=5)
    status = response.getcode()
    print(f"{name}: HTTP {{status}}")
except Exception as e:
    print(f"{name}: ERROR - {{e}}")
'''
            success, test_output, _ = run_command(ssh, f"python3 << 'TEST'\n{test_code}\nTEST", check=False)
            if test_output:
                print(f"   {test_output}")
        print("")
        
        # Try to restart service
        print("7️⃣  Attempting to restart service...")
        print("")
        
        run_command(ssh, "systemctl restart secure-vpn-download", check=False)
        time.sleep(3)
        
        success, restart_status, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -5", check=False)
        if 'active (running)' in restart_status:
            print("   ✅ Service restarted successfully")
        else:
            print("   ❌ Service failed to start:")
            print(restart_status)
        
        print("")
        print("=" * 70)
        print("✅ DIAGNOSIS COMPLETE")
        print("=" * 70)
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

