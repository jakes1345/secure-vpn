#!/usr/bin/env python3
"""
Fix admin login on VPS - ensure admin/admin123 works
"""
import paramiko
from pathlib import Path
import json
import bcrypt
import tempfile
import os

# SSH connection
hostname = "phazevpn.com"
username = "root"
key_paths = [
    Path.home() / '.ssh' / 'id_rsa',
    Path.home() / '.ssh' / 'id_ed25519',
]

print("=" * 60)
print("Fixing Admin Login on VPS")
print("=" * 60)
print()

# Try to connect
ssh = None
for key_path in key_paths:
    if key_path.exists():
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname, username=username, key_filename=str(key_path), timeout=10)
            print(f"✅ Connected using {key_path.name}")
            break
        except Exception as e:
            print(f"❌ Failed with {key_path.name}: {e}")
            continue

if not ssh:
    print("❌ Could not connect to VPS")
    print("   Please run this script manually or check SSH keys")
    exit(1)

# Fix admin password
print("\n[1/3] Checking users.json...")
users_file = "/opt/phaze-vpn/users.json"

# Read current users
stdin, stdout, stderr = ssh.exec_command(f"cat {users_file} 2>/dev/null || echo '{{}}'")
users_content = stdout.read().decode().strip()
if not users_content or users_content == '{}':
    users = {}
    print("   ⚠️  users.json is empty or doesn't exist")
else:
    try:
        users = json.loads(users_content)
        print(f"   ✅ Found {len(users)} user(s)")
    except json.JSONDecodeError as e:
        print(f"   ❌ Invalid JSON: {e}")
        users = {}

# Hash new password
print("\n[2/3] Creating password hash...")
password = "admin123"
password_bytes = password.encode('utf-8')
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
print(f"   ✅ Password hash created")

# Update admin user
print("\n[3/3] Updating admin user...")
if 'admin' not in users:
    users['admin'] = {}
    print("   ✅ Created admin user")

users['admin']['password'] = hashed
users['admin']['role'] = 'admin'
if 'created' not in users['admin']:
    from datetime import datetime
    users['admin']['created'] = datetime.now().isoformat()

# Write back
print("   Writing users.json...")
import tempfile
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
    json.dump(users, f, indent=2)
    temp_file = f.name

# Copy to VPS
sftp = ssh.open_sftp()
try:
    sftp.put(temp_file, users_file)
    print("   ✅ File uploaded")
except Exception as e:
    print(f"   ❌ Upload failed: {e}")
    sftp.close()
    os.unlink(temp_file)
    ssh.close()
    exit(1)
sftp.close()
os.unlink(temp_file)

# Set permissions
stdin, stdout, stderr = ssh.exec_command(f"chmod 600 {users_file}")
stdout.read()  # Wait for command

print()
print("=" * 60)
print("✅ Admin user updated!")
print("=" * 60)
print(f"   Username: admin")
print(f"   Password: admin123")
print(f"   Role: admin")
print()
print("Testing login...")

# Test login
import requests
import urllib3
urllib3.disable_warnings()

session = requests.Session()
session.verify = False
try:
    response = session.post(
        "https://phazevpn.com/api/app/login",
        json={"username": "admin", "password": "admin123"},
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ Login successful!")
        data = response.json()
        print(f"   User: {data.get('user', {})}")
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ Connection error: {e}")

ssh.close()
print()
print("Done!")

