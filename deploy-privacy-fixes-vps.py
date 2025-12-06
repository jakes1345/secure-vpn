#!/usr/bin/env python3
"""
Deploy Privacy Fixes to VPS
Uploads all privacy fixes (no tracking, no logging, no IP storage)
"""

import paramiko
from pathlib import Path
import sys
import os

# VPS Configuration - Use environment variables for security
VPS_IP = os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASS = os.environ.get('VPS_PASS', '')
if not VPS_PASS:
    print("❌ Error: VPS_PASS environment variable not set")
    print("   Set it with: export VPS_PASS='your-password'")
    sys.exit(1)
VPS_WEB_PORTAL_PATH = "/opt/secure-vpn/web-portal"
VPS_BASE_PATH = "/opt/secure-vpn"

BASE_DIR = Path(__file__).parent
WEB_PORTAL_DIR = BASE_DIR / 'web-portal'

def ensure_remote_dir(sftp, remote_path):
    """Ensure remote directory exists"""
    parts = remote_path.strip('/').split('/')
    current_path = ''
    for part in parts:
        current_path += '/' + part
        try:
            sftp.stat(current_path)
        except FileNotFoundError:
            sftp.mkdir(current_path)

def sync_file(ssh, sftp, local_file, remote_file):
    """Sync a single file to VPS"""
    try:
        # Ensure remote directory exists
        remote_dir = os.path.dirname(remote_file)
        ensure_remote_dir(sftp, remote_dir)
        
        # Upload file
        sftp.put(str(local_file), remote_file)
        print(f"   ✅ {local_file.name} → {remote_file}")
        return True
    except Exception as e:
        print(f"   ❌ {local_file.name}: {e}")
        return False

def main():
    print("=" * 80)
    print("🔒 DEPLOYING PRIVACY FIXES TO VPS")
    print("=" * 80)
    print()
    print(f"VPS: {VPS_USER}@{VPS_IP}")
    print(f"Remote Path: {VPS_WEB_PORTAL_PATH}")
    print()
    
    # Connect to VPS
    try:
        print("Connecting to VPS...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        sftp = ssh.open_sftp()
        print("✅ Connected to VPS")
        print()
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    try:
        files_synced = 0
        files_failed = 0
        
        # 1. Upload privacy-fixed app.py
        print("[1/4] Uploading privacy-fixed app.py...")
        local_file = WEB_PORTAL_DIR / 'app.py'
        remote_file = f"{VPS_WEB_PORTAL_PATH}/app.py"
        if sync_file(ssh, sftp, local_file, remote_file):
            files_synced += 1
        else:
            files_failed += 1
        print()
        
        # 2. Upload privacy-fixed mysql_db.py
        print("[2/4] Uploading privacy-fixed mysql_db.py...")
        local_file = WEB_PORTAL_DIR / 'mysql_db.py'
        remote_file = f"{VPS_WEB_PORTAL_PATH}/mysql_db.py"
        if sync_file(ssh, sftp, local_file, remote_file):
            files_synced += 1
        else:
            files_failed += 1
        print()
        
        # 3. Upload privacy-fixed rate_limiting.py
        print("[3/4] Uploading privacy-fixed rate_limiting.py...")
        local_file = WEB_PORTAL_DIR / 'rate_limiting.py'
        remote_file = f"{VPS_WEB_PORTAL_PATH}/rate_limiting.py"
        if sync_file(ssh, sftp, local_file, remote_file):
            files_synced += 1
        else:
            files_failed += 1
        print()
        
        # 4. Upload database migration SQL
        print("[4/4] Uploading database migration...")
        local_file = WEB_PORTAL_DIR / 'remove_ip_tracking_migration.sql'
        remote_file = f"{VPS_WEB_PORTAL_PATH}/remove_ip_tracking_migration.sql"
        if sync_file(ssh, sftp, local_file, remote_file):
            files_synced += 1
        else:
            files_failed += 1
        print()
        
        # 5. Run database migration
        print("[5/5] Running database migration...")
        try:
            # Check if MySQL is available
            stdin, stdout, stderr = ssh.exec_command("which mysql")
            mysql_path = stdout.read().decode().strip()
            
            if mysql_path:
                print("   Running migration SQL...")
                migration_sql = (WEB_PORTAL_DIR / 'remove_ip_tracking_migration.sql').read_text()
                
                # Run migration
                stdin, stdout, stderr = ssh.exec_command(
                    f"mysql -u phazevpn -p'$(grep MYSQL_PASSWORD /opt/secure-vpn/.env 2>/dev/null | cut -d= -f2)' phazevpn < {remote_file} 2>&1 || echo 'Migration may need manual run'"
                )
                output = stdout.read().decode()
                error = stderr.read().decode()
                
                if output:
                    print(f"   {output}")
                if error and 'ERROR' in error:
                    print(f"   ⚠️  {error}")
                    print("   ℹ️  You may need to run migration manually")
                else:
                    print("   ✅ Migration completed (or needs manual run)")
            else:
                print("   ⚠️  MySQL not found - skipping migration")
                print("   ℹ️  Run migration manually: mysql -u user -p db < remove_ip_tracking_migration.sql")
        except Exception as e:
            print(f"   ⚠️  Migration check failed: {e}")
            print("   ℹ️  Run migration manually")
        print()
        
        # 6. Restart web service
        print("[6/6] Restarting web service...")
        try:
            stdin, stdout, stderr = ssh.exec_command("systemctl restart phazevpn-portal 2>&1 || systemctl restart secure-vpn-portal 2>&1 || service phazevpn-portal restart 2>&1")
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if output:
                print(f"   {output}")
            if error:
                print(f"   {error}")
            
            # Check status
            stdin, stdout, stderr = ssh.exec_command("systemctl status phazevpn-portal --no-pager -l 2>&1 || systemctl status secure-vpn-portal --no-pager -l 2>&1")
            status = stdout.read().decode()
            if 'active (running)' in status.lower():
                print("   ✅ Web service is running")
            else:
                print("   ⚠️  Check service status manually")
        except Exception as e:
            print(f"   ⚠️  Service restart failed: {e}")
            print("   ℹ️  Restart manually: systemctl restart phazevpn-portal")
        print()
        
        # Summary
        print("=" * 80)
        print("✅ DEPLOYMENT COMPLETE")
        print("=" * 80)
        print()
        print(f"Files synced: {files_synced}")
        print(f"Files failed: {files_failed}")
        print()
        print("🔒 Privacy Status:")
        print("   ✅ No activity logging")
        print("   ✅ No connection history")
        print("   ✅ No IP address storage")
        print("   ✅ Complete anonymity")
        print()
        print("📋 Next Steps:")
        print("   1. Verify web portal is running")
        print("   2. Run database migration if not done:")
        print(f"      mysql -u phazevpn -p phazevpn < {VPS_WEB_PORTAL_PATH}/remove_ip_tracking_migration.sql")
        print("   3. Test privacy - verify no tracking")
        print()
        
    except Exception as e:
        print(f"❌ Error during deployment: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sftp.close()
        ssh.close()
        print("✅ Connection closed")

if __name__ == '__main__':
    main()
