#!/usr/bin/env python3
"""
Fix Client and Link to Admin User
Make sure admin client exists and is linked properly
"""

from paramiko import SSHClient, AutoAddPolicy
import json

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 70)
print("🔧 FIXING CLIENT AND LINKING TO ADMIN USER")
print("=" * 70)
print()

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print()
    
    # Step 1: Check if admin client exists
    print("1️⃣ Checking admin client...")
    stdin, stdout, stderr = ssh.exec_command(
        "test -f /opt/secure-vpn/client-configs/admin.ovpn && echo 'EXISTS' || echo 'MISSING'"
    )
    client_exists = stdout.read().decode().strip()
    print(f"   Client file: {client_exists}")
    
    if client_exists == "MISSING":
        print("   Creating admin client...")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /opt/secure-vpn && python3 vpn-manager.py add-client admin 2>&1"
        )
        result = stdout.read().decode()
        print(result)
    print()
    
    # Step 2: Check users.json
    print("2️⃣ Checking users.json...")
    stdin, stdout, stderr = ssh.exec_command("cat /opt/secure-vpn/users.json 2>&1")
    users_json = stdout.read().decode()
    
    try:
        users_data = json.loads(users_json)
        admin_user = users_data.get('users', {}).get('admin', {})
        print(f"   Admin user exists: {admin_user is not None}")
        
        # Check if admin has clients linked
        admin_clients = admin_user.get('clients', [])
        print(f"   Admin clients: {admin_clients}")
        
        if 'admin' not in admin_clients:
            print("   ⚠️  Admin client not linked to admin user")
            print("   🔧 Linking admin client to admin user...")
            
            # Update users.json to link admin client
            if 'clients' not in admin_user:
                admin_user['clients'] = []
            if 'admin' not in admin_user['clients']:
                admin_user['clients'].append('admin')
            
            users_data['users']['admin'] = admin_user
            
            # Write back
            updated_json = json.dumps(users_data, indent=2)
            stdin, stdout, stderr = ssh.exec_command(
                f'cat > /opt/secure-vpn/users.json << "EOF"\n{updated_json}\nEOF'
            )
            stdout.channel.recv_exit_status()
            print("   ✅ Admin client linked to admin user")
        else:
            print("   ✅ Admin client already linked")
    except Exception as e:
        print(f"   ❌ Error parsing users.json: {e}")
    print()
    
    # Step 3: Verify the fix
    print("3️⃣ Verifying fix...")
    stdin, stdout, stderr = ssh.exec_command("cat /opt/secure-vpn/users.json | python3 -m json.tool | grep -A 10 '\"admin\"' | head -15")
    admin_data = stdout.read().decode()
    print(admin_data)
    print()
    
    print("=" * 70)
    print("✅ FIX COMPLETE")
    print("=" * 70)
    print()
    print("Now try PhazeVPN client again:")
    print("1. Click CONNECT")
    print("2. Login: admin / admin123")
    print("3. Should work now!")
    print()
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

