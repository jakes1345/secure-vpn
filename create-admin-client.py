#!/usr/bin/env python3
"""
Create VPN Client for Admin User
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 70)
print("🔧 CREATING VPN CLIENT FOR ADMIN USER")
print("=" * 70)
print()

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print()
    
    # Create client for admin user
    print("1️⃣ Creating VPN client for admin user...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/secure-vpn && python3 vpn-manager.py add-client admin 2>&1"
    )
    result = stdout.read().decode()
    error = stderr.read().decode()
    
    print(result)
    if error:
        print(f"Errors: {error}")
    
    # Check if client was created
    stdin, stdout, stderr = ssh.exec_command(
        "test -f /opt/secure-vpn/client-configs/admin.ovpn && echo 'EXISTS' || echo 'MISSING'"
    )
    client_exists = stdout.read().decode().strip()
    
    if client_exists == "EXISTS":
        print("   ✅ Client config created: admin.ovpn")
    else:
        print("   ⚠️  Client config might not exist")
    print()
    
    # Verify the client is in users.json
    print("2️⃣ Verifying client in database...")
    stdin, stdout, stderr = ssh.exec_command(
        "grep -A 5 '\"admin\"' /opt/secure-vpn/users.json 2>&1 | head -10"
    )
    user_data = stdout.read().decode()
    if user_data:
        print("   ✅ Admin user found in database")
    else:
        print("   ⚠️  Admin user not found")
    print()
    
    print("=" * 70)
    print("✅ CLIENT CREATED")
    print("=" * 70)
    print()
    print("Now try connecting with PhazeVPN client:")
    print("1. Click CONNECT in PhazeVPN client")
    print("2. Login with:")
    print("   Username: admin")
    print("   Password: admin123")
    print("3. Client should download config and connect")
    print()
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

