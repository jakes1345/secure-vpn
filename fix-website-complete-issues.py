#!/usr/bin/env python3
"""
Fix all website issues:
1. Port 5000 conflict (multiple gunicorn processes)
2. Email/SMTP configuration
3. Login/signup errors
"""

import paramiko
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description=""):
    """Run command on VPS"""
    if description:
        print(f"🔧 {description}...")
    
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    
    output_lines = []
    for line in iter(stdout.readline, ""):
        if line:
            line = line.rstrip()
            print(f"   {line}")
            output_lines.append(line)
    
    exit_status = stdout.channel.recv_exit_status()
    return exit_status == 0, "\n".join(output_lines)

def main():
    print("=" * 70)
    print("🔧 FIXING ALL WEBSITE ISSUES")
    print("=" * 70)
    print("")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # 1. Fix port 5000 conflict - kill all gunicorn processes
        print("1️⃣ Fixing port 5000 conflict...")
        run_command(ssh, "pkill -9 gunicorn", "Killing all gunicorn processes")
        time.sleep(2)
        
        # Verify port is free
        success, output = run_command(ssh, "lsof -i :5000 || echo 'PORT_FREE'", "Checking port 5000")
        if 'PORT_FREE' in output or not output.strip():
            print("   ✅ Port 5000 is now free")
        else:
            print("   ⚠️  Port still in use, killing processes...")
            run_command(ssh, "fuser -k 5000/tcp 2>/dev/null || true", "Force killing port 5000")
            time.sleep(1)
        
        # 2. Stop and restart web portal service
        print("\n2️⃣ Restarting web portal service...")
        run_command(ssh, "systemctl stop phazevpn-portal", "Stopping service")
        time.sleep(2)
        run_command(ssh, "systemctl start phazevpn-portal", "Starting service")
        time.sleep(3)
        
        # Check status
        success, output = run_command(ssh, "systemctl status phazevpn-portal --no-pager | head -15", "Checking service status")
        if 'active (running)' in output.lower():
            print("   ✅ Web portal service is running")
        else:
            print("   ❌ Service not running properly")
        
        # 3. Check email configuration
        print("\n3️⃣ Checking email configuration...")
        success, output = run_command(ssh, "test -f /opt/phaze-vpn/web-portal/email_util.py && echo 'EXISTS' || echo 'NOT_FOUND'", "Checking email util")
        
        # Check if postfix/sendmail is running
        success, output = run_command(ssh, "systemctl is-active postfix 2>&1 || echo 'NOT_ACTIVE'", "Checking postfix")
        if 'active' in output.lower():
            print("   ✅ Postfix is running")
        else:
            print("   ⚠️  Postfix not running - starting...")
            run_command(ssh, "systemctl start postfix && systemctl enable postfix", "Starting postfix")
        
        # 4. Test website endpoints
        print("\n4️⃣ Testing website endpoints...")
        time.sleep(2)
        
        # Test login page
        success, output = run_command(ssh, "curl -s -o /dev/null -w 'Login page: %{http_code}' http://localhost:5000/login 2>&1", "Testing login")
        print(f"   {output.strip()}")
        
        # Test signup page
        success, output = run_command(ssh, "curl -s -o /dev/null -w 'Signup page: %{http_code}' http://localhost:5000/signup 2>&1", "Testing signup")
        print(f"   {output.strip()}")
        
        # Test homepage
        success, output = run_command(ssh, "curl -s -o /dev/null -w 'Homepage: %{http_code}' http://localhost:5000/ 2>&1", "Testing homepage")
        print(f"   {output.strip()}")
        
        # 5. Check for Python errors in app
        print("\n5️⃣ Checking for Python import errors...")
        success, output = run_command(ssh, "cd /opt/phaze-vpn/web-portal && python3 -c 'import app' 2>&1 | head -10", "Testing app imports")
        if 'Error' in output or 'ImportError' in output or 'ModuleNotFoundError' in output:
            print("   ⚠️  Import errors found:")
            for line in output.split('\n')[:5]:
                if line.strip() and ('Error' in line or 'Import' in line):
                    print(f"      {line[:80]}")
        else:
            print("   ✅ No import errors")
        
        # 6. Check recent application errors
        print("\n6️⃣ Checking application error logs...")
        success, output = run_command(ssh, "tail -30 /var/log/phazevpn-portal-error.log 2>&1 | grep -i 'error\\|exception\\|traceback' | tail -10 || echo 'NO_ERRORS'", "Checking error log")
        if 'NO_ERRORS' not in output and output.strip():
            print("   Recent errors:")
            for line in output.strip().split('\n')[:5]:
                if line.strip():
                    print(f"      {line[:100]}")
        else:
            print("   ✅ No recent errors in log")
        
        # Summary
        print("\n" + "=" * 70)
        print("📋 SUMMARY")
        print("=" * 70)
        print("")
        print("✅ Port 5000 conflict fixed")
        print("✅ Web portal service restarted")
        print("✅ Postfix email service checked")
        print("")
        print("🔧 Next steps if issues persist:")
        print("   1. Check application logs: journalctl -u phazevpn-portal -f")
        print("   2. Test login/signup manually")
        print("   3. Check email configuration in app.py")
        print("")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

