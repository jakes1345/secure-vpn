#!/usr/bin/env python3
"""
Automated VPS Update Script
Syncs files and restarts services cleanly without manual intervention
"""

import paramiko
from pathlib import Path
import time
import sys

VPS_IP = '15.204.11.19'
VPS_USER = 'root'
VPS_PASS = 'Jakes1328!@'

BASE_DIR = Path('/opt/phaze-vpn')
REMOTE_BASE = '/opt/phaze-vpn'

def run_vps(ssh, command):
    """Run command on VPS"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status == 0, output, error

def sync_file(sftp, local_file, remote_file):
    """Sync file to VPS"""
    local_path = BASE_DIR / local_file
    if local_path.exists():
        try:
            sftp.put(str(local_path), remote_file)
            return True, f"✅ Synced: {local_path.name}"
        except Exception as e:
            return False, f"❌ Failed to sync {local_path.name}: {e}"
    else:
        return False, f"⚠️  Not found: {local_file}"

def test_endpoint(ssh, route, name):
    """Test HTTP endpoint"""
    success, output, _ = run_vps(ssh, f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:5000{route}')
    if success:
        status_code = output.strip()
        if status_code in ['200', '302', '301']:
            print(f"✅ {name}: {status_code}")
            return True
        else:
            print(f"❌ {name}: {status_code}")
            return False
    return False

def main():
    print('='*70)
    print('🔄 PHASEVPN VPS UPDATE SCRIPT')
    print('='*70)
    
    # Connect to VPS
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    except Exception as e:
        print(f"❌ Failed to connect to VPS: {e}")
        sys.exit(1)
    
    try:
        # Step 1: Clean up old processes
        print('\n1️⃣  CLEANING UP OLD PROCESSES')
        print('-'*70)
        run_vps(ssh, 'pkill -9 -f gunicorn || true')
        run_vps(ssh, 'fuser -k 5000/tcp 2>/dev/null || true')
        time.sleep(2)
        print('✅ Cleaned up processes')
        
        # Step 2: Sync files
        print('\n2️⃣  SYNCING FILES TO VPS')
        print('-'*70)
        sftp = ssh.open_sftp()
        
        files_to_sync = [
            ('debian/phaze-vpn/opt/phaze-vpn/web-portal/app.py', f'{REMOTE_BASE}/web-portal/app.py'),
            ('debian/phaze-vpn/opt/phaze-vpn/web-portal/email_api.py', f'{REMOTE_BASE}/web-portal/email_api.py'),
            ('debian/phaze-vpn/opt/phaze-vpn/web-portal/email_smtp.py', f'{REMOTE_BASE}/web-portal/email_smtp.py'),
            ('debian/phaze-vpn/opt/phaze-vpn/web-portal/templates/base.html', f'{REMOTE_BASE}/web-portal/templates/base.html'),
            ('debian/phaze-vpn/opt/phaze-vpn/web-portal/templates/home.html', f'{REMOTE_BASE}/web-portal/templates/home.html'),
            ('debian/phaze-vpn/opt/phaze-vpn/web-portal/phazevpn-portal.service', '/etc/systemd/system/phazevpn-portal.service'),
        ]
        
        synced_count = 0
        for local_rel, remote_path in files_to_sync:
            success, message = sync_file(sftp, local_rel, remote_path)
            print(message)
            if success:
                synced_count += 1
        
        sftp.close()
        print(f'\n✅ Synced {synced_count}/{len(files_to_sync)} files')
        
        # Step 3: Reload systemd
        print('\n3️⃣  RELOADING SYSTEMD')
        print('-'*70)
        run_vps(ssh, 'systemctl daemon-reload')
        print('✅ Systemd reloaded')
        
        # Step 4: Fix log permissions and restart service
        print('\n4️⃣  FIXING PERMISSIONS & RESTARTING SERVICES')
        print('-'*70)
        run_vps(ssh, 'touch /var/log/phazevpn-portal-error.log /var/log/phazevpn-portal-access.log')
        run_vps(ssh, 'chown www-data:www-data /var/log/phazevpn-portal-error.log /var/log/phazevpn-portal-access.log')
        run_vps(ssh, 'chmod 644 /var/log/phazevpn-portal-error.log /var/log/phazevpn-portal-access.log')
        print('✅ Fixed log file permissions')
        
        run_vps(ssh, 'systemctl stop phazevpn-portal || true')
        time.sleep(2)
        run_vps(ssh, 'systemctl start phazevpn-portal')
        time.sleep(5)
        print('✅ Service restarted')
        
        # Step 5: Verify service status
        print('\n5️⃣  VERIFYING SERVICE STATUS')
        print('-'*70)
        success, output, _ = run_vps(ssh, 'systemctl is-active phazevpn-portal')
        status = output.strip()
        if status == 'active':
            print('✅ Service is active')
        else:
            print(f'❌ Service is not active: {status}')
            print('\nChecking service logs...')
            success, logs, _ = run_vps(ssh, 'journalctl -u phazevpn-portal --no-pager -n 20')
            print(logs[:2000])
            sys.exit(1)
        
        # Step 6: Test endpoints
        print('\n6️⃣  TESTING ENDPOINTS')
        print('-'*70)
        time.sleep(2)
        
        endpoints = [
            ('/', 'Homepage'),
            ('/login', 'Login'),
            ('/signup', 'Signup'),
        ]
        
        all_passed = True
        for route, name in endpoints:
            if not test_endpoint(ssh, route, name):
                all_passed = False
        
        print('\n' + '='*70)
        if all_passed:
            print('✅✅✅ UPDATE COMPLETE - ALL TESTS PASSED! ✅✅✅')
        else:
            print('⚠️  UPDATE COMPLETE - SOME TESTS FAILED')
        print('='*70)
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

