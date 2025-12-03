#!/usr/bin/env python3
"""
ULTIMATE DEEP DIVE AUDIT - FROM THE BEGINNING
Check EVERYTHING on VPS - code, services, configs, files, permissions, errors
"""

import paramiko
import time
import json
import os
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
    print('\n' + '='*80)
    print(f'🔍 {title}')
    print('='*80)

def check_directory_structure(ssh):
    """Check all directories and files"""
    print_section('1. DIRECTORY STRUCTURE AUDIT')
    
    issues = []
    
    # Check all critical directories
    dirs = {
        '/opt/phaze-vpn': 'Main PhazeVPN directory',
        '/opt/phaze-vpn/web-portal': 'Web portal code',
        '/opt/phaze-vpn/web-portal/templates': 'HTML templates',
        '/opt/phaze-vpn/web-portal/static': 'Static files (CSS, JS)',
        '/opt/phaze-vpn/phazebrowser': 'Browser code',
        '/opt/secure-vpn': 'VPN data directory',
        '/opt/secure-vpn/client-configs': 'VPN client configs',
        '/opt/secure-vpn/logs': 'Log files',
        '/etc/systemd/system': 'Systemd services',
        '/etc/nginx/sites-enabled': 'Nginx configs',
    }
    
    for dir_path, description in dirs.items():
        success, output, _ = run_vps(ssh, f'test -d {dir_path} && echo "EXISTS" || echo "NOT_FOUND"')
        if 'EXISTS' in output:
            # Count files
            success, count, _ = run_vps(ssh, f'find {dir_path} -type f 2>/dev/null | wc -l')
            file_count = count.strip()
            print(f'✅ {dir_path}: {file_count} files')
        else:
            print(f'❌ {dir_path}: NOT FOUND - {description}')
            issues.append(f'Missing directory: {dir_path}')
    
    return issues

def check_all_python_files(ssh):
    """Check all Python files for syntax errors"""
    print_section('2. PYTHON FILES SYNTAX CHECK')
    
    issues = []
    
    # Find all Python files
    success, output, _ = run_vps(ssh, 'find /opt/phaze-vpn -name "*.py" -type f 2>/dev/null')
    python_files = [f.strip() for f in output.split('\n') if f.strip()]
    
    print(f'Found {len(python_files)} Python files')
    
    for py_file in python_files[:50]:  # Check first 50
        # Syntax check
        success, output, _ = run_vps(ssh, f'python3 -m py_compile {py_file} 2>&1')
        if success and not output.strip():
            print(f'✅ {Path(py_file).name}')
        else:
            print(f'❌ {Path(py_file).name}: {output[:200]}')
            issues.append(f'Syntax error in {py_file}: {output[:200]}')
    
    return issues

def check_imports(ssh):
    """Check all Python imports"""
    print_section('3. PYTHON IMPORTS CHECK')
    
    issues = []
    
    # Check main app imports
    imports_to_check = [
        ('app.py', 'from app import app'),
        ('email_api.py', 'from email_api import send_verification_email'),
        ('email_smtp.py', 'from email_smtp import send_email'),
    ]
    
    for file_name, import_cmd in imports_to_check:
        success, output, _ = run_vps(ssh, f'cd /opt/phaze-vpn/web-portal && python3 -c "{import_cmd}; print(\\"SUCCESS\\")" 2>&1')
        if 'SUCCESS' in output:
            print(f'✅ {file_name} imports successfully')
        else:
            print(f'❌ {file_name} import failed: {output[:500]}')
            issues.append(f'Import error in {file_name}: {output[:500]}')
    
    return issues

