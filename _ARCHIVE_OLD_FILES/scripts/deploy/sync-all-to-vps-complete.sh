#!/bin/bash
# COMPREHENSIVE VPS SYNC SCRIPT
# Syncs ALL web portal files to VPS - complete and thorough

set -e

VPS_IP="${VPS_IP:-15.204.11.19}"
VPS_USER="${VPS_USER:-root}"
VPS_PASS="${VPS_PASS:-}"

if [ -z "$VPS_PASS" ]; then
    echo "❌ Error: VPS_PASS environment variable not set"
    echo "   Set it with: export VPS_PASS='your-password'"
    exit 1
fi
VPS_PATH="/opt/secure-vpn/web-portal"
LOCAL_PATH="web-portal"

echo "=========================================="
echo "🔄 COMPREHENSIVE VPS SYNC"
echo "=========================================="
echo ""
echo "VPS: ${VPS_USER}@${VPS_IP}"
echo "Remote Path: ${VPS_PATH}"
echo "Local Path: ${LOCAL_PATH}"
echo ""

# Check if paramiko is available
if ! python3 -c "import paramiko" 2>/dev/null; then
    echo "Installing paramiko..."
    pip3 install paramiko --user 2>/dev/null || {
        echo "❌ Could not install paramiko"
        echo "Install manually: pip3 install paramiko"
        exit 1
    }
fi

python3 << 'PYTHON_SCRIPT'
import paramiko
from pathlib import Path
import sys
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_PATH = "/opt/secure-vpn/web-portal"
LOCAL_PATH = Path("web-portal")

def ensure_remote_dir(ssh, remote_path):
    """Ensure remote directory exists"""
    try:
        ssh.exec_command(f"mkdir -p {remote_path}")
    except:
        pass

def sync_file(sftp, local_file, remote_file, ssh):
    """Sync a single file"""
    try:
        # Ensure remote directory exists
        remote_dir = "/".join(remote_file.split("/")[:-1])
        ensure_remote_dir(ssh, remote_dir)
        
        # Upload file
        sftp.put(str(local_file), remote_file)
        return True
    except Exception as e:
        print(f"   ❌ Error syncing {local_file.name}: {e}")
        return False

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    
    sftp = ssh.open_sftp()
    
    # Files to sync
    files_synced = 0
    files_failed = 0
    
    # 1. Sync all Python files
    print("\n[1/6] Syncing Python files...")
    python_files = [
        'app.py',
        'mysql_db.py',
        'email_api.py',
        'email_smtp.py',
        'email_mailjet.py',
        'email_outlook_oauth2.py',
        'email_util.py',
        'payment_integrations.py',
        'payment_integrations_secure.py',
        'file_locking.py',
        'rate_limiting.py',
        'secure_auth.py',
        'generate_all_protocols.py',
        'mysql_migration.py',
        'outlook_oauth2_config.py',
        'smtp_config.py',
    ]
    
    for py_file in python_files:
        local_file = LOCAL_PATH / py_file
        if local_file.exists():
            remote_file = f"{VPS_PATH}/{py_file}"
            if sync_file(sftp, local_file, remote_file, ssh):
                print(f"   ✅ {py_file}")
                files_synced += 1
            else:
                files_failed += 1
        else:
            print(f"   ⚠️  {py_file} not found locally")
    
    # 2. Sync requirements.txt
    print("\n[2/6] Syncing requirements.txt...")
    req_file = LOCAL_PATH / 'requirements.txt'
    if req_file.exists():
        if sync_file(sftp, req_file, f"{VPS_PATH}/requirements.txt", ssh):
            print("   ✅ requirements.txt")
            files_synced += 1
        else:
            files_failed += 1
    
    # 3. Sync all templates
    print("\n[3/6] Syncing templates...")
    templates_dir = LOCAL_PATH / "templates"
    if templates_dir.exists():
        template_count = 0
        for template_file in templates_dir.rglob("*.html"):
            relative_path = template_file.relative_to(templates_dir)
            remote_path = f"{VPS_PATH}/templates/{relative_path}"
            
            if sync_file(sftp, template_file, remote_path, ssh):
                template_count += 1
                files_synced += 1
            else:
                files_failed += 1
        
        # Also sync sitemap.xml if it exists
        sitemap = templates_dir / "sitemap.xml"
        if sitemap.exists():
            if sync_file(sftp, sitemap, f"{VPS_PATH}/templates/sitemap.xml", ssh):
                template_count += 1
                files_synced += 1
        
        print(f"   ✅ Synced {template_count} templates")
    
    # 4. Sync all static files (CSS, JS, images)
    print("\n[4/6] Syncing static files...")
    static_dir = LOCAL_PATH / "static"
    if static_dir.exists():
        static_count = 0
        for static_file in static_dir.rglob("*"):
            if static_file.is_file():
                relative_path = static_file.relative_to(static_dir)
                remote_path = f"{VPS_PATH}/static/{relative_path}"
                
                if sync_file(sftp, static_file, remote_path, ssh):
                    static_count += 1
                    files_synced += 1
                else:
                    files_failed += 1
        
        print(f"   ✅ Synced {static_count} static files")
    
    # 5. Sync configuration files (if they exist)
    print("\n[5/6] Syncing configuration files...")
    config_files = [
        'nginx-phazevpn.conf',
        'phazevpn-portal.service',
        'pyrightconfig.json',
    ]
    
    config_count = 0
    for config_file in config_files:
        local_file = LOCAL_PATH / config_file
        if local_file.exists():
            remote_file = f"{VPS_PATH}/{config_file}"
            if sync_file(sftp, local_file, remote_file, ssh):
                print(f"   ✅ {config_file}")
                config_count += 1
                files_synced += 1
            else:
                files_failed += 1
    
    # 6. Sync scripts directory
    print("\n[6/6] Syncing scripts directory...")
    scripts_dir = LOCAL_PATH / "scripts"
    if scripts_dir.exists():
        script_count = 0
        for script_file in scripts_dir.rglob("*.sh"):
            relative_path = script_file.relative_to(scripts_dir)
            remote_path = f"{VPS_PATH}/scripts/{relative_path}"
            
            if sync_file(sftp, script_file, remote_path, ssh):
                script_count += 1
                files_synced += 1
            else:
                files_failed += 1
        
        print(f"   ✅ Synced {script_count} scripts")
    
    sftp.close()
    
    # Restart web service
    print("\n[7/7] Restarting web service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl restart phazevpn-web 2>&1 || systemctl restart secure-vpn-portal 2>&1 || true")
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        print("   ✅ Web service restarted")
    else:
        error = stderr.read().decode().strip()
        if error:
            print(f"   ⚠️  Restart had issues: {error}")
        else:
            print("   ✅ Web service restarted (or not running)")
    
    # Check service status
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1 || systemctl is-active secure-vpn-portal 2>&1 || echo 'not-found'")
    status = stdout.read().decode().strip()
    if status == "active":
        print("   ✅ Web service is active")
    elif status != "not-found":
        print(f"   ⚠️  Web service status: {status}")
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("✅ SYNC COMPLETE!")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   Files synced: {files_synced}")
    if files_failed > 0:
        print(f"   Files failed: {files_failed}")
    print(f"\n🌐 Site should be updated at:")
    print(f"   https://phazevpn.duckdns.org")
    print(f"   http://{VPS_IP}")
    
except Exception as e:
    print(f"\n❌ Sync failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "✅ Comprehensive sync complete!"
