#!/bin/bash
# Start PhazeVPN Protocol Server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting PhazeVPN Protocol Server..."
echo ""

# Check if running as root (needed for TUN interface)
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Warning: Not running as root"
    echo "   TUN interface will not be available"
    echo "   Server will run in relay mode only"
    echo ""
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

# Check if users database exists
if [ ! -f "phazevpn-users.json" ]; then
    echo "⚠️  Users database not found, creating default..."
    python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from crypto import PhazeVPNCrypto
import json
from pathlib import Path

crypto = PhazeVPNCrypto()
users = {}
password = 'admin123'
password_hash, salt = crypto.hash_password(password)
users['admin'] = {
    'password_hash': password_hash.hex(),
    'password_salt': salt.hex()
}

db_path = Path('phazevpn-users.json')
with open(db_path, 'w') as f:
    json.dump(users, f, indent=2)
print("✅ Created users database")
print("   Default user: admin / admin123")
EOF
fi

# Start server
echo "📍 Starting server on port 51821..."
echo ""
python3 phazevpn-server-production.py