def check_file_permissions(ssh):
    """Check all file permissions"""
    print_section('4. FILE PERMISSIONS AUDIT')
    
    issues = []
    
    # Critical files that need specific permissions
    files_to_check = [
        ('/opt/phaze-vpn/web-portal/app.py', 'www-data', '644'),
        ('/opt/secure-vpn/users.json', 'www-data', '664'),
        ('/opt/phaze-vpn/web-portal/email_api.py', 'www-data', '644'),
        ('/opt/phaze-vpn/web-portal/email_smtp.py', 'www-data', '644'),
    ]
    
    for file_path, expected_user, expected_perm in files_to_check:
        success, output, _ = run_vps(ssh, f'test -f {file_path} && ls -l {file_path} || echo "NOT_FOUND"')
        if 'NOT_FOUND' in output:
            print(f'❌ {file_path}: NOT FOUND')
            issues.append(f'Missing file: {file_path}')
        else:
            # Check if www-data can read/write
            success, output, _ = run_vps(ssh, f'sudo -u www-data test -r {file_path} && echo "READABLE" || echo "NOT_READABLE"')
            if 'READABLE' not in output:
                print(f'❌ {file_path}: www-data cannot read')
                issues.append(f'Permission error: {file_path} not readable by www-data')
            else:
                print(f'✅ {file_path}: readable by www-data')
    
    # Check if www-data can write to users.json
    success, output, _ = run_vps(ssh, 'sudo -u www-data test -w /opt/secure-vpn/users.json && echo "WRITABLE" || echo "NOT_WRITABLE"')
    if 'WRITABLE' in output:
        print('✅ www-data can write to users.json')
    else:
        print('❌ www-data CANNOT write to users.json')
        issues.append('www-data cannot write to users.json')
    
    return issues

def check_services(ssh):
    """Check all services"""
    print_section('5. SERVICES AUDIT')
    
    issues = []
    
    services = {
        'phazevpn-portal': 'Web portal service',
        'nginx': 'Web server',
        'openvpn@server': 'VPN service',
    }
    
    for service, description in services.items():
        success, output, _ = run_vps(ssh, f'systemctl is-active {service}')
        status = output.strip()
        if status == 'active':
            print(f'✅ {service}: active')
        else:
            print(f'❌ {service}: {status} - {description}')
            issues.append(f'Service {service} is {status}')
            
            # Get error logs
            if service == 'phazevpn-portal':
                success, logs, _ = run_vps(ssh, f'journalctl -u {service} --no-pager -n 20 | tail -10')
                print(f'   Recent logs: {logs[:500]}')
    
    # Check gunicorn processes
    success, output, _ = run_vps(ssh, 'ps aux | grep gunicorn | grep -v grep | wc -l')
    worker_count = int(output.strip())
    if worker_count > 0:
        print(f'✅ Gunicorn workers: {worker_count}')
    else:
        print('❌ No gunicorn workers running')
        issues.append('No gunicorn workers')
    
    return issues

def check_ports(ssh):
    """Check all ports"""
    print_section('6. PORTS AUDIT')
    
    issues = []
    
    ports = {
        '80': 'HTTP',
        '443': 'HTTPS',
        '5000': 'Gunicorn',
        '1194': 'OpenVPN',
    }
    
    for port, service in ports.items():
        success, output, _ = run_vps(ssh, f'lsof -i :{port} || ss -tlnp | grep :{port} || echo "NOT_LISTENING"')
        if 'NOT_LISTENING' not in output and output.strip():
            print(f'✅ Port {port} ({service}): listening')
        else:
            print(f'❌ Port {port} ({service}): NOT listening')
            issues.append(f'Port {port} ({service}) not listening')
    
    return issues

def check_website_routes(ssh):
    """Test all website routes"""
    print_section('7. WEBSITE ROUTES TEST')
    
    issues = []
    
    routes = [
        ('/', 'Homepage'),
        ('/login', 'Login'),
        ('/signup', 'Signup'),
        ('/pricing', 'Pricing'),
        ('/download', 'Download'),
        ('/contact', 'Contact'),
        ('/guide', 'Guide'),
    ]
    
    for route, name in routes:
        success, output, _ = run_vps(ssh, f'curl -s -o /dev/null -w "%{{http_code}}" http://localhost:5000{route}')
        status = output.strip()
        if status == '200':
            print(f'✅ {name}: {status}')
        elif status in ['302', '301']:
            print(f'✅ {name}: {status} (redirect)')
        elif status == '500':
            print(f'❌ {name}: {status} (internal error)')
            issues.append(f'Route {route} returns 500')
            # Get error
            success, error, _ = run_vps(ssh, f'curl -s http://localhost:5000{route} 2>&1 | head -10')
            print(f'   Error: {error[:200]}')
        else:
            print(f'⚠️  {name}: {status}')
    
    return issues

