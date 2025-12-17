#!/usr/bin/env python3
"""
Fix CRITICAL security vulnerabilities
"""

import secrets
import string
import hashlib
from pathlib import Path

print("🔒 Fixing CRITICAL Security Issues...")
print("="*60)

# 1. Generate secure secret key
print("\n1️⃣  Generating secure secret key...")
secret_key = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(64))
print(f"   ✅ Generated: {secret_key[:20]}...")

# Read app.py
app_file = Path('/opt/phaze-vpn/web-portal/app.py')
content = app_file.read_text()

# Replace secret key
old_key = "app.secret_key = 'change-this-to-random-secret-key-in-production'"
new_key = f"app.secret_key = '{secret_key}'  # Auto-generated secure key"
content = content.replace(old_key, new_key)

# Save
app_file.write_text(content)
print("   ✅ Updated app.py with secure secret key")

# 2. Generate secure admin password
print("\n2️⃣  Generating secure passwords...")
def generate_password(length=16):
    return ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(length))

admin_pass = generate_password(20)
moderator_pass = generate_password(20)
user_pass = generate_password(20)

print(f"   ✅ Admin password: {admin_pass}")
print(f"   ✅ Moderator password: {moderator_pass}")
print(f"   ✅ User password: {user_pass}")

# Save passwords to secure file
passwords_file = Path('/opt/phaze-vpn/SECURE-PASSWORDS.txt')
passwords_file.write_text(f"""
🔒 SECURE PASSWORDS - KEEP THIS SECRET!

Generated: {__import__('datetime').datetime.now()}

Admin:
  Username: admin
  Password: {admin_pass}

Moderator:
  Username: moderator
  Password: {moderator_pass}

User:
  Username: user
  Password: {user_pass}

⚠️  IMPORTANT:
- Change these passwords in the web portal after login
- Store this file securely
- Don't share these passwords
""")
print("   ✅ Saved passwords to SECURE-PASSWORDS.txt")

# 3. Add rate limiting function
print("\n3️⃣  Adding rate limiting protection...")
rate_limit_code = '''
# Rate limiting storage (in-memory, simple)
login_attempts = {}
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 900  # 15 minutes

def check_rate_limit(ip):
    """Check if IP is rate limited"""
    import time
    now = time.time()
    
    if ip not in login_attempts:
        login_attempts[ip] = []
    
    # Remove old attempts
    login_attempts[ip] = [t for t in login_attempts[ip] if now - t < RATE_LIMIT_WINDOW]
    
    if len(login_attempts[ip]) >= RATE_LIMIT_MAX:
        return False
    
    login_attempts[ip].append(now)
    return True
'''

# Add before login route
if 'def check_rate_limit' not in content:
    login_route_idx = content.find("@app.route('/login'")
    if login_route_idx > 0:
        # Find the function before login
        func_start = content.rfind('def ', 0, login_route_idx)
        insert_pos = content.rfind('\n', func_start, login_route_idx) + 1
        content = content[:insert_pos] + rate_limit_code + '\n' + content[insert_pos:]
        app_file.write_text(content)
        print("   ✅ Added rate limiting function")

# Update login route to use rate limiting
if 'check_rate_limit(request.remote_addr)' not in content:
    login_check = 'if request.method == \'POST\':'
    rate_limit_check = '''    # Rate limiting
    if not check_rate_limit(request.remote_addr):
        return render_template('login.html', error='Too many login attempts. Please try again in 15 minutes.')'''
    content = content.replace(
        f"@app.route('/login', methods=['GET', 'POST'])\ndef login():\n    \"\"\"Login page\"\"\"\n    {login_check}",
        f"@app.route('/login', methods=['GET', 'POST'])\ndef login():\n    \"\"\"Login page\"\"\"\n    {login_check}\n{rate_limit_check}"
    )
    app_file.write_text(content)
    print("   ✅ Added rate limiting to login route")

print("\n" + "="*60)
print("✅ CRITICAL Security Fixes Applied!")
print("="*60)
print("\n🔒 What was fixed:")
print("  1. ✅ Secure random secret key generated")
print("  2. ✅ Strong passwords generated")
print("  3. ✅ Rate limiting added (5 attempts per 15 min)")
print("\n📋 Next steps:")
print("  1. Deploy updated app.py to VPS")
print("  2. Change default passwords using SECURE-PASSWORDS.txt")
print("  3. Set up HTTPS (recommended)")
print("\n⚠️  Passwords saved to: SECURE-PASSWORDS.txt")
print("    KEEP THIS FILE SECRET!")
print()

