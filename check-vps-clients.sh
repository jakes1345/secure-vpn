#!/bin/bash
# Check clients on VPS

echo "🔍 Checking VPS for clients..."
echo ""

# SSH to VPS and check
ssh root@phazevpn.com << 'VPSCHECK'
echo "=== Checking client configs directory ==="
ls -la /opt/phaze-vpn/client-configs/ 2>/dev/null || echo "Directory doesn't exist"

echo ""
echo "=== Checking if jake.ovpn exists ==="
if [ -f /opt/phaze-vpn/client-configs/jake.ovpn ]; then
    echo "✅ jake.ovpn EXISTS"
    ls -lh /opt/phaze-vpn/client-configs/jake.ovpn
else
    echo "❌ jake.ovpn NOT FOUND"
fi

echo ""
echo "=== Checking users.json for admin's clients ==="
if [ -f /opt/phaze-vpn/web-portal/users.json ]; then
    echo "Admin's clients:"
    python3 << 'PYCHECK'
import json
try:
    with open('/opt/phaze-vpn/web-portal/users.json', 'r') as f:
        data = json.load(f)
        if 'users' in data and 'admin' in data['users']:
            clients = data['users']['admin'].get('clients', [])
            print(f"  Clients linked to admin: {clients}")
            if 'jake' in clients:
                print("  ✅ jake IS linked to admin")
            else:
                print("  ❌ jake is NOT linked to admin")
        else:
            print("  Could not find admin user")
except Exception as e:
    print(f"  Error: {e}")
PYCHECK
else
    echo "users.json not found"
fi

echo ""
echo "=== All .ovpn files ==="
find /opt/phaze-vpn/client-configs/ -name "*.ovpn" 2>/dev/null | head -10
VPSCHECK