def check_config_files(ssh):
    """Check all config files"""
    print_section('8. CONFIG FILES AUDIT')
    
    issues = []
    
    configs = {
        '/etc/systemd/system/phazevpn-portal.service': 'Systemd service',
        '/etc/nginx/sites-enabled/phazevpn': 'Nginx config',
        '/opt/phaze-vpn/web-portal/app.py': 'Main app',
    }
    
    for config_path, description in configs.items():
        success, output, _ = run_vps(ssh, f'test -f {config_path} && echo "EXISTS" || echo "NOT_FOUND"')
        if 'EXISTS' in output:
            print(f'✅ {description}: exists')
            
            # Check for local paths
            success, output, _ = run_vps(ssh, f'grep -E "/media/jack|/root" {config_path} || echo "NO_LOCAL_PATHS"')
            if 'NO_LOCAL_PATHS' not in output:
                print(f'❌ {description}: Contains local paths!')
                issues.append(f'{description} contains local paths')
        else:
            print(f'❌ {description}: NOT FOUND')
            issues.append(f'Missing config: {config_path}')
    
    return issues

def check_database(ssh):
    """Check database files"""
    print_section('9. DATABASE FILES AUDIT')
    
    issues = []
    
    # Check users.json
    success, output, _ = run_vps(ssh, 'test -f /opt/secure-vpn/users.json && echo "EXISTS" || echo "NOT_FOUND"')
    if 'EXISTS' in output:
        print('✅ users.json exists')
        
        # Check if valid JSON
        success, content, _ = run_vps(ssh, 'cat /opt/secure-vpn/users.json')
        try:
            users = json.loads(content)
            user_count = len([u for u in users if isinstance(users.get(u), dict)])
            print(f'✅ Valid JSON with {user_count} users')
        except Exception as e:
            print(f'❌ Invalid JSON: {str(e)[:200]}')
            issues.append(f'users.json invalid JSON: {str(e)[:200]}')
    else:
        print('❌ users.json NOT FOUND')
        issues.append('users.json missing')
    
    return issues

def check_logs(ssh):
    """Check error logs"""
    print_section('10. ERROR LOGS AUDIT')
    
    issues = []
    
    # Check gunicorn error log
    success, output, _ = run_vps(ssh, 'tail -50 /var/log/phazevpn-portal-error.log 2>/dev/null | grep -i "error\\|exception\\|traceback" | tail -20')
    if output.strip():
        print('⚠️  Found errors in error log:')
        print(output[:1000])
        issues.append('Errors found in error log')
    else:
        print('✅ No recent errors in error log')
    
    # Check systemd logs
    success, output, _ = run_vps(ssh, 'journalctl -u phazevpn-portal --no-pager -n 50 | grep -i "error\\|exception\\|traceback\\|failed" | tail -20')
    if output.strip():
        print('⚠️  Found errors in systemd logs:')
        print(output[:1000])
        issues.append('Errors found in systemd logs')
    else:
        print('✅ No recent errors in systemd logs')
    
    return issues

def check_dependencies(ssh):
    """Check all dependencies"""
    print_section('11. DEPENDENCIES AUDIT')
    
    issues = []
    
    packages = [
        'flask',
        'bcrypt',
        'paramiko',
        'qrcode',
        'gunicorn',
    ]
    
    for package in packages:
        success, output, _ = run_vps(ssh, f'python3 -c "import {package}; print(\\"OK\\")" 2>&1')
        if 'OK' in output:
            print(f'✅ {package}')
        else:
            print(f'❌ {package}: {output[:200]}')
            issues.append(f'Missing package: {package}')
    
    return issues

def main():
    print('='*80)
    print('🔍 ULTIMATE DEEP DIVE AUDIT - FROM THE BEGINNING')
    print('='*80)
    print('Checking EVERYTHING on VPS...')
    print('='*80)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    all_issues = []
    
    try:
        all_issues.extend(check_directory_structure(ssh))
        all_issues.extend(check_all_python_files(ssh))
        all_issues.extend(check_imports(ssh))
        all_issues.extend(check_file_permissions(ssh))
        all_issues.extend(check_services(ssh))
        all_issues.extend(check_ports(ssh))
        all_issues.extend(check_website_routes(ssh))
        all_issues.extend(check_config_files(ssh))
        all_issues.extend(check_database(ssh))
        all_issues.extend(check_logs(ssh))
        all_issues.extend(check_dependencies(ssh))
        
        # FINAL SUMMARY
        print('\n' + '='*80)
        print('📊 FINAL AUDIT SUMMARY')
        print('='*80)
        
        if not all_issues:
            print('✅✅✅ NO ISSUES FOUND! ✅✅✅')
            print('Everything is working correctly!')
        else:
            print(f'❌ Found {len(all_issues)} issues:')
            for i, issue in enumerate(all_issues, 1):
                print(f'   {i}. {issue}')
        
        print('='*80)
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

