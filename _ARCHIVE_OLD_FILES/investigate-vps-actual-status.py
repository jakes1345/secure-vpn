#!/usr/bin/env python3
"""
Deep Dive VPS Investigation
SSH into VPS and check what's actually deployed
"""

import paramiko
import sys
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description=""):
    """Run command on VPS and return output"""
    if description:
        print(f"\n{'='*80}")
        print(f"🔍 {description}")
        print('='*80)
    
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if exit_status == 0:
        print(output)
        return True, output
    else:
        print(f"⚠️  Exit code: {exit_status}")
        if error:
            print(f"Error: {error}")
        if output:
            print(f"Output: {output}")
        return False, output

def check_service(ssh, service_name):
    """Check if a service is running"""
    success, output = run_command(
        ssh,
        f"systemctl is-active {service_name} 2>&1",
        f"Service: {service_name}"
    )
    if "active" in output.lower():
        print(f"   ✅ {service_name} is RUNNING")
        return True
    else:
        print(f"   ❌ {service_name} is NOT RUNNING")
        return False

def check_directory(ssh, path, description=""):
    """Check if directory exists and list contents"""
    desc = description or f"Directory: {path}"
    success, output = run_command(
        ssh,
        f"test -d {path} && echo 'EXISTS' && ls -lah {path} | head -20 || echo 'NOT FOUND'",
        desc
    )
    if "EXISTS" in output:
        print(f"   ✅ Directory exists")
        return True
    else:
        print(f"   ❌ Directory does NOT exist")
        return False

def check_file(ssh, path, description=""):
    """Check if file exists"""
    desc = description or f"File: {path}"
    success, output = run_command(
        ssh,
        f"test -f {path} && echo 'EXISTS' && ls -lh {path} || echo 'NOT FOUND'",
        desc
    )
    if "EXISTS" in output:
        print(f"   ✅ File exists")
        return True
    else:
        print(f"   ❌ File does NOT exist")
        return False

def check_port(ssh, port, protocol="tcp"):
    """Check if port is listening"""
    success, output = run_command(
        ssh,
        f"ss -tlnp | grep ':{port}' || netstat -tlnp 2>/dev/null | grep ':{port}' || echo 'NOT LISTENING'",
        f"Port {port} ({protocol.upper()})"
    )
    if "LISTEN" in output or ":" + str(port) in output:
        print(f"   ✅ Port {port} is LISTENING")
        return True
    else:
        print(f"   ❌ Port {port} is NOT listening")
        return False

