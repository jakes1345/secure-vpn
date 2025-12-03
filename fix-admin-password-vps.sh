#!/bin/bash
# Fix admin password on VPS - run this ON THE VPS

set -e

echo "============================================================"
echo "Fixing Admin Password on VPS"
echo "============================================================"
echo ""

USERS_FILE="/opt/phaze-vpn/users.json"
BACKUP_FILE="${USERS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# Backup
if [ -f "$USERS_FILE" ]; then
    cp "$USERS_FILE" "$BACKUP_FILE"
    echo "✅ Backed up to: $BACKUP_FILE"
else
    echo "⚠️  users.json not found, will create new one"
fi

# Create Python script to hash password
python3 << 'PYTHON_SCRIPT'
import json
import bcrypt
from pathlib import Path
from datetime import datetime

users_file = Path("/opt/phaze-vpn/users.json")

# Load existing users or create new
if users_file.exists():
    with open(users_file, 'r') as f:
        users = json.load(f)
else:
    users = {}

# Hash password
password = "admin123"
password_bytes = password.encode('utf-8')
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

# Update admin user
if 'admin' not in users:
    users['admin'] = {}

users['admin']['password'] = hashed
users['admin']['role'] = 'admin'
if 'created' not in users['admin']:
    users['admin']['created'] = datetime.now().isoformat()

# Write back
users_file.parent.mkdir(parents=True, exist_ok=True)
with open(users_file, 'w') as f:
    json.dump(users, f, indent=2)

print(f"✅ Admin user updated")
print(f"   Username: admin")
print(f"   Password: admin123")
print(f"   Hash: {hashed[:50]}...")

# Set permissions
import os
os.chmod(users_file, 0o600)
print(f"✅ Permissions set to 600")
PYTHON_SCRIPT

echo ""
echo "============================================================"
echo "✅ Admin password fixed!"
echo "============================================================"
echo ""
echo "Now test login with:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""

