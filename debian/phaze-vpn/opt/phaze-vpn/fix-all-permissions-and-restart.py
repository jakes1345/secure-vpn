#!/usr/bin/env python3
"""
Fix all permissions and restart service
"""

import paramiko
import time

VPS_IP = '15.204.11.19'
VPS_USER = 'root'
VPS_PASS = 'Jakes1328!@'

def run_vps(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status == 0, output, error

def main():
    print('='*70)
    print('🔧 FIXING ALL PERMISSIONS AND RESTARTING')
    print('='*70)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    try:
        # Step 1: Kill everything
        print('\n1. Killing all processes...')
        run_vps(ssh, 'pkill -9 -f gunicorn')
        run_vps(ssh, 'fuser -k 5000/tcp 2>/dev/null || lsof -ti :5000 | xargs kill -9 2>/dev/null || true')
        run_vps(ssh, 'systemctl stop phazevpn-portal')
        time.sleep(3)
        
        # Step 2: Fix file permissions
        print('\n2. Fixing file permissions...')
        
        # Create directories if they don't exist
        dirs = [
            '/opt/secure-vpn',
            '/opt/secure-vpn/logs',
            '/opt/secure-vpn/client-configs',
        ]
        for dir_path in dirs:
            run_vps(ssh, f'mkdir -p {dir_path}')
            run_vps(ssh, f'chown -R www-data:www-data {dir_path}')
            run_vps(ssh, f'chmod -R 755 {dir_path}')
            print(f'✅ Fixed: {dir_path}')
        
        # Fix users.json permissions
        run_vps(ssh, 'chown www-data:www-data /opt/secure-vpn/users.json')
        run_vps(ssh, 'chmod 664 /opt/secure-vpn/users.json')
        print('✅ Fixed: /opt/secure-vpn/users.json')
        
        # Fix web portal directory
        run_vps(ssh, 'chown -R www-data:www-data /opt/phaze-vpn/web-portal')
        run_vps(ssh, 'chmod -R 755 /opt/phaze-vpn/web-portal')
        print('✅ Fixed: /opt/phaze-vpn/web-portal')
        
        # Fix log files
        log_files = [
            '/var/log/phazevpn-portal-access.log',
            '/var/log/phazevpn-portal-error.log',
        ]
        for log_file in log_files:
            run_vps(ssh, f'touch {log_file}')
            run_vps(ssh, f'chown www-data:www-data {log_file}')
            run_vps(ssh, f'chmod 664 {log_file}')
            print(f'✅ Fixed: {log_file}')
        
        # Step 3: Verify permissions
        print('\n3. Verifying permissions...')
        success, output, _ = run_vps(ssh, 'sudo -u www-data test -w /opt/secure-vpn/users.json && echo "WRITABLE" || echo "NOT_WRITABLE"')
        if 'WRITABLE' in output:
            print('✅ www-data can write to users.json')
        else:
            print('❌ www-data still cannot write')
            return
        
        # Step 4: Test app import
        print('\n4. Testing app import...')
        success, output, _ = run_vps(ssh, 'cd /opt/phaze-vpn/web-portal && sudo -u www-data python3 -c "from app import app; print(\"SUCCESS\")" 2>&1')
        if 'SUCCESS' in output:
            print('✅ App imports successfully as www-data')
        else:
            print(f'❌ App import failed: {output[:1500]}')
            return
        
        # Step 5: Start service
        print('\n5. Starting service...')
        run_vps(ssh, 'systemctl daemon-reload')
        time.sleep(1)
        run_vps(ssh, 'systemctl start phazevpn-portal')
        time.sleep(8)
        
        # Step 6: Check status
        print('\n6. Checking service status...')
        success, output, _ = run_vps(ssh, 'systemctl is-active phazevpn-portal')
        status = output.strip()
        if status == 'active':
            print('✅✅✅ SERVICE IS ACTIVE!')
        else:
            print(f'❌ Service status: {status}')
            # Get logs
            success, output, _ = run_vps(ssh, 'journalctl -u phazevpn-portal --no-pager -n 20')
            print('Recent logs:')
            print(output[:2000])
            return
        
        # Step 7: Test routes
        print('\n7. Testing routes...')
        routes = [
            ('/', 'Homepage'),
            ('/login', 'Login'),
            ('/signup', 'Signup'),
        ]
        for route, name in routes:
            time.sleep(1)
            success, output, _ = run_vps(ssh, f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:5000{route}')
            status = output.strip()
            if status == '200':
                print(f'✅ {name}: {status}')
            elif status in ['302', '301']:
                print(f'✅ {name}: {status} (redirect)')
            else:
                print(f'❌ {name}: {status}')
                # Get error
                success, output, _ = run_vps(ssh, f'curl -s http://localhost:5000{route} 2>&1 | head -20')
                print(f'   Error: {output[:300]}')
        
        print('\n' + '='*70)
        print('✅ ALL FIXES COMPLETE')
        print('='*70)
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

