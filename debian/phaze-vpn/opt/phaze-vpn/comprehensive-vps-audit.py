#!/usr/bin/env python3
"""
Comprehensive VPS Audit - Deep Dive Everything
Verifies VPN, Email, Website, Browser, and all integrations
"""

import paramiko
import requests
import time
import json
from pathlib import Path

VPS_IP = '15.204.11.19'
VPS_USER = 'root'
VPS_PASS = 'Jakes1328!@'

def run_vps(ssh, command):
    """Run command on VPS and return output"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status == 0, output, error

def print_section(title):
    """Print formatted section header"""
    print('\n' + '='*70)
    print(f'🔍 {title}')
    print('='*70)

def check_vpn_services(ssh):
    """Check VPN services"""
    print_section('VPN SERVICES AUDIT')
    
    issues = []
    
    # Check OpenVPN service
    print('\n1. OpenVPN Service:')
    success, output, _ = run_vps(ssh, 'systemctl is-active openvpn@server')
    status = output.strip()
    if status == 'active':
        print('✅ OpenVPN service is active')
    else:
        print(f'❌ OpenVPN service is {status}')
        issues.append(f'OpenVPN service: {status}')
    
    # Check OpenVPN port
    print('\n2. OpenVPN Port (1194):')
    success, output, _ = run_vps(ssh, 'netstat -tuln | grep :1194 || ss -tuln | grep :1194')
    if ':1194' in output:
        print('✅ OpenVPN port 1194 is listening')
    else:
        print('❌ OpenVPN port 1194 is NOT listening')
        issues.append('OpenVPN port 1194 not listening')
    
    # Check VPN config directory
    print('\n3. VPN Config Directory:')
    success, output, _ = run_vps(ssh, 'test -d /opt/secure-vpn/client-configs && echo "EXISTS" || echo "NOT_FOUND"')
    if 'EXISTS' in output:
        print('✅ VPN config directory exists')
        # Count configs
        success, count, _ = run_vps(ssh, 'ls -1 /opt/secure-vpn/client-configs/*.ovpn 2>/dev/null | wc -l')
        config_count = count.strip()
        print(f'   Found {config_count} client configs')
    else:
        print('❌ VPN config directory NOT found')
        issues.append('VPN config directory missing')
    
    # Check users.json
    print('\n4. Users Database:')
    success, output, _ = run_vps(ssh, 'test -f /opt/secure-vpn/users.json && echo "EXISTS" || echo "NOT_FOUND"')
    if 'EXISTS' in output:
        print('✅ users.json exists')
        # Check if it's valid JSON
        success, content, _ = run_vps(ssh, 'cat /opt/secure-vpn/users.json')
        try:
            users = json.loads(content)
            user_count = len([u for u in users if isinstance(users[u], dict)])
            print(f'   Found {user_count} users')
        except:
            print('⚠️  users.json is not valid JSON')
            issues.append('users.json invalid JSON')
    else:
        print('❌ users.json NOT found')
        issues.append('users.json missing')
    
    return issues

def check_email_system(ssh):
    """Check email system"""
    print_section('EMAIL SYSTEM AUDIT')
    
    issues = []
    
    # Check email files exist
    print('\n1. Email Module Files:')
    email_files = [
        '/opt/phaze-vpn/web-portal/email_api.py',
        '/opt/phaze-vpn/web-portal/email_smtp.py',
    ]
    for file_path in email_files:
        success, output, _ = run_vps(ssh, f'test -f {file_path} && echo "EXISTS" || echo "NOT_FOUND"')
        if 'EXISTS' in output:
            print(f'✅ {Path(file_path).name} exists')
        else:
            print(f'❌ {Path(file_path).name} NOT found')
            issues.append(f'{Path(file_path).name} missing')
    
    # Check SMTP configuration
    print('\n2. SMTP Configuration:')
    success, output, _ = run_vps(ssh, 'grep -E "SMTP_HOST|SMTP_USER|SMTP_PASSWORD" /etc/systemd/system/phazevpn-portal.service | head -5')
    if 'SMTP_HOST' in output:
        print('✅ SMTP environment variables configured')
        if 'smtp.gmail.com' in output:
            print('   Using Gmail SMTP')
    else:
        print('❌ SMTP configuration missing')
        issues.append('SMTP not configured')
    
    # Check email_api imports
    print('\n3. Email Module Syntax:')
    success, output, _ = run_vps(ssh, 'cd /opt/phaze-vpn/web-portal && python3 -c "from email_api import send_verification_email; print(\"SUCCESS\")" 2>&1')
    if 'SUCCESS' in output:
        print('✅ email_api.py imports successfully')
    else:
        print(f'❌ email_api.py import failed: {output[:500]}')
        issues.append('email_api.py import error')
    
    # Check for local paths in email files
    print('\n4. Local Path Check:')
    success, output, _ = run_vps(ssh, 'grep -r "/media/jack\\|/root" /opt/phaze-vpn/web-portal/email*.py 2>/dev/null')
    if output.strip():
        print('❌ Local paths found in email files:')
        print(output[:500])
        issues.append('Local paths in email files')
    else:
        print('✅ No local paths in email files')
    
    return issues

def check_website(ssh):
    """Check website"""
    print_section('WEBSITE AUDIT')
    
    issues = []
    
    # Check web portal service
    print('\n1. Web Portal Service:')
    success, output, _ = run_vps(ssh, 'systemctl is-active phazevpn-portal')
    status = output.strip()
    if status == 'active':
        print('✅ Web portal service is active')
    else:
        print(f'❌ Web portal service is {status}')
        issues.append(f'Web portal service: {status}')
    
    # Check gunicorn processes
    print('\n2. Gunicorn Workers:')
    success, output, _ = run_vps(ssh, 'ps aux | grep gunicorn | grep worker | wc -l')
    worker_count = int(output.strip())
    if worker_count > 0:
        print(f'✅ Gunicorn running ({worker_count} workers)')
    else:
        print('❌ Gunicorn NOT running')
        issues.append('Gunicorn not running')
    
    # Check app.py syntax
    print('\n3. App.py Syntax:')
    success, output, _ = run_vps(ssh, 'cd /opt/phaze-vpn/web-portal && python3 -m py_compile app.py 2>&1')
    if success and not output.strip():
        print('✅ app.py has no syntax errors')
    else:
        print(f'❌ app.py syntax errors: {output[:500]}')
        issues.append('app.py syntax errors')
    
    # Check app imports
    print('\n4. App Import:')
    success, output, _ = run_vps(ssh, 'cd /opt/phaze-vpn/web-portal && python3 -c "from app import app; print(\"SUCCESS\")" 2>&1')
    if 'SUCCESS' in output:
        print('✅ app.py imports successfully')
    else:
        print(f'❌ app.py import failed: {output[:1000]}')
        issues.append('app.py import error')
    
    # Check templates
    print('\n5. Templates:')
    templates = [
        'base.html',
        'home.html',
        'login.html',
        'signup.html',
        'dashboard.html',
    ]
    for template in templates:
        success, output, _ = run_vps(ssh, f'test -f /opt/phaze-vpn/web-portal/templates/{template} && echo "EXISTS" || echo "NOT_FOUND"')
        if 'EXISTS' in output:
            print(f'✅ {template} exists')
        else:
            print(f'❌ {template} NOT found')
            issues.append(f'Template {template} missing')
    
    # Check static files
    print('\n6. Static Files:')
    success, output, _ = run_vps(ssh, 'test -d /opt/phaze-vpn/web-portal/static && echo "EXISTS" || echo "NOT_FOUND"')
    if 'EXISTS' in output:
        print('✅ Static directory exists')
        success, output, _ = run_vps(ssh, 'ls -1 /opt/phaze-vpn/web-portal/static/css/*.css 2>/dev/null | wc -l')
        css_count = output.strip()
        print(f'   Found {css_count} CSS files')
    else:
        print('❌ Static directory NOT found')
        issues.append('Static directory missing')
    
    # Check for local paths
    print('\n7. Local Path Check:')
    success, output, _ = run_vps(ssh, 'grep -r "/media/jack\\|/root" /opt/phaze-vpn/web-portal/*.py /opt/phaze-vpn/web-portal/templates/*.html 2>/dev/null | head -10')
    if output.strip():
        print('❌ Local paths found:')
        print(output[:1000])
        issues.append('Local paths in web portal')
    else:
        print('✅ No local paths found')
    
    # Test website routes
    print('\n8. Website Routes:')
    routes = [
        ('/', 'Homepage'),
        ('/login', 'Login'),
        ('/signup', 'Signup'),
        ('/pricing', 'Pricing'),
        ('/download', 'Download'),
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
            issues.append(f'Route {route} returns {status}')
    
    return issues

def check_browser(ssh):
    """Check PhazeBrowser"""
    print_section('PHAZEBROWSER AUDIT')
    
    issues = []
    
    # Check browser directory
    print('\n1. Browser Directory:')
    success, output, _ = run_vps(ssh, 'test -d /opt/phaze-vpn/phazebrowser && echo "EXISTS" || echo "NOT_FOUND"')
    if 'EXISTS' in output:
        print('✅ Browser directory exists')
    else:
        print('❌ Browser directory NOT found')
        issues.append('Browser directory missing')
    
    # Check browser files
    print('\n2. Browser Files:')
    browser_files = [
        'phazebrowser-modern.py',
        'src/phazebrowser.py',
    ]
    for file_path in browser_files:
        success, output, _ = run_vps(ssh, f'test -f /opt/phaze-vpn/phazebrowser/{file_path} && echo "EXISTS" || echo "NOT_FOUND"')
        if 'EXISTS' in output:
            print(f'✅ {Path(file_path).name} exists')
        else:
            print(f'❌ {Path(file_path).name} NOT found')
            issues.append(f'Browser file {file_path} missing')
    
    # Check SearXNG
    print('\n3. SearXNG Search Engine:')
    # Docker not used - SearXNG would be installed natively if needed
    output = "NOT_RUNNING"
    if 'searxng' in output.lower() and 'NOT_RUNNING' not in output:
        print('✅ SearXNG container is running')
        # Check port
        # Docker not used
        output = "NO_PORT"
        if 'NO_PORT' not in output:
            print(f'   Running on port: {output.strip()}')
    else:
        print('❌ SearXNG container NOT running')
        issues.append('SearXNG not running')
    
    # Check browser search engine config
    print('\n4. Browser Search Engine Config:')
    success, output, _ = run_vps(ssh, 'grep -n "searxng\\|15.204.11.19:8080" /opt/phaze-vpn/phazebrowser/phazebrowser-modern.py | head -5')
    if 'searxng' in output.lower() or '15.204.11.19:8080' in output:
        print('✅ Browser configured to use SearXNG')
    else:
        print('⚠️  Browser may not be using SearXNG')
        issues.append('Browser not configured for SearXNG')
    
    # Check for local paths in browser
    print('\n5. Local Path Check:')
    success, output, _ = run_vps(ssh, 'grep -r "/media/jack\\|/root" /opt/phaze-vpn/phazebrowser/*.py 2>/dev/null | head -5')
    if output.strip():
        print('❌ Local paths found in browser files:')
        print(output[:500])
        issues.append('Local paths in browser files')
    else:
        print('✅ No local paths in browser files')
    
    return issues

def check_integrations(ssh):
    """Check integrations and dependencies"""
    print_section('INTEGRATIONS & DEPENDENCIES AUDIT')
    
    issues = []
    
    # Check Python packages
    print('\n1. Python Dependencies:')
    packages = ['flask', 'bcrypt', 'paramiko', 'qrcode']
    for package in packages:
        success, output, _ = run_vps(ssh, f'python3 -c "import {package}; print(\"SUCCESS\")" 2>&1')
        if 'SUCCESS' in output:
            print(f'✅ {package} installed')
        else:
            print(f'❌ {package} NOT installed')
            issues.append(f'Python package {package} missing')
    
    # Check Nginx
    print('\n2. Nginx:')
    success, output, _ = run_vps(ssh, 'systemctl is-active nginx')
    status = output.strip()
    if status == 'active':
        print('✅ Nginx is active')
    else:
        print(f'❌ Nginx is {status}')
        issues.append(f'Nginx: {status}')
    
    # Check Nginx config
    print('\n3. Nginx Configuration:')
    success, output, _ = run_vps(ssh, 'test -f /etc/nginx/sites-enabled/phazevpn && echo "EXISTS" || echo "NOT_FOUND"')
    if 'EXISTS' in output:
        print('✅ Nginx config exists')
    else:
        print('❌ Nginx config NOT found')
        issues.append('Nginx config missing')
    
    # Check SSL certificates
    print('\n4. SSL Certificates:')
    success, output, _ = run_vps(ssh, 'test -f /etc/letsencrypt/live/phazevpn.com/fullchain.pem && echo "EXISTS" || echo "NOT_FOUND"')
    if 'EXISTS' in output:
        print('✅ SSL certificate exists')
    else:
        print('⚠️  SSL certificate NOT found (may use self-signed)')
    
    # Docker not used - using native systemd services instead
    print('\n5. Docker:')
    print('   ℹ️  Docker not used - using native systemd services')
    
    return issues

def main():
    print('='*70)
    print('🔍 COMPREHENSIVE VPS AUDIT - DEEP DIVE')
    print('='*70)
    print('Verifying: VPN, Email, Website, Browser, Integrations')
    print('='*70)
    
    # Connect to VPS
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    except Exception as e:
        print(f"❌ Failed to connect to VPS: {e}")
        return
    
    all_issues = []
    
    try:
        # Run all audits
        all_issues.extend(check_vpn_services(ssh))
        all_issues.extend(check_email_system(ssh))
        all_issues.extend(check_website(ssh))
        all_issues.extend(check_browser(ssh))
        all_issues.extend(check_integrations(ssh))
        
        # Final summary
        print('\n' + '='*70)
        print('📊 AUDIT SUMMARY')
        print('='*70)
        
        if not all_issues:
            print('✅✅✅ ALL SYSTEMS OPERATIONAL! ✅✅✅')
            print('✅ No issues found')
            print('✅ All services running')
            print('✅ All files present')
            print('✅ No syntax errors')
            print('✅ No local paths')
            print('✅ Everything on VPS')
        else:
            print(f'❌ Found {len(all_issues)} issues:')
            for i, issue in enumerate(all_issues, 1):
                print(f'   {i}. {issue}')
        
        print('='*70)
        
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