def main():
    print("="*80)
    print("🔍 DEEP DIVE VPS INVESTIGATION")
    print("="*80)
    print(f"VPS: {VPS_USER}@{VPS_IP}")
    print("")
    
    # Connect to VPS
    print("📡 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        sys.exit(1)
    
    results = {
        'services': {},
        'directories': {},
        'files': {},
        'ports': {}
    }
    
    # ============================================================
    # 1. CHECK SERVICES
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  CHECKING SERVICES")
    print("="*80)
    
    services_to_check = [
        'phazevpn-portal',
        'phazevpn-email-service',
        'phazevpn-web',
        'openvpn@server',
        'openvpn',
        'phaze-vpn',
        'nginx',
        'postfix',
        'dovecot',
        'fail2ban',
        'phazevpn-protocol'
    ]
    
    for service in services_to_check:
        results['services'][service] = check_service(ssh, service)
    
    # ============================================================
    # 2. CHECK DIRECTORIES
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  CHECKING DIRECTORIES")
    print("="*80)
    
    directories_to_check = [
        '/opt/secure-vpn',
        '/opt/phaze-vpn',
        '/opt/phazevpn-email',
        '/opt/phazebrowser',
        '/opt/secure-vpn/web-portal',
        '/opt/phaze-vpn/web-portal',
        '/opt/secure-vpn/config',
        '/opt/secure-vpn/scripts',
        '/opt/secure-vpn/client-configs',
        '/opt/secure-vpn/logs',
        '/opt/phazevpn-email/email-service-api',
        '/opt/phazebrowser/src'
    ]
    
    for directory in directories_to_check:
        results['directories'][directory] = check_directory(ssh, directory)
    
    # ============================================================
    # 3. CHECK CRITICAL FILES
    # ============================================================
    print("\n" + "="*80)
    print("3️⃣  CHECKING CRITICAL FILES")
    print("="*80)
    
    files_to_check = [
        # VPN Files
        '/opt/secure-vpn/config/server.conf',
        '/opt/secure-vpn/vpn-manager.py',
        '/opt/phaze-vpn/config/server.conf',
        
        # Security Scripts
        '/opt/secure-vpn/scripts/up-ultimate-security.sh',
        '/opt/secure-vpn/scripts/down-ultimate-security.sh',
        '/opt/secure-vpn/scripts/setup-ddos-protection.sh',
        '/opt/secure-vpn/scripts/monitor-ddos.sh',
        '/opt/secure-vpn/scripts/enhance-privacy.sh',
        '/opt/secure-vpn/scripts/setup-vpn-ipv6.sh',
        
        # Web Portal
        '/opt/secure-vpn/web-portal/app.py',
        '/opt/phaze-vpn/web-portal/app.py',
        
        # Email Service
        '/opt/phazevpn-email/email-service-api/app.py',
        '/opt/phazevpn-email/setup-email-server-core.sh',
        
        # Browser
        '/opt/phazebrowser/phazebrowser-modern.py',
        '/opt/phazebrowser/src/phazebrowser-webkit.py',
        '/opt/phazebrowser/vpn/vpn_manager.py'
    ]
    
    for file_path in files_to_check:
        results['files'][file_path] = check_file(ssh, file_path)
    
    # ============================================================
    # 4. CHECK PORTS
    # ============================================================
    print("\n" + "="*80)
    print("4️⃣  CHECKING LISTENING PORTS")
    print("="*80)
    
    ports_to_check = [
        (22, 'tcp', 'SSH'),
        (80, 'tcp', 'HTTP'),
        (443, 'tcp', 'HTTPS'),
        (1194, 'udp', 'OpenVPN'),
        (5000, 'tcp', 'Web Portal'),
        (5005, 'tcp', 'Email API'),
        (25, 'tcp', 'SMTP'),
        (587, 'tcp', 'SMTP Submission'),
        (143, 'tcp', 'IMAP'),
        (993, 'tcp', 'IMAPS'),
        (51820, 'udp', 'PhazeVPN Protocol')
    ]
    
    for port, protocol, name in ports_to_check:
        results['ports'][f"{port}/{protocol}"] = check_port(ssh, port, protocol)
    
    # ============================================================
    # 5. CHECK WEB PORTAL SPECIFIC
    # ============================================================
    print("\n" + "="*80)
    print("5️⃣  CHECKING WEB PORTAL DETAILS")
    print("="*80)
    
    # Check which directory web portal is actually using
    run_command(ssh, "ps aux | grep gunicorn | grep -v grep", "Gunicorn Process")
    run_command(ssh, "cat /etc/systemd/system/phazevpn-portal.service 2>/dev/null | grep WorkingDirectory || echo 'Service file not found'", "Web Portal Service File")
    
    # Check web portal accessibility
    run_command(ssh, "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/ 2>&1", "Web Portal Local Test")
    
    # ============================================================
    # 6. CHECK VPN CONFIG
    # ============================================================
    print("\n" + "="*80)
    print("6️⃣  CHECKING VPN CONFIGURATION")
    print("="*80)
    
    # Check if security scripts are in server.conf
    run_command(ssh, "grep -E 'up|down' /opt/secure-vpn/config/server.conf 2>/dev/null | head -5 || echo 'Config not found or no up/down scripts'", "VPN Config - Up/Down Scripts")
    
    # Check OpenVPN status
    run_command(ssh, "systemctl status openvpn@server --no-pager 2>&1 | head -15 || systemctl status openvpn --no-pager 2>&1 | head -15 || echo 'OpenVPN service not found'", "OpenVPN Service Status")
    
    # ============================================================
    # 7. CHECK EMAIL SERVICE
    # ============================================================
    print("\n" + "="*80)
    print("7️⃣  CHECKING EMAIL SERVICE")
    print("="*80)
    
    # Check email service status
    run_command(ssh, "systemctl status phazevpn-email-service --no-pager 2>&1 | head -15 || echo 'Email service not found'", "Email Service Status")
    
    # Test email API
    run_command(ssh, "curl -s http://127.0.0.1:5005/api/v1/email/health 2>&1 || echo 'Email API not responding'", "Email API Health Check")
    
    # ============================================================
    # 8. CHECK BROWSER
    # ============================================================
    print("\n" + "="*80)
    print("8️⃣  CHECKING BROWSER")
    print("="*80)
    
    # Check browser files
    run_command(ssh, "du -sh /opt/phazebrowser 2>/dev/null || echo 'Browser directory not found'", "Browser Directory Size")
    run_command(ssh, "du -sh /opt/phazebrowser/src 2>/dev/null || echo 'Browser source not found'", "Browser Source Size")
    run_command(ssh, "ls -la /opt/depot_tools 2>/dev/null | head -5 || echo 'depot_tools not found'", "depot_tools Check")
    
    # ============================================================
    # 9. CHECK NGINX CONFIG
    # ============================================================
    print("\n" + "="*80)
    print("9️⃣  CHECKING NGINX CONFIGURATION")
    print("="*80)
    
    run_command(ssh, "nginx -t 2>&1", "Nginx Config Test")
    run_command(ssh, "ls -la /etc/nginx/sites-enabled/ 2>&1", "Nginx Enabled Sites")
    run_command(ssh, "cat /etc/nginx/sites-enabled/* 2>/dev/null | grep -E 'server_name|proxy_pass' | head -10 || echo 'No nginx configs found'", "Nginx Proxy Config")
    
    # ============================================================
    # 10. SUMMARY
    # ============================================================
    print("\n" + "="*80)
    print("📊 INVESTIGATION SUMMARY")
    print("="*80)
    
    print("\n✅ RUNNING SERVICES:")
    for service, status in results['services'].items():
        if status:
            print(f"   ✅ {service}")
    
    print("\n❌ NOT RUNNING SERVICES:")
    for service, status in results['services'].items():
        if not status:
            print(f"   ❌ {service}")
    
    print("\n✅ EXISTING DIRECTORIES:")
    for directory, status in results['directories'].items():
        if status:
            print(f"   ✅ {directory}")
    
    print("\n❌ MISSING DIRECTORIES:")
    for directory, status in results['directories'].items():
        if not status:
            print(f"   ❌ {directory}")
    
    print("\n✅ EXISTING FILES:")
    for file_path, status in results['files'].items():
        if status:
            print(f"   ✅ {file_path}")
    
    print("\n❌ MISSING FILES:")
    for file_path, status in results['files'].items():
        if not status:
            print(f"   ❌ {file_path}")
    
    print("\n✅ LISTENING PORTS:")
    for port, status in results['ports'].items():
        if status:
            print(f"   ✅ {port}")
    
    print("\n❌ NOT LISTENING PORTS:")
    for port, status in results['ports'].items():
        if not status:
            print(f"   ❌ {port}")
    
    # Close connection
    ssh.close()
    
    print("\n" + "="*80)
    print("✅ INVESTIGATION COMPLETE")
    print("="*80)
    print("\n📝 Check the output above for details on what's actually deployed!")

if __name__ == "__main__":
    main()

