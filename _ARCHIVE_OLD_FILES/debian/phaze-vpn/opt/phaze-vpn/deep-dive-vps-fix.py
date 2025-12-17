#!/usr/bin/env python3
"""
DEEP DIVE VPS FIX - Find and fix EVERYTHING
Goes back to basics and verifies everything works
"""

import paramiko
import time
import json
from pathlib import Path

VPS_IP = '15.204.11.19'
VPS_USER = 'root'
VPS_PASS = 'Jakes1328!@'

def run_vps(ssh, command):
    """Run command on VPS"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status == 0, output, error

def print_section(title):
    print('\n' + '='*70)
    print(f'🔍 {title}')
    print('='*70)

def main():
    print('='*70)
    print('🔍 DEEP DIVE VPS FIX - FROM THE BEGINNING')
    print('='*70)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    try:
        # STEP 1: Kill EVERYTHING
        print_section('STEP 1: KILLING ALL PROCESSES')
        print('Killing all gunicorn processes...')
        run_vps(ssh, 'pkill -9 -f gunicorn')
        time.sleep(2)
        print('Killing all python processes on port 5000...')
        run_vps(ssh, 'fuser -k 5000/tcp 2>/dev/null || lsof -ti :5000 | xargs kill -9 2>/dev/null || true')
        time.sleep(2)
        print('Stopping service...')
        run_vps(ssh, 'systemctl stop phazevpn-portal')
        time.sleep(2)
        
        # Verify port is free
        success, output, _ = run_vps(ssh, 'lsof -i :5000 || echo "PORT_FREE"')
        if 'PORT_FREE' in output or not output.strip():
            print('✅ Port 5000 is free')
        else:
            print(f'⚠️  Port still in use: {output[:200]}')
            # Force kill
            pids = output.split('\n')[1:] if '\n' in output else []
            for line in pids:
                if line.strip():
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        run_vps(ssh, f'kill -9 {pid}')
            time.sleep(2)
        
        # STEP 2: Check Python and dependencies
        print_section('STEP 2: VERIFYING PYTHON ENVIRONMENT')
        success, output, _ = run_vps(ssh, 'python3 --version')
        print(f'Python version: {output.strip()}')
        
        # Check all imports
        imports = [
            'flask',
            'bcrypt',
            'paramiko',
            'qrcode',
            'smtplib',
            'email',
            'json',
            'os',
            'pathlib',
        ]
        for imp in imports:
            success, output, _ = run_vps(ssh, f'python3 -c "import {imp}; print(\"OK\")" 2>&1')
            if 'OK' in output:
                print(f'✅ {imp}')
            else:
                print(f'❌ {imp}: {output[:200]}')
        
        # STEP 3: Check app.py syntax and imports
        print_section('STEP 3: VERIFYING APP.PY')
        
        # Syntax check
        success, output, _ = run_vps(ssh, 'cd /opt/phaze-vpn/web-portal && python3 -m py_compile app.py 2>&1')
        if success and not output.strip():
            print('✅ app.py syntax is valid')
        else:
            print(f'❌ app.py syntax error: {output[:1000]}')
            return
        
        # Try to import app
        success, output, _ = run_vps(ssh, 'cd /opt/phaze-vpn/web-portal && python3 -c "from app import app; print(\"SUCCESS\")" 2>&1')
        if 'SUCCESS' in output:
            print('✅ app.py imports successfully')
        else:
            print(f'❌ app.py import failed:')
            print(output[:2000])
            return
        
        # Check for local paths
        success, output, _ = run_vps(ssh, 'grep -r "/media/jack\\|/root" /opt/phaze-vpn/web-portal/*.py 2>/dev/null')
        if output.strip():
            print('❌ Local paths found:')
            print(output[:1000])
        else:
            print('✅ No local paths in app.py')
        
        # STEP 4: Check email modules
        print_section('STEP 4: VERIFYING EMAIL MODULES')
        
        # email_smtp.py
        success, output, _ = run_vps(ssh, 'cd /opt/phaze-vpn/web-portal && python3 -c "from email_smtp import send_email; print(\"SUCCESS\")" 2>&1')
        if 'SUCCESS' in output:
            print('✅ email_smtp.py imports successfully')
        else:
            print(f'❌ email_smtp.py import failed: {output[:1000]}')
            return
        
        # email_api.py
        success, output, _ = run_vps(ssh, 'cd /opt/phaze-vpn/web-portal && python3 -c "from email_api import send_verification_email; print(\"SUCCESS\")" 2>&1')
        if 'SUCCESS' in output:
            print('✅ email_api.py imports successfully')
        else:
            print(f'❌ email_api.py import failed: {output[:1000]}')
            return
        
        # STEP 5: Check service file
        print_section('STEP 5: VERIFYING SERVICE FILE')
        success, output, _ = run_vps(ssh, 'cat /etc/systemd/system/phazevpn-portal.service')
        service_content = output
        
        # Check critical settings
        checks = {
            'WorkingDirectory=/opt/phaze-vpn/web-portal': 'WorkingDirectory',
            'User=www-data': 'User',
            'Group=www-data': 'Group',
            '--bind 127.0.0.1:5000': 'Bind address',
            'app:app': 'App module',
        }
        
        for check, name in checks.items():
            if check in service_content:
                print(f'✅ {name}: OK')
            else:
                print(f'❌ {name}: Missing or incorrect')
                print(f'   Looking for: {check}')
        
        # Check environment variables
        if 'SMTP_USER' in service_content and 'SMTP_PASSWORD' in service_content:
            print('✅ SMTP environment variables configured')
        else:
            print('⚠️  SMTP environment variables may be missing')
        
        # STEP 6: Test running app directly
        print_section('STEP 6: TESTING APP DIRECTLY')
        
        # Try to run Flask app directly
        print('Testing Flask app startup...')
        stdin, stdout, stderr = ssh.exec_command('cd /opt/phaze-vpn/web-portal && timeout 5 python3 -c "from app import app; print(\"FLASK_APP_OK\")" 2>&1')
        time.sleep(2)
        output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
        if 'FLASK_APP_OK' in output:
            print('✅ Flask app can be imported')
        else:
            print(f'❌ Flask app import issue: {output[:1500]}')
            return
        
        # STEP 7: Check file permissions
        print_section('STEP 7: CHECKING FILE PERMISSIONS')
        
        files_to_check = [
            '/opt/phaze-vpn/web-portal/app.py',
            '/opt/phaze-vpn/web-portal/email_api.py',
            '/opt/phaze-vpn/web-portal/email_smtp.py',
            '/opt/secure-vpn/users.json',
        ]
        
        for file_path in files_to_check:
            success, output, _ = run_vps(ssh, f'test -f {file_path} && ls -l {file_path} || echo "NOT_FOUND"')
            if 'NOT_FOUND' in output:
                print(f'❌ {file_path}: NOT FOUND')
            else:
                print(f'✅ {file_path}: {output.strip()[:80]}')
        
        # STEP 8: Check gunicorn
        print_section('STEP 8: VERIFYING GUNICORN')
        
        success, output, _ = run_vps(ssh, 'which gunicorn')
        if success and output.strip():
            print(f'✅ Gunicorn found: {output.strip()}')
        else:
            print('❌ Gunicorn not found')
            return
        
        # Test gunicorn command
        print('Testing gunicorn command...')
        stdin, stdout, stderr = ssh.exec_command('cd /opt/phaze-vpn/web-portal && timeout 3 /usr/local/bin/gunicorn --check-config app:app 2>&1')
        time.sleep(2)
        output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
        if 'error' not in output.lower() or 'success' in output.lower():
            print('✅ Gunicorn config check passed')
        else:
            print(f'⚠️  Gunicorn config check: {output[:500]}')
        
        # STEP 9: Start service manually to see error
        print_section('STEP 9: STARTING SERVICE MANUALLY')
        
        # Start gunicorn manually with full output
        print('Starting gunicorn manually to capture errors...')
        stdin, stdout, stderr = ssh.exec_command('cd /opt/phaze-vpn/web-portal && /usr/local/bin/gunicorn --workers 1 --bind 127.0.0.1:5000 --timeout 120 --log-level debug app:app 2>&1 &')
        time.sleep(5)
        
        # Check if it's running
        success, output, _ = run_vps(ssh, 'ps aux | grep gunicorn | grep -v grep')
        if 'gunicorn' in output.lower():
            print('✅ Gunicorn process is running')
            
            # Test a route
            time.sleep(2)
            success, output, _ = run_vps(ssh, 'curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/')
            status = output.strip()
            if status == '200':
                print(f'✅ Homepage returns: {status}')
            elif status in ['302', '301']:
                print(f'✅ Homepage redirects: {status}')
            else:
                print(f'❌ Homepage returns: {status}')
                # Get error details
                success, output, _ = run_vps(ssh, 'curl -s http://localhost:5000/ 2>&1 | head -50')
                print(f'Response: {output[:500]}')
        else:
            print('❌ Gunicorn process not running')
            # Get stderr
            stderr_output = stderr.read().decode('utf-8')
            if stderr_output:
                print(f'Error: {stderr_output[:1500]}')
        
        # Kill manual process
        run_vps(ssh, 'pkill -9 -f gunicorn')
        time.sleep(2)
        
        # STEP 10: Fix and restart service
        print_section('STEP 10: FIXING AND RESTARTING SERVICE')
        
        # Reload systemd
        run_vps(ssh, 'systemctl daemon-reload')
        time.sleep(1)
        
        # Start service
        print('Starting phazevpn-portal service...')
        run_vps(ssh, 'systemctl start phazevpn-portal')
        time.sleep(8)
        
        # Check status
        success, output, _ = run_vps(ssh, 'systemctl is-active phazevpn-portal')
        status = output.strip()
        if status == 'active':
            print('✅✅✅ SERVICE IS ACTIVE!')
        else:
            print(f'❌ Service status: {status}')
            # Get detailed logs
            success, output, _ = run_vps(ssh, 'journalctl -u phazevpn-portal --no-pager -n 30')
            print('Recent logs:')
            print(output[:2000])
        
        # STEP 11: Final route test
        print_section('STEP 11: FINAL ROUTE TEST')
        
        routes = [
            ('/', 'Homepage'),
            ('/login', 'Login'),
            ('/signup', 'Signup'),
            ('/pricing', 'Pricing'),
        ]
        
        for route, name in routes:
            success, output, _ = run_vps(ssh, f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:5000{route}')
            status = output.strip()
            if status == '200':
                print(f'✅ {name}: {status}')
            elif status in ['302', '301']:
                print(f'✅ {name}: {status} (redirect)')
            else:
                print(f'❌ {name}: {status}')
        
        print('\n' + '='*70)
        print('✅ DEEP DIVE COMPLETE')
        print('='*70)
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

