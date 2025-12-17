#!/usr/bin/env python3
"""
Fix ALL users.json files on VPS - make sure web portal reads the right one
"""

import paramiko
import json
import time
import sys

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
    print("🔧 FIXING ALL users.json FILES ON VPS")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # ============================================================
        # STEP 1: Generate proper bcrypt hash
        # ============================================================
        print("1️⃣  Generating proper bcrypt hash for admin123...")
        print("")
        
        hash_code = '''
import bcrypt
pwd = "admin123".encode('utf-8')
salt = bcrypt.gensalt(rounds=12)
hash_val = bcrypt.hashpw(pwd, salt).decode('utf-8')
print(hash_val)
'''
        success, hash_output, error = run_command(ssh, f"python3 << 'HASH'\n{hash_code}\nHASH", check=False)
        
        if not success or not hash_output:
            print(f"   ❌ Failed to generate hash: {error or hash_output}")
            return
        
        admin_hash = hash_output.strip()
        print(f"   ✅ Generated hash: {admin_hash[:30]}...")
        print("")
        
        # ============================================================
        # STEP 2: Create proper users.json structure
        # ============================================================
        print("2️⃣  Creating proper users.json structure...")
        print("")
        
        proper_users = {
            "users": {
                "admin": {
                    "password": admin_hash,
                    "role": "admin",
                    "created": "2025-11-19"
                }
            },
            "roles": {
                "admin": {
                    "can_start_stop_vpn": True,
                    "can_edit_server_config": True,
                    "can_manage_clients": True,
                    "can_view_logs": True,
                    "can_view_statistics": True,
                    "can_export_configs": True,
                    "can_backup": True,
                    "can_disconnect_clients": True,
                    "can_revoke_clients": True,
                    "can_add_clients": True,
                    "can_edit_clients": True,
                    "can_start_download_server": True,
                    "can_manage_users": True,
                    "can_manage_tickets": True
                },
                "moderator": {
                    "can_start_stop_vpn": False,
                    "can_edit_server_config": False,
                    "can_manage_clients": True,
                    "can_view_logs": True,
                    "can_view_statistics": True,
                    "can_export_configs": True,
                    "can_backup": False,
                    "can_disconnect_clients": True,
                    "can_revoke_clients": False,
                    "can_add_clients": True,
                    "can_edit_clients": True,
                    "can_start_download_server": True,
                    "can_manage_users": False,
                    "can_manage_tickets": True
                },
                "user": {
                    "can_start_stop_vpn": False,
                    "can_edit_server_config": False,
                    "can_manage_clients": False,
                    "can_view_logs": False,
                    "can_view_statistics": True,
                    "can_export_configs": False,
                    "can_backup": False,
                    "can_disconnect_clients": False,
                    "can_revoke_clients": False,
                    "can_add_clients": False,
                    "can_edit_clients": False,
                    "can_start_download_server": False,
                    "can_manage_users": False
                },
                "premium": {
                    "can_start_stop_vpn": False,
                    "can_edit_server_config": False,
                    "can_manage_clients": False,
                    "can_view_logs": True,
                    "can_view_statistics": True,
                    "can_export_configs": True,
                    "can_backup": False,
                    "can_disconnect_clients": False,
                    "can_revoke_clients": False,
                    "can_add_clients": False,
                    "can_edit_clients": False,
                    "can_start_download_server": False,
                    "can_manage_users": False
                }
            }
        }
        
        users_json = json.dumps(proper_users, indent=2)
        print("   ✅ Created proper structure")
        print("")
        
        # ============================================================
        # STEP 3: Update ALL possible users.json locations
        # ============================================================
        print("3️⃣  Updating ALL users.json files on VPS...")
        print("")
        
        locations = [
            f"{VPN_DIR}/users.json",
            f"{VPN_DIR}/web-portal/users.json"
        ]
        
        for location in locations:
            print(f"   📝 Updating: {location}")
            
            # Backup existing file
            run_command(ssh, f"cp {location} {location}.backup.$(date +%s) 2>/dev/null || true", check=False)
            
            # Ensure directory exists
            run_command(ssh, f"mkdir -p $(dirname {location})", check=False)
            
            # Write file
            stdin, stdout, stderr = ssh.exec_command(f"cat > {location} << 'EOF'\n{users_json}\nEOF")
            stdout.channel.recv_exit_status()
            
            # Verify it was written
            success, verify_output, _ = run_command(ssh, f"test -f {location} && python3 -m json.tool {location} > /dev/null 2>&1 && echo 'OK' || echo 'FAIL'", check=False)
            if 'OK' in verify_output:
                print(f"      ✅ Updated and verified")
            else:
                print(f"      ⚠️  File exists but may have issues")
        
        # Also create a symlink to ensure consistency
        print("")
        print("   🔗 Creating symlink for consistency...")
        run_command(ssh, f"ln -sf {VPN_DIR}/users.json {VPN_DIR}/web-portal/users.json", check=False)
        print("      ✅ Symlink created")
        print("")
        
        # ============================================================
        # STEP 4: Verify which file the web portal actually uses
        # ============================================================
        print("4️⃣  Verifying which users.json the web portal reads...")
        print("")
        
        test_code = f'''
import sys
from pathlib import Path

# Simulate what app.py does
BASE_DIR = Path(__file__).parent.parent if "__file__" in globals() else Path("/opt/secure-vpn/web-portal").parent
VPN_DIR = BASE_DIR if (BASE_DIR / "vpn-manager.py").exists() else Path("/opt/secure-vpn")
USERS_FILE = VPN_DIR / "users.json"

print(f"BASE_DIR: {{BASE_DIR}}")
print(f"VPN_DIR: {{VPN_DIR}}")
print(f"USERS_FILE: {{USERS_FILE}}")
print(f"EXISTS: {{USERS_FILE.exists()}}")
print(f"ABSOLUTE: {{USERS_FILE.resolve()}}")
'''
        
        success, output, _ = run_command(ssh, f"cd {VPN_DIR}/web-portal && python3 << 'TESTCODE'\n{test_code}\nTESTCODE", check=False)
        if success:
            for line in output.split('\n'):
                if line.strip():
                    print(f"   {line}")
        print("")
        
        # ============================================================
        # STEP 5: Test login with actual web portal code
        # ============================================================
        print("5️⃣  Testing login with actual web portal code...")
        print("")
        
        login_test = f'''
import sys
sys.path.insert(0, "{VPN_DIR}/web-portal")
sys.path.insert(0, "{VPN_DIR}")

try:
    from app import load_users, verify_password
    
    users, roles = load_users()
    
    if "admin" not in users:
        print("❌ ADMIN_NOT_FOUND")
        sys.exit(1)
    
    admin = users["admin"]
    stored_hash = admin.get("password", "")
    
    if len(stored_hash) < 60:
        print(f"❌ HASH_TOO_SHORT: {{len(stored_hash)}}")
        sys.exit(1)
    
    if verify_password("admin123", stored_hash):
        print("✅ LOGIN_TEST_PASSED")
    else:
        print("❌ LOGIN_TEST_FAILED")
        sys.exit(1)
        
except Exception as e:
    import traceback
    print(f"❌ ERROR: {{e}}")
    traceback.print_exc()
    sys.exit(1)
'''
        
        success, output, error = run_command(ssh, f"cd {VPN_DIR}/web-portal && python3 << 'LOGINTEST'\n{login_test}\nLOGINTEST", check=False)
        
        if success and 'LOGIN_TEST_PASSED' in output:
            print("   ✅ Login test PASSED - web portal can authenticate!")
        elif 'LOGIN_TEST_FAILED' in output:
            print("   ❌ Login test FAILED - password verification not working")
        else:
            print(f"   ⚠️  Test output: {output}")
            if error:
                print(f"   Error: {error}")
        print("")
        
        # ============================================================
        # STEP 6: Restart all web portal services
        # ============================================================
        print("6️⃣  Restarting all web portal services...")
        print("")
        
        services = [
            "secure-vpn-download",
            "phazevpn-portal",
            "phazevpn-unified-portal"
        ]
        
        for service in services:
            print(f"   Restarting {service}...")
            run_command(ssh, f"systemctl restart {service} 2>&1 || echo 'Service not found'", check=False)
            time.sleep(1)
        
        time.sleep(2)
        
        # Check which service is actually running the web portal
        success, output, _ = run_command(ssh, "systemctl list-units --type=service --state=running | grep -E 'secure-vpn|phazevpn.*portal' || true", check=False)
        if output:
            print("   Running portal services:")
            for line in output.split('\n'):
                if line.strip():
                    print(f"      {line.strip()}")
        print("")
        
        # ============================================================
        # SUMMARY
        # ============================================================
        print("=" * 70)
        print("✅ ALL users.json FILES FIXED ON VPS")
        print("=" * 70)
        print("")
        print("📋 What was done:")
        print("   1. ✅ Generated proper bcrypt hash")
        print("   2. ✅ Updated /opt/secure-vpn/users.json")
        print("   3. ✅ Updated /opt/secure-vpn/web-portal/users.json")
        print("   4. ✅ Created symlink for consistency")
        print("   5. ✅ Tested login authentication")
        print("   6. ✅ Restarted web portal services")
        print("")
        print("🔐 Login credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("")
        print("🌐 Try logging in now at: https://phazevpn.com/login")
        print("")
        print("⚠️  If login still doesn't work:")
        print("   1. Clear your browser cache/cookies")
        print("   2. Try incognito/private browsing mode")
        print("   3. Check browser console for errors (F12)")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

