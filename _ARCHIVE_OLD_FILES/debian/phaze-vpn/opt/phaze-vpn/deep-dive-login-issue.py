#!/usr/bin/env python3
"""
Deep dive into login issue - test the actual login flow step by step
"""

import paramiko
import json
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
    print("🔍 DEEP DIVE: Why Login Isn't Working")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # ============================================================
        # STEP 1: Check login route code
        # ============================================================
        print("1️⃣  Checking login route implementation...")
        print("")
        
        success, output, _ = run_command(ssh, f"sed -n '714,766p' {VPN_DIR}/web-portal/app.py", check=False)
        if output:
            print("   Login route code:")
            for i, line in enumerate(output.split('\n'), 714):
                print(f"   {i:4d}: {line}")
        print("")
        
        # ============================================================
        # STEP 2: Check login.html template
        # ============================================================
        print("2️⃣  Checking login.html form submission...")
        print("")
        
        success, output, _ = run_command(ssh, f"grep -n 'form\\|method\\|action\\|submit' {VPN_DIR}/web-portal/templates/login.html | head -15", check=False)
        if output:
            print("   Form details:")
            for line in output.split('\n'):
                if line.strip():
                    print(f"      {line}")
        print("")
        
        # ============================================================
        # STEP 3: Test actual HTTP POST to login endpoint
        # ============================================================
        print("3️⃣  Testing actual HTTP POST to /login...")
        print("")
        
        test_post = '''
import urllib.request
import urllib.parse
import http.cookiejar

# Create cookie jar to handle session cookies
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# First, GET the login page to get any CSRF tokens or session cookies
print("STEP 1: Getting login page...")
try:
    req = urllib.request.Request("http://localhost:8081/login")
    response = opener.open(req, timeout=5)
    login_page = response.read().decode()
    cookies_before = len(cj)
    print(f"   Status: {response.getcode()}")
    print(f"   Cookies received: {cookies_before}")
    
    # Check for CSRF token in page
    if "csrf" in login_page.lower() or "_token" in login_page.lower():
        print("   ⚠️  CSRF token found in page - may need to extract it")
    
except Exception as e:
    print(f"   ❌ Failed to get login page: {e}")
    exit(1)

# Now POST login credentials
print("")
print("STEP 2: POSTing login credentials...")
data = urllib.parse.urlencode({
    "username": "admin",
    "password": "admin123"
}).encode()

req = urllib.request.Request(
    "http://localhost:8081/login",
    data=data,
    method="POST",
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "http://localhost:8081/login"
    }
)

try:
    response = opener.open(req, timeout=5)
    status = response.getcode()
    location = response.headers.get("Location", "")
    cookies_after = len(cj)
    
    print(f"   Status: {status}")
    print(f"   Location header: {location}")
    print(f"   Cookies after login: {cookies_after}")
    
    # Check cookies
    for cookie in cj:
        print(f"   Cookie: {cookie.name} = {cookie.value[:50]}... (domain={cookie.domain}, path={cookie.path})")
    
    if status == 302:
        if "dashboard" in location.lower():
            print("   ✅ SUCCESS: Redirected to dashboard!")
        else:
            print(f"   ⚠️  Redirected to: {location}")
    elif status == 200:
        content = response.read().decode()
        if "invalid" in content.lower() or "error" in content.lower():
            print("   ❌ FAILED: Login rejected")
            # Extract error message
            import re
            error_match = re.search(r'<div[^>]*error[^>]*>([^<]+)</div>', content, re.IGNORECASE)
            if error_match:
                print(f"   Error message: {error_match.group(1)}")
        elif "dashboard" in content.lower():
            print("   ✅ SUCCESS: Dashboard content returned")
        else:
            print("   ⚠️  Status 200 but unclear if login worked")
            print(f"   Content preview: {content[:200]}...")
    
except urllib.error.HTTPError as e:
    print(f"   ❌ HTTP Error {e.code}")
    content = e.read().decode()
    print(f"   Response: {content[:200]}...")
except Exception as e:
    print(f"   ❌ Error: {e}")
'''
        
        success, output, error = run_command(ssh, f"python3 << 'TESTPOST'\n{test_post}\nTESTPOST", check=False)
        if success:
            for line in output.split('\n'):
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"   ❌ Test failed: {error or output}")
        print("")
        
        # ============================================================
        # STEP 4: Check session cookie settings
        # ============================================================
        print("4️⃣  Checking session cookie configuration...")
        print("")
        
        success, output, _ = run_command(ssh, f"grep -n 'SESSION_COOKIE\\|session.permanent\\|session\\[' {VPN_DIR}/web-portal/app.py | head -15", check=False)
        if output:
            print("   Session cookie settings:")
            for line in output.split('\n'):
                if line.strip():
                    print(f"      {line}")
        print("")
        
        # ============================================================
        # STEP 5: Check for rate limiting issues
        # ============================================================
        print("5️⃣  Checking rate limiting...")
        print("")
        
        success, output, _ = run_command(ssh, f"grep -A 10 'check_rate_limit\\|rate_limit' {VPN_DIR}/web-portal/app.py | head -20", check=False)
        if output:
            print("   Rate limiting code:")
            for line in output.split('\n'):
                if line.strip():
                    print(f"      {line}")
        print("")
        
        # ============================================================
        # STEP 6: Test user loading directly
        # ============================================================
        print("6️⃣  Testing user loading and password verification...")
        print("")
        
        test_user = f'''
import sys
sys.path.insert(0, "{VPN_DIR}/web-portal")
sys.path.insert(0, "{VPN_DIR}")

from app import load_users, verify_password

users, roles = load_users()
print(f"Users loaded: {{list(users.keys())}}")

if "admin" in users:
    admin = users["admin"]
    stored_hash = admin.get("password", "")
    print(f"Admin password hash length: {{len(stored_hash)}}")
    
    # Test exact password from login
    test_password = "admin123"
    result = verify_password(test_password, stored_hash)
    print(f"Password 'admin123' verification: {{result}}")
    
    if not result:
        print("❌ PASSWORD VERIFICATION FAILED!")
        # Try to see what's wrong
        print(f"Stored hash: {{stored_hash[:50]}}...")
else:
    print("❌ Admin user not found!")
'''
        
        success, output, error = run_command(ssh, f"python3 << 'TESTUSER'\n{test_user}\nTESTUSER", check=False)
        if success:
            for line in output.split('\n'):
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"   ⚠️  Test output: {error or output}")
        print("")
        
        # ============================================================
        # STEP 7: Check application logs
        # ============================================================
        print("7️⃣  Checking application logs for errors...")
        print("")
        
        # Check if there are any log files
        success, output, _ = run_command(ssh, f"find {VPN_DIR} -name '*.log' -type f 2>/dev/null | head -5", check=False)
        if output:
            print("   Log files found:")
            for log_file in output.split('\n'):
                if log_file.strip():
                    print(f"      {log_file}")
                    # Show last few lines
                    success2, log_output, _ = run_command(ssh, f"tail -5 '{log_file}' 2>/dev/null || echo 'Cannot read'", check=False)
                    if log_output and 'Cannot read' not in log_output:
                        print(f"         Last lines: {log_output[:100]}")
        else:
            print("   ℹ️  No log files found")
        print("")
        
        # Check systemd journal for errors
        print("   Checking systemd journal for errors...")
        success, output, _ = run_command(ssh, "journalctl -u secure-vpn-download --no-pager -n 20 | grep -i 'error\\|exception\\|traceback' || echo 'No errors found'", check=False)
        if output and 'No errors' not in output:
            print("   Recent errors in journal:")
            for line in output.split('\n')[:10]:
                if line.strip():
                    print(f"      {line[:100]}")
        else:
            print("   ✅ No errors in journal")
        print("")
        
        # ============================================================
        # STEP 8: Check username validation
        # ============================================================
        print("8️⃣  Checking username validation...")
        print("")
        
        test_validation = f'''
import sys
sys.path.insert(0, "{VPN_DIR}/web-portal")
sys.path.insert(0, "{VPN_DIR}")

from app import validate_username, sanitize_input

test_username = "admin"
sanitized = sanitize_input(test_username.strip(), max_length=30)
is_valid = validate_username(sanitized)

print(f"Username: '{test_username}'")
print(f"Sanitized: '{sanitized}'")
print(f"Valid: {{is_valid}}")
'''
        
        success, output, error = run_command(ssh, f"python3 << 'TESTVALID'\n{test_validation}\nTESTVALID", check=False)
        if success:
            for line in output.split('\n'):
                if line.strip():
                    print(f"   {line}")
        print("")
        
        # ============================================================
        # SUMMARY & RECOMMENDATIONS
        # ============================================================
        print("=" * 70)
        print("✅ DEEP DIVE COMPLETE")
        print("=" * 70)
        print("")
        print("📋 Common issues to check:")
        print("   1. Session cookies not being set (check cookie settings)")
        print("   2. CSRF token required but not sent")
        print("   3. Rate limiting blocking login attempts")
        print("   4. Username/password validation failing silently")
        print("   5. Redirect loop or dashboard route issue")
        print("   6. Browser blocking cookies (same-site, secure flags)")
        print("")
        print("🔧 Next steps:")
        print("   1. Check the HTTP POST test results above")
        print("   2. Check browser console (F12) for JavaScript errors")
        print("   3. Check browser Network tab for login request/response")
        print("   4. Try with browser developer tools to see exact error")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

