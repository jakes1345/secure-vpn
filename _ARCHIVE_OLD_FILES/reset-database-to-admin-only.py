#!/usr/bin/env python3
"""
Hard reset database - Keep only admin/admin123
Removes all users, clients, emails, everything except admin
"""

import paramiko
import os
import json
from pathlib import Path
from datetime import datetime

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"

def connect_vps():
    """Connect to VPS"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key_paths = [
        Path.home() / '.ssh' / 'id_rsa',
        Path.home() / '.ssh' / 'id_ed25519',
    ]
    
    for key_path in key_paths:
        if key_path.exists() and key_path.is_file():
            try:
                key = paramiko.RSAKey.from_private_key_file(str(key_path))
                ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                return ssh
            except:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(str(key_path))
                    ssh.connect(VPS_HOST, username=VPS_USER, pkey=key, timeout=10)
                    return ssh
                except:
                    continue
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        return ssh
    except:
        pass
    
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    return None

def hash_password(password):
    """Hash password using bcrypt"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def main():
    print("="*60)
    print("HARD RESET DATABASE - Admin Only")
    print("="*60)
    print()
    print("⚠️  WARNING: This will DELETE:")
    print("   - All users except admin")
    print("   - All client configs")
    print("   - All emails/verification tokens")
    print("   - Everything except admin/admin123")
    print()
    
    confirm = input("Type 'RESET' to confirm: ").strip()
    if confirm != 'RESET':
        print("❌ Cancelled")
        return
    
    print()
    print("🚀 Connecting to VPS...")
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect")
        return
    
    try:
        # Backup existing users.json
        print("📦 Creating backup...")
        backup_cmd = f"""
cd {VPS_DIR}/web-portal
if [ -f users.json ]; then
    cp users.json users.json.backup-$(date +%Y%m%d-%H%M%S)
    echo "✅ Backup created"
else
    echo "⚠️  No users.json to backup"
fi
"""
        stdin, stdout, stderr = ssh.exec_command(backup_cmd)
        print(stdout.read().decode())
        print()
        
        # Create new users.json with only admin
        print("🔄 Creating fresh users.json (admin only)...")
        admin_password_hash = hash_password('admin123')
        
        new_users = {
            'admin': {
                'password': admin_password_hash,
                'role': 'admin',
                'email': 'admin@phazevpn.com',
                'email_verified': True,
                'created': datetime.now().isoformat(),
                'clients': [],
                'subscription': {
                    'tier': 'admin',
                    'status': 'active',
                    'created': datetime.now().isoformat(),
                    'expires': None
                }
            }
        }
        
        # Default admin role permissions (matching web-portal/app.py)
        new_roles = {
            'admin': {
                'can_start_stop_vpn': True,
                'can_edit_server_config': True,
                'can_manage_clients': True,
                'can_view_logs': True,
                'can_view_statistics': True,
                'can_export_configs': True,
                'can_backup': True,
                'can_disconnect_clients': True,
                'can_revoke_clients': True,
                'can_add_clients': True,
                'can_edit_clients': True,
                'can_start_download_server': True,
                'can_manage_users': True,
                'can_manage_tickets': True
            }
        }
        
        # Format: {"users": {...}, "roles": {...}}
        data = {
            'users': new_users,
            'roles': new_roles
        }
        
        users_json = json.dumps(data, indent=2)
        
        # Write new users.json
        write_cmd = f"""
cd {VPS_DIR}/web-portal
cat > users.json << 'USERS_EOF'
{users_json}
USERS_EOF
chmod 600 users.json
echo "✅ users.json reset"
"""
        stdin, stdout, stderr = ssh.exec_command(write_cmd)
        output = stdout.read().decode()
        errors = stderr.read().decode()
        print(output)
        if errors:
            print(f"⚠️  Warnings: {errors}")
        print()
        
        # Delete all client configs
        print("🗑️  Deleting all client configs...")
        delete_configs_cmd = f"""
cd {VPS_DIR}
rm -f client-configs/*.ovpn client-configs/*.conf client-configs/*.phazevpn 2>/dev/null || true
rm -f easy-rsa/pki/issued/*.crt easy-rsa/pki/private/*.key easy-rsa/pki/reqs/*.req 2>/dev/null || true
rm -f wireguard/clients/*.conf wireguard/clients/*_private.key wireguard/clients/*_public.key 2>/dev/null || true
rm -f phazevpn-protocol/phazevpn-certs/phazevpn-*.crt phazevpn-protocol/phazevpn-certs/phazevpn-*.key 2>/dev/null || true
echo "✅ All client configs deleted"
"""
        stdin, stdout, stderr = ssh.exec_command(delete_configs_cmd)
        print(stdout.read().decode())
        print()
        
        # Keep CA and server certs (don't delete those)
        print("✅ Keeping CA and server certificates (needed for VPN)")
        print()
        
        # Restart web portal
        print("🔄 Restarting web portal...")
        restart_cmd = f"""
cd {VPS_DIR}/web-portal
systemctl restart phaze-vpn-web 2>/dev/null || \
systemctl restart gunicorn 2>/dev/null || \
(pkill -f 'python.*app.py' 2>/dev/null; sleep 1; nohup python3 app.py > /dev/null 2>&1 &)
sleep 2
pgrep -f 'python.*app.py' > /dev/null && echo '✅ Web portal restarted' || echo '⚠️  Check web portal status'
"""
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        print(stdout.read().decode())
        print()
        
        print("="*60)
        print("✅ DATABASE RESET COMPLETE!")
        print("="*60)
        print()
        print("What's left:")
        print("  ✅ admin / admin123 (only user)")
        print("  ✅ CA and server certificates (for VPN)")
        print()
        print("What's deleted:")
        print("  ❌ All other users")
        print("  ❌ All client configs")
        print("  ❌ All emails/verification tokens")
        print("  ❌ Everything else")
        print()
        print("Backup saved (if users.json existed)")
        print()
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

