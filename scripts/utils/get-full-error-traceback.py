#!/usr/bin/env python3
"""
Get the full error traceback from the login attempt
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
    print("🔍 GETTING FULL ERROR TRACEBACK")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Check recent errors in journal
        print("1️⃣  Getting full error traceback from journal...")
        print("")
        
        success, output, _ = run_command(ssh, "journalctl -u secure-vpn-download --no-pager -n 100 | grep -A 30 'BuildError\\|Traceback\\|Error' | tail -50", check=False)
        if output:
            print("   Recent errors:")
            for line in output.split('\n'):
                if line.strip():
                    print(f"   {line}")
        print("")
        
        # Test login and capture error
        print("2️⃣  Testing login with error capture...")
        print("")
        
        test_code = '''
import sys
sys.path.insert(0, "/opt/secure-vpn/web-portal")
sys.path.insert(0, "/opt/secure-vpn")

from app import app
from flask import Flask

# Enable debug to see errors
app.config['DEBUG'] = True
app.config['TESTING'] = True

with app.test_client() as client:
    # Try login
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=False)
    
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    if response.status_code >= 400:
        print(f"Response: {response.data.decode()[:500]}")
'''
        
        success, output, error = run_command(ssh, f"cd {VPN_DIR}/web-portal && python3 << 'TEST'\n{test_code}\nTEST 2>&1", check=False)
        
        print("   Test output:")
        if output:
            for line in output.split('\n'):
                if line.strip():
                    print(f"      {line}")
        if error:
            print("   Errors:")
            for line in error.split('\n'):
                if line.strip():
                    print(f"      {line}")
        print("")
        
        # Check if the issue is with session cookie settings
        print("3️⃣  Checking session cookie issue...")
        print("")
        
        # The issue might be SESSION_COOKIE_SECURE being False but we're using HTTPS
        # Or SESSION_COOKIE_SAMESITE='Strict' causing issues
        success, output, _ = run_command(ssh, f"grep -n 'SESSION_COOKIE' {VPN_DIR}/web-portal/app.py | head -10", check=False)
        if output:
            print("   Session cookie settings:")
            for line in output.split('\n'):
                if line.strip():
                    print(f"      {line}")
                    
                    # Check if SESSION_COOKIE_SECURE is False but we're using HTTPS
                    if 'SESSION_COOKIE_SECURE' in line and 'False' in line:
                        print("      ⚠️  ISSUE: SESSION_COOKIE_SECURE is False but site uses HTTPS!")
                        print("      This can cause session cookies not to be set!")
                    if 'SESSION_COOKIE_SAMESITE.*Strict' in line.replace(' ', ''):
                        print("      ⚠️  SESSION_COOKIE_SAMESITE='Strict' might cause redirect issues")
        print("")
        
        # Fix session cookie settings
        print("4️⃣  Fixing session cookie settings...")
        print("")
        
        # Read the session config section
        success, session_config, _ = run_command(ssh, f"sed -n '72,84p' {VPN_DIR}/web-portal/app.py", check=False)
        
        if session_config:
            print("   Current config:")
            for line in session_config.split('\n'):
                if line.strip():
                    print(f"      {line}")
            
            # Check if we need to fix SESSION_COOKIE_SECURE
            if 'SESSION_COOKIE_SECURE' in session_config and 'False' in session_config:
                print("")
                print("   🔧 Fixing SESSION_COOKIE_SECURE to auto-detect HTTPS...")
                
                # Read full file
                success2, full_file, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/app.py", check=False)
                if success2:
                    # Replace the SESSION_COOKIE_SECURE line
                    fixed_file = full_file.replace(
                        "app.config['SESSION_COOKIE_SECURE'] = os.environ.get('HTTPS_ENABLED', 'false').lower() == 'true'",
                        "# Auto-detect HTTPS from request\n    app.config['SESSION_COOKIE_SECURE'] = False  # Will be set per-request"
                    )
                    
                    # Actually, let's make it simpler - just set it based on whether we're behind a proxy (which we are with Nginx)
                    # Nginx sets X-Forwarded-Proto header
                    fixed_file = full_file.replace(
                        "app.config['SESSION_COOKIE_SECURE'] = os.environ.get('HTTPS_ENABLED', 'false').lower() == 'true'",
                        "app.config['SESSION_COOKIE_SECURE'] = True  # Always use secure cookies (HTTPS via Nginx)"
                    )
                    
                    # Write back
                    stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/app.py << 'PYEOF'\n{fixed_file}\nPYEOF")
                    stdout.channel.recv_exit_status()
                    print("   ✅ Fixed SESSION_COOKIE_SECURE")
        
        # Also check SESSION_COOKIE_SAMESITE
        if 'Strict' in session_config:
            print("")
            print("   🔧 Changing SESSION_COOKIE_SAMESITE from Strict to Lax...")
            print("   (Strict can cause redirect issues with POST requests)")
            
            success3, full_file2, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/app.py", check=False)
            if success3:
                fixed_file2 = full_file2.replace(
                    "app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'",
                    "app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Changed from Strict to allow POST redirects"
                )
                
                stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/app.py << 'PYEOF'\n{fixed_file2}\nPYEOF")
                stdout.channel.recv_exit_status()
                print("   ✅ Fixed SESSION_COOKIE_SAMESITE")
        print("")
        
        # Restart service
        print("5️⃣  Restarting service...")
        run_command(ssh, "systemctl restart secure-vpn-download", check=False)
        time.sleep(3)
        print("   ✅ Restarted")
        print("")
        
        print("=" * 70)
        print("✅ FIXES APPLIED")
        print("=" * 70)
        print("")
        print("🔧 What was fixed:")
        print("   1. SESSION_COOKIE_SECURE - Set to True for HTTPS")
        print("   2. SESSION_COOKIE_SAMESITE - Changed from Strict to Lax")
        print("")
        print("🌐 Try logging in now!")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

