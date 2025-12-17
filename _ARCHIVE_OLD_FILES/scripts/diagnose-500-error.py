#!/usr/bin/env python3
"""
Diagnose the 500 Internal Server Error
"""

import paramiko
import sys

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
    print("🔍 DIAGNOSING 500 INTERNAL SERVER ERROR")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # ============================================================
        # STEP 1: Check service status and logs
        # ============================================================
        print("1️⃣  Checking service status...")
        success, status, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -15", check=False)
        print(status)
        print("")
        
        # ============================================================
        # STEP 2: Get recent error logs
        # ============================================================
        print("2️⃣  Checking recent error logs...")
        success, logs, _ = run_command(ssh, "journalctl -u secure-vpn-download --no-pager -n 50 | tail -50", check=False)
        if logs:
            print(logs)
        print("")
        
        # ============================================================
        # STEP 3: Check for Python syntax errors
        # ============================================================
        print("3️⃣  Checking Python syntax...")
        success, syntax_check, _ = run_command(ssh, f"python3 -m py_compile {VPN_DIR}/web-portal/app.py 2>&1", check=False)
        if success:
            print("   ✅ Syntax is valid")
        else:
            print(f"   ❌ Syntax error found:")
            print(f"   {syntax_check[:500]}")
        print("")
        
        # ============================================================
        # STEP 4: Test importing the Flask app
        # ============================================================
        print("4️⃣  Testing Flask app import...")
        test_import = f'''
import sys
sys.path.insert(0, "{VPN_DIR}/web-portal")
sys.path.insert(0, "{VPN_DIR}")

try:
    from app import app
    print("✅ App imported successfully")
    
    # Try to access a route
    with app.test_client() as client:
        response = client.get('/admin')
        print(f"Response status: {{response.status_code}}")
        if response.status_code != 200:
            print(f"Response data: {{response.data[:500]}}")
except Exception as e:
    import traceback
    print(f"❌ Error: {{str(e)}}")
    print("Traceback:")
    traceback.print_exc()
'''
        
        success, import_test, _ = run_command(ssh, f"python3 << 'IMPORT_TEST'\n{test_import}\nIMPORT_TEST", check=False)
        print(import_test)
        print("")
        
        # ============================================================
        # STEP 5: Check if port is listening
        # ============================================================
        print("5️⃣  Checking if service is listening...")
        success, port_check, _ = run_command(ssh, "ss -tuln | grep ':8081' || netstat -tuln | grep ':8081'", check=False)
        if port_check:
            print(f"   ✅ Port 8081 is listening: {port_check}")
        else:
            print("   ❌ Port 8081 is NOT listening")
        print("")
        
        # ============================================================
        # STEP 6: Check for traceback in logs
        # ============================================================
        print("6️⃣  Searching for tracebacks in logs...")
        success, traceback_logs, _ = run_command(ssh, "journalctl -u secure-vpn-download --no-pager -n 200 | grep -A 20 'Traceback' | tail -30", check=False)
        if traceback_logs:
            print("   Found traceback:")
            print(traceback_logs)
        else:
            print("   No recent tracebacks found")
        print("")
        
        # ============================================================
        # STEP 7: Check Nginx error logs
        # ============================================================
        print("7️⃣  Checking Nginx error logs...")
        success, nginx_errors, _ = run_command(ssh, "tail -50 /var/log/nginx/error.log 2>/dev/null | grep -A 10 phazevpn || echo 'No Nginx errors found'", check=False)
        if nginx_errors and 'No Nginx errors' not in nginx_errors:
            print(nginx_errors[:1000])
        else:
            print("   No recent Nginx errors")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

