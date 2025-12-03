#!/usr/bin/env python3
"""
Direct fix for admin password - can be run on VPS or locally
"""
import json
import bcrypt
from pathlib import Path
from datetime import datetime

# Try VPS path first, then local
users_files = [
    Path("/opt/phaze-vpn/users.json"),
    Path("/opt/secure-vpn/users.json"),
    Path(__file__).parent / "users.json",
]

users_file = None
for path in users_files:
    if path.exists():
        users_file = path
        break
    # If parent directory exists, we can create it
    if path.parent.exists():
        users_file = path
        break

if not users_file:
    # Use first path and create directory
    users_file = users_files[0]
    users_file.parent.mkdir(parents=True, exist_ok=True)

print(f"Using users file: {users_file}")

# Load existing users
if users_file.exists():
    with open(users_file, 'r') as f:
        users = json.load(f)
    print(f"✅ Loaded {len(users)} existing user(s)")
else:
    users = {}
    print("⚠️  Creating new users.json")

# Hash password
password = "admin123"
password_bytes = password.encode('utf-8')
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

# Update admin user
if 'admin' not in users:
    users['admin'] = {}
    print("✅ Created admin user")

users['admin']['password'] = hashed
users['admin']['role'] = 'admin'
if 'created' not in users['admin']:
    users['admin']['created'] = datetime.now().isoformat()

# Write back
with open(users_file, 'w') as f:
    json.dump(users, f, indent=2)

# Set permissions (if on Linux)
import os
try:
    os.chmod(users_file, 0o600)
except:
    pass

print()
print("=" * 60)
print("✅ Admin user updated!")
print("=" * 60)
print(f"   Username: admin")
print(f"   Password: admin123")
print(f"   Role: admin")
print(f"   Hash: {hashed[:50]}...")
print()
print(f"   File: {users_file}")
print()

