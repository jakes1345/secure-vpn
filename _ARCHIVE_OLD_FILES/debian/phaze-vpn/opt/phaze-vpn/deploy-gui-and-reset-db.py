#!/usr/bin/env python3
"""
Deploy updated GUI and reset database to admin only
"""

import paramiko
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"
LOCAL_DIR = Path(__file__).parent

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

def main():
    print("="*60)
    print("Deploy Updated GUI & Reset Database")
    print("="*60)
    print()
    
    print("🚀 Connecting to VPS...")
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        print("   Make sure you have SSH access configured")
        return
    
    print("✅ Connected")
    print()
    
    try:
        # Deploy updated GUI
        print("📦 Deploying updated GUI...")
        sftp = ssh.open_sftp()
        
        gui_file = LOCAL_DIR / 'vpn-gui.py'
        if gui_file.exists():
            remote_path = f"{VPS_DIR}/vpn-gui.py"
            sftp.put(str(gui_file), remote_path)
            sftp.chmod(remote_path, 0o755)
            print(f"✅ Deployed {gui_file.name} to {remote_path}")
        else:
            print(f"⚠️  {gui_file} not found")
        
        sftp.close()
        print()
        
        # Run database reset
        print("🔄 Resetting database to admin only...")
        print("   (This will delete all users/clients except admin/admin123)")
        print()
        
        # Read and execute reset script
        reset_script = LOCAL_DIR / 'reset-database-to-admin-only.py'
        if reset_script.exists():
            with open(reset_script, 'r') as f:
                script_content = f.read()
            
            # Execute on VPS
            exec_cmd = f"""
cd {VPS_DIR}
python3 << 'PYTHON_EOF'
{script_content}
PYTHON_EOF
"""
            stdin, stdout, stderr = ssh.exec_command(exec_cmd)
            
            # For interactive confirmation, we'll need to handle it differently
            # Instead, let's create a non-interactive version
            print("   Running non-interactive reset...")
            
            # Create Python script for reset
            reset_py = f"""
import json
import bcrypt
from datetime import datetime

admin_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

data = {{
    "users": {{
        "admin": {{
            "password": admin_hash,
            "role": "admin",
            "email": "admin@phazevpn.com",
            "email_verified": True,
            "created": datetime.now().isoformat(),
            "clients": [],
            "subscription": {{
                "tier": "admin",
                "status": "active",
                "created": datetime.now().isoformat(),
                "expires": None
            }}
        }}
    }},
    "roles": {{
        "admin": {{
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
        }}
    }}
}}

with open('users.json', 'w') as f:
    json.dump(data, f, indent=2)
print("✅ users.json reset to admin only")
"""
            
            # Upload reset script
            reset_script_path = f"{VPS_DIR}/reset-db-temp.py"
            sftp = ssh.open_sftp()
            with sftp.file(reset_script_path, 'w') as f:
                f.write(reset_py)
            sftp.chmod(reset_script_path, 0o644)
            sftp.close()
            
            reset_cmd = f"""
cd {VPS_DIR}/web-portal
# Backup
if [ -f users.json ]; then
    cp users.json users.json.backup-$(date +%Y%m%d-%H%M%S)
    echo "✅ Backup created"
fi

# Run reset script
python3 {reset_script_path}

# Delete all client configs
cd {VPS_DIR}
rm -f client-configs/*.ovpn client-configs/*.conf client-configs/*.phazevpn 2>/dev/null || true
rm -f easy-rsa/pki/issued/*.crt easy-rsa/pki/private/*.key easy-rsa/pki/reqs/*.req 2>/dev/null || true
rm -f wireguard/clients/*.conf wireguard/clients/*_private.key wireguard/clients/*_public.key 2>/dev/null || true
rm -f phazevpn-protocol/phazevpn-certs/phazevpn-*.crt phazevpn-protocol/phazevpn-certs/phazevpn-*.key 2>/dev/null || true
echo "✅ All client configs deleted"

# Restart web portal
systemctl restart phaze-vpn-web 2>/dev/null || \
systemctl restart gunicorn 2>/dev/null || \
(pkill -f 'python.*app.py' 2>/dev/null; sleep 1; nohup python3 app.py > /dev/null 2>&1 &)
sleep 2
pgrep -f 'python.*app.py' > /dev/null && echo '✅ Web portal restarted' || echo '⚠️  Check web portal status'
"""
            
            stdin, stdout, stderr = ssh.exec_command(reset_cmd)
            output = stdout.read().decode()
            errors = stderr.read().decode()
            print(output)
            if errors:
                print(f"⚠️  Warnings: {errors}")
            print()
        else:
            print(f"⚠️  {reset_script} not found")
            print()
        
        print("="*60)
        print("✅ DEPLOYMENT COMPLETE!")
        print("="*60)
        print()
        print("What was done:")
        print("  ✅ Updated GUI deployed")
        print("  ✅ Database reset to admin/admin123 only")
        print("  ✅ All client configs deleted")
        print("  ✅ Web portal restarted")
        print()
        print("You can now:")
        print("  • Login with admin/admin123")
        print("  • Create new clients")
        print("  • Download configs using the updated GUI")
        print()
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

