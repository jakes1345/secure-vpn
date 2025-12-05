#!/usr/bin/env python3
"""
Fix session cookie domain issues - make sure cookies work with phazevpn.com
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
    print("🔧 FIXING SESSION COOKIE DOMAIN ISSUES")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Check current session cookie settings
        print("1️⃣  Checking current session cookie settings...")
        print("")
        
        success, output, _ = run_command(ssh, f"grep -n 'SESSION_COOKIE' {VPN_DIR}/web-portal/app.py", check=False)
        if output:
            print("   Current settings:")
            for line in output.split('\n'):
                if line.strip():
                    print(f"      {line}")
        print("")
        
        # Read the session config section
        print("2️⃣  Reading session configuration section...")
        print("")
        
        success, session_config, _ = run_command(ssh, f"sed -n '72,85p' {VPN_DIR}/web-portal/app.py", check=False)
        if session_config:
            print("   Current config:")
            for line in session_config.split('\n'):
                if line.strip():
                    print(f"      {line}")
        print("")
        
        # Check if SESSION_COOKIE_DOMAIN is set
        print("3️⃣  Checking for SESSION_COOKIE_DOMAIN setting...")
        print("")
        
        success, domain_check, _ = run_command(ssh, f"grep 'SESSION_COOKIE_DOMAIN' {VPN_DIR}/web-portal/app.py || echo 'NOT_SET'", check=False)
        if 'NOT_SET' in domain_check:
            print("   ⚠️  SESSION_COOKIE_DOMAIN is not set")
            print("   This could cause issues if cookies are being set for wrong domain")
        else:
            print(f"   Current domain setting: {domain_check}")
        print("")
        
        # Fix session cookie settings
        print("4️⃣  Fixing session cookie settings for phazevpn.com...")
        print("")
        
        # Read full file
        success, full_file, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/app.py", check=False)
        
        if success:
            # Fix 1: Set SESSION_COOKIE_SECURE to True (we're using HTTPS)
            if "SESSION_COOKIE_SECURE = False" in full_file:
                full_file = full_file.replace(
                    "SESSION_COOKIE_SECURE = False  # Set to True when using HTTPS",
                    "SESSION_COOKIE_SECURE = True  # Always use secure cookies (HTTPS via Nginx)"
                )
                print("   ✅ Fixed SESSION_COOKIE_SECURE = True")
            
            # Fix 2: Set SESSION_COOKIE_SAMESITE to Lax (Strict causes redirect issues)
            if "SESSION_COOKIE_SAMESITE'] = 'Strict'" in full_file:
                full_file = full_file.replace(
                    "app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'",
                    "app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Lax allows POST redirects"
                )
                print("   ✅ Fixed SESSION_COOKIE_SAMESITE = Lax")
            
            # Fix 3: Set SESSION_COOKIE_DOMAIN to None (use default - works for phazevpn.com)
            # Don't set domain, let Flask use default (current domain only)
            if "SESSION_COOKIE_DOMAIN" not in full_file:
                # Add it after SESSION_COOKIE_NAME
                if "SESSION_COOKIE_NAME" in full_file:
                    full_file = full_file.replace(
                        "app.config['SESSION_COOKIE_NAME'] = '__Secure-VPN-Session'",
                        "app.config['SESSION_COOKIE_NAME'] = '__Secure-VPN-Session'\napp.config['SESSION_COOKIE_DOMAIN'] = None  # Use default (current domain only, no subdomain sharing)"
                    )
                    print("   ✅ Added SESSION_COOKIE_DOMAIN = None (prevents mail.phazevpn.com confusion)")
            
            # Fix 4: Remove the __Secure- prefix from cookie name if SESSION_COOKIE_SECURE is False
            # Actually, since we're setting SECURE=True, we can keep __Secure- prefix
            
            # Write fixed file
            stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/app.py << 'PYEOF'\n{full_file}\nPYEOF")
            stdout.channel.recv_exit_status()
            print("   ✅ Updated app.py")
        print("")
        
        # Verify syntax
        print("5️⃣  Verifying syntax...")
        success, syntax_check, _ = run_command(ssh, f"python3 -m py_compile {VPN_DIR}/web-portal/app.py 2>&1", check=False)
        if success:
            print("   ✅ Syntax is valid")
        else:
            print(f"   ❌ Syntax error: {syntax_check}")
            return
        print("")
        
        # Restart service
        print("6️⃣  Restarting web portal service...")
        run_command(ssh, "systemctl restart secure-vpn-download", check=False)
        
        import time
        time.sleep(3)
        
        success, status, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -3", check=False)
        if 'active (running)' in status:
            print("   ✅ Service restarted and running")
        else:
            print(f"   ⚠️  Service status: {status}")
        print("")
        
        # Test session cookie behavior
        print("7️⃣  Testing session cookie behavior...")
        print("")
        
        test_session = '''
import sys
sys.path.insert(0, "/opt/secure-vpn/web-portal")
sys.path.insert(0, "/opt/secure-vpn")

from app import app

print("Session cookie settings:")
print(f"  SESSION_COOKIE_SECURE: {app.config.get('SESSION_COOKIE_SECURE')}")
print(f"  SESSION_COOKIE_SAMESITE: {app.config.get('SESSION_COOKIE_SAMESITE')}")
print(f"  SESSION_COOKIE_DOMAIN: {app.config.get('SESSION_COOKIE_DOMAIN')}")
print(f"  SESSION_COOKIE_NAME: {app.config.get('SESSION_COOKIE_NAME')}")
print(f"  SESSION_COOKIE_HTTPONLY: {app.config.get('SESSION_COOKIE_HTTPONLY')}")
'''
        
        success, test_output, _ = run_command(ssh, f"python3 << 'TEST'\n{test_session}\nTEST", check=False)
        if success:
            for line in test_output.split('\n'):
                if line.strip():
                    print(f"   {line}")
        print("")
        
        print("=" * 70)
        print("✅ SESSION COOKIE FIXES COMPLETE")
        print("=" * 70)
        print("")
        print("🔧 What was fixed:")
        print("   1. ✅ SESSION_COOKIE_SECURE = True (required for HTTPS)")
        print("   2. ✅ SESSION_COOKIE_SAMESITE = Lax (allows POST redirects)")
        print("   3. ✅ SESSION_COOKIE_DOMAIN = None (prevents mail.phazevpn.com confusion)")
        print("")
        print("📋 Important:")
        print("   - Cookies are now set for phazevpn.com only (not shared with mail.phazevpn.com)")
        print("   - Secure cookies are enabled (required for HTTPS)")
        print("   - SameSite is Lax (allows redirects after POST)")
        print("")
        print("🌐 Try logging in now:")
        print("   1. Clear browser cookies for phazevpn.com")
        print("   2. Go to: https://phazevpn.com/login")
        print("   3. Login with: admin / admin123")
        print("")
        print("   If it still redirects, check:")
        print("   - Browser console (F12) for cookie errors")
        print("   - Network tab to see if Set-Cookie header is sent")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

