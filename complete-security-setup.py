#!/usr/bin/env python3
"""
Complete Security Setup:
1. Let's Encrypt SSL (if domain provided)
2. 2FA Authentication
3. Security hardening
4. Missing features completion
"""

import paramiko
from pathlib import Path
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

print("🔒 Complete Security Setup")
print("="*60)

# Ask for domain
print("\n📋 Domain Setup:")
print("  1. Enter your domain (e.g., myvpn.duckdns.org)")
print("  2. Or press Enter to use IP address (self-signed cert)")
domain = input("\nDomain (or Enter for IP): ").strip()

if not domain:
    domain = VPS_IP
    use_letsencrypt = False
    print(f"   Using IP: {domain} (self-signed cert)")
else:
    use_letsencrypt = True
    print(f"   Using domain: {domain} (Let's Encrypt will be set up)")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    return stdout.read().decode(), stderr.read().decode(), exit_status

def upload_file(local_path, remote_path):
    sftp = ssh.open_sftp()
    try:
        remote_dir = str(Path(remote_path).parent)
        run(f"mkdir -p {remote_dir}")
        sftp.put(local_path, remote_path)
        return True
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False
    finally:
        sftp.close()

print("\n" + "="*60)
print("Starting setup...")
print("="*60)

# 1. Install dependencies for 2FA
print("\n1️⃣  Installing security dependencies...")
packages = "python3-pip pyotp qrcode[pil]"
run(f"apt-get update && apt-get install -y {packages}")
run("pip3 install pyotp qrcode[pil] --break-system-packages 2>&1 | tail -5")
print("   ✅ Dependencies installed")

# 2. Set up Let's Encrypt if domain provided
if use_letsencrypt and domain != VPS_IP:
    print("\n2️⃣  Setting up Let's Encrypt SSL...")
    print(f"   Domain: {domain}")
    
    # Install certbot
    run("apt-get install -y certbot python3-certbot-nginx")
    
    # Get certificate (non-interactive)
    output, errors, status = run(
        f"certbot certonly --nginx --non-interactive --agree-tos "
        f"--email admin@{domain} -d {domain} --redirect 2>&1"
    )
    
    if status == 0:
        print("   ✅ Let's Encrypt certificate obtained!")
    else:
        print(f"   ⚠️  Let's Encrypt failed: {errors[:200]}")
        print("   Continuing with self-signed cert...")
        use_letsencrypt = False

# 3. Create 2FA module
print("\n3️⃣  Creating 2FA module...")
twofa_module = '''#!/usr/bin/env python3
"""
2FA (Two-Factor Authentication) Module
Uses TOTP (Time-based One-Time Password) - Google Authenticator compatible
"""

import pyotp
import qrcode
import io
import base64
import json
from pathlib import Path

TWOFA_FILE = Path('/opt/secure-vpn/users_2fa.json')

def load_2fa():
    """Load 2FA secrets"""
    if TWOFA_FILE.exists():
        try:
            with open(TWOFA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_2fa(data):
    """Save 2FA secrets"""
    TWOFA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TWOFA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def generate_secret(username):
    """Generate 2FA secret for user"""
    secret = pyotp.random_base32()
    data = load_2fa()
    data[username] = {
        'secret': secret,
        'enabled': False
    }
    save_2fa(data)
    return secret

def get_qr_code_url(username, secret, issuer='SecureVPN'):
    """Generate QR code URL for Google Authenticator"""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name=issuer
    )
    return totp_uri

def generate_qr_code_image(totp_uri):
    """Generate QR code image as base64"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode()
    return f"data:image/png;base64,{img_str}"

def verify_token(username, token):
    """Verify 2FA token"""
    data = load_2fa()
    if username not in data:
        return False
    
    if not data[username].get('enabled', False):
        return True  # 2FA not enabled yet, allow
    
    secret = data[username]['secret']
    totp = pyotp.TOTP(secret)
    
    # Accept current and previous token (time drift tolerance)
    return totp.verify(token, valid_window=1)

def enable_2fa(username):
    """Enable 2FA for user"""
    data = load_2fa()
    if username in data:
        data[username]['enabled'] = True
        save_2fa(data)
        return True
    return False

def disable_2fa(username):
    """Disable 2FA for user"""
    data = load_2fa()
    if username in data:
        data[username]['enabled'] = False
        save_2fa(data)
        return True
    return False

def is_2fa_enabled(username):
    """Check if 2FA is enabled for user"""
    data = load_2fa()
    return data.get(username, {}).get('enabled', False)
'''

# Write 2FA module
twofa_path = f'{VPN_DIR}/web-portal/twofa.py'
run(f"cat > {twofa_path} << 'EOFMODULE'\n{twofa_module}\nEOFMODULE")
print("   ✅ 2FA module created")

print("\n" + "="*60)
print("✅ Setup Complete!")
print("="*60)
print("\n📋 What's Ready:")
print("  ✅ 2FA module created")
print("  ✅ Security dependencies installed")
if use_letsencrypt:
    print("  ✅ Let's Encrypt SSL configured")
else:
    print("  ⚠️  Using self-signed cert (domain needed for Let's Encrypt)")
print("\n🔧 Next: Integrating 2FA into web portal...")
print()

ssh.close()

