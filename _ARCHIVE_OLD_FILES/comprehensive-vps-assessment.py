#!/usr/bin/env python3
"""
Comprehensive VPS Assessment
Checks everything that's wrong or needs fixing
"""
import paramiko
import os
from pathlib import Path
import json

VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD', 'Jakes1328!@')

def connect_vps():
    """Connect to VPS using SSH key or password"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key_paths = [
        Path.home() / '.ssh' / 'id_rsa',
        Path.home() / '.ssh' / 'id_ed25519',
    ]
    
    for key_path in key_paths:
        if key_path.exists():
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
    
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    
    raise Exception("Failed to connect to VPS")

def run_cmd(ssh, cmd):
    """Run command and return output"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    return exit_status == 0, output, error

def assess():
    """Run comprehensive assessment"""
    print("=" * 80)
    print("🔍 COMPREHENSIVE VPS ASSESSMENT")
    print("=" * 80)
    print()
    
    ssh = connect_vps()
    print(f"✅ Connected to {VPS_HOST}\n")
    
    issues = []
    warnings = []
    good = []
    
    # 1. Check Services
    print("📋 1. SYSTEMD SERVICES")
    print("-" * 80)
    services = [
        'phazevpn-go.service',
        'shadowsocks-phazevpn.service',
        'phazevpn-web-portal.service',
        'phazevpn-deadswitch.service',
    ]
    
    for service in services:
        success, output, error = run_cmd(ssh, f"systemctl is-active {service} 2>&1")
        if success and 'active' in output.lower():
            status = output.strip()
            success2, output2, _ = run_cmd(ssh, f"systemctl is-enabled {service} 2>&1")
            enabled = 'enabled' in output2.lower()
            if enabled:
                good.append(f"✅ {service}: {status} (enabled)")
                print(f"  ✅ {service}: {status} (enabled)")
            else:
                warnings.append(f"⚠️  {service}: {status} but NOT enabled on boot")
                print(f"  ⚠️  {service}: {status} but NOT enabled on boot")
        else:
            issues.append(f"❌ {service}: NOT RUNNING")
            print(f"  ❌ {service}: NOT RUNNING")
    
    print()
    
    # 2. Check Ports
    print("📋 2. NETWORK PORTS")
    print("-" * 80)
    ports_to_check = {
        '51821': 'PhazeVPN Protocol',
        '8388': 'Shadowsocks',
        '1194': 'OpenVPN',
        '5000': 'Web Portal',
        '443': 'HTTPS',
        '80': 'HTTP',
    }
    
    success, output, _ = run_cmd(ssh, "ss -tuln | grep -E 'LISTEN|udp'")
    listening_ports = output
    
    for port, name in ports_to_check.items():
        if port in listening_ports:
            good.append(f"✅ Port {port} ({name}): LISTENING")
            print(f"  ✅ Port {port} ({name}): LISTENING")
        else:
            issues.append(f"❌ Port {port} ({name}): NOT LISTENING")
            print(f"  ❌ Port {port} ({name}): NOT LISTENING")
    
    print()
    
    # 3. Check Processes
    print("📋 3. RUNNING PROCESSES")
    print("-" * 80)
    processes = [
        ('phazevpn-server-go', 'PhazeVPN Go Server'),
        ('ss-server', 'Shadowsocks Server'),
        ('openvpn', 'OpenVPN Server'),
        ('python3.*app.py', 'Web Portal'),
        ('dead-mans-switch.py', 'Dead Man\'s Switch'),
    ]
    
    success, output, _ = run_cmd(ssh, "ps aux")
    all_processes = output
    
    for pattern, name in processes:
        if pattern in all_processes or any(p in all_processes for p in pattern.split('.*')):
            good.append(f"✅ {name}: RUNNING")
            print(f"  ✅ {name}: RUNNING")
        else:
            issues.append(f"❌ {name}: NOT RUNNING")
            print(f"  ❌ {name}: NOT RUNNING")
    
    print()
    
    # 4. Check Files & Directories
    print("📋 4. FILES & DIRECTORIES")
    print("-" * 80)
    paths_to_check = [
        ('/opt/phaze-vpn', 'Main directory'),
        ('/opt/phaze-vpn/phazevpn-protocol-go', 'Go protocol directory'),
        ('/opt/phaze-vpn/phazevpn-protocol-go/phazevpn-server-go', 'Go server binary'),
        ('/opt/phaze-vpn/web-portal', 'Web portal directory'),
        ('/opt/phaze-vpn/web-portal/app.py', 'Web portal app'),
        ('/opt/phaze-vpn/dead-mans-switch.py', 'Dead Man\'s Switch'),
        ('/opt/phaze-vpn/certs', 'Certificates directory'),
        ('/opt/phaze-vpn/client-configs', 'Client configs directory'),
    ]
    
    for path, name in paths_to_check:
        success, output, _ = run_cmd(ssh, f"test -e {path} && echo 'exists' || echo 'missing'")
        if 'exists' in output:
            good.append(f"✅ {name}: EXISTS")
            print(f"  ✅ {name}: EXISTS")
        else:
            issues.append(f"❌ {name}: MISSING ({path})")
            print(f"  ❌ {name}: MISSING ({path})")
    
    print()
    
    # 5. Check Permissions
    print("📋 5. FILE PERMISSIONS")
    print("-" * 80)
    success, output, _ = run_cmd(ssh, "ls -la /opt/phaze-vpn/phazevpn-protocol-go/phazevpn-server-go 2>&1")
    if 'cannot access' in output.lower():
        issues.append(f"❌ Go server binary: PERMISSION DENIED or MISSING")
        print(f"  ❌ Go server binary: PERMISSION DENIED or MISSING")
    else:
        if 'x' in output.split()[0]:  # Check if executable
            good.append(f"✅ Go server binary: EXECUTABLE")
            print(f"  ✅ Go server binary: EXECUTABLE")
        else:
            warnings.append(f"⚠️  Go server binary: NOT EXECUTABLE")
            print(f"  ⚠️  Go server binary: NOT EXECUTABLE")
    
    print()
    
    # 6. Check Logs for Errors
    print("📋 6. RECENT ERRORS IN LOGS")
    print("-" * 80)
    log_checks = [
        ('phazevpn-go.service', 'journalctl -u phazevpn-go.service -n 20 --no-pager'),
        ('web-portal', 'tail -20 /opt/phaze-vpn/web-portal/logs/*.log 2>/dev/null || echo "no logs"'),
    ]
    
    for name, cmd in log_checks:
        success, output, _ = run_cmd(ssh, cmd)
        error_keywords = ['error', 'failed', 'fatal', 'panic', 'exception']
        errors_found = [line for line in output.split('\n') if any(kw in line.lower() for kw in error_keywords)]
        if errors_found:
            issues.append(f"❌ {name}: ERRORS IN LOGS")
            print(f"  ❌ {name}: ERRORS IN LOGS")
            for err in errors_found[:3]:  # Show first 3
                print(f"     {err[:70]}")
        else:
            good.append(f"✅ {name}: NO RECENT ERRORS")
            print(f"  ✅ {name}: NO RECENT ERRORS")
    
    print()
    
    # 7. Check Firewall
    print("📋 7. FIREWALL RULES")
    print("-" * 80)
    success, output, _ = run_cmd(ssh, "ufw status 2>&1 | head -20")
    if 'active' in output.lower():
        good.append(f"✅ UFW: ACTIVE")
        print(f"  ✅ UFW: ACTIVE")
        # Check if VPN ports are allowed
        if '51821' in output or '8388' in output or '1194' in output:
            good.append(f"✅ VPN ports: ALLOWED")
            print(f"  ✅ VPN ports: ALLOWED")
        else:
            warnings.append(f"⚠️  VPN ports: MAY NOT BE ALLOWED")
            print(f"  ⚠️  VPN ports: MAY NOT BE ALLOWED")
    else:
        warnings.append(f"⚠️  UFW: NOT ACTIVE (or using iptables)")
        print(f"  ⚠️  UFW: NOT ACTIVE (or using iptables)")
    
    print()
    
    # 8. Check IP Forwarding
    print("📋 8. IP FORWARDING")
    print("-" * 80)
    success, output, _ = run_cmd(ssh, "cat /proc/sys/net/ipv4/ip_forward")
    if output.strip() == '1':
        good.append(f"✅ IP Forwarding: ENABLED")
        print(f"  ✅ IP Forwarding: ENABLED")
    else:
        issues.append(f"❌ IP Forwarding: DISABLED")
        print(f"  ❌ IP Forwarding: DISABLED")
    
    print()
    
    # 9. Check Disk Space
    print("📋 9. DISK SPACE")
    print("-" * 80)
    success, output, _ = run_cmd(ssh, "df -h / | tail -1")
    if success:
        parts = output.split()
        if len(parts) >= 5:
            used_pct = parts[4].rstrip('%')
            try:
                used = int(used_pct)
                if used > 90:
                    issues.append(f"❌ Disk Space: {used_pct}% USED (CRITICAL)")
                    print(f"  ❌ Disk Space: {used_pct}% USED (CRITICAL)")
                elif used > 80:
                    warnings.append(f"⚠️  Disk Space: {used_pct}% USED (WARNING)")
                    print(f"  ⚠️  Disk Space: {used_pct}% USED (WARNING)")
                else:
                    good.append(f"✅ Disk Space: {used_pct}% USED")
                    print(f"  ✅ Disk Space: {used_pct}% USED")
            except:
                print(f"  ⚠️  Could not parse disk usage")
    
    print()
    
    # 10. Check Environment Variables
    print("📋 10. ENVIRONMENT VARIABLES")
    print("-" * 80)
    env_vars = [
        'FLASK_SECRET_KEY',
        'VPN_SERVER_IP',
        'VPN_SERVER_HOST',
    ]
    
    for var in env_vars:
        success, output, _ = run_cmd(ssh, f"grep -r {var} /opt/phaze-vpn/web-portal/.env 2>/dev/null || echo 'not found'")
        if 'not found' in output or not output.strip():
            warnings.append(f"⚠️  {var}: NOT SET (may use defaults)")
            print(f"  ⚠️  {var}: NOT SET (may use defaults)")
        else:
            good.append(f"✅ {var}: SET")
            print(f"  ✅ {var}: SET")
    
    print()
    
    # 11. Check Client Configs
    print("📋 11. CLIENT CONFIGS")
    print("-" * 80)
    success, output, _ = run_cmd(ssh, "find /opt/phaze-vpn/client-configs -name '*.conf' -o -name '*.ovpn' -o -name '*.wg' 2>/dev/null | wc -l")
    try:
        count = int(output.strip())
        if count > 0:
            good.append(f"✅ Client Configs: {count} FOUND")
            print(f"  ✅ Client Configs: {count} FOUND")
        else:
            warnings.append(f"⚠️  Client Configs: NONE FOUND")
            print(f"  ⚠️  Client Configs: NONE FOUND")
    except:
        warnings.append(f"⚠️  Could not count client configs")
        print(f"  ⚠️  Could not count client configs")
    
    # Check for 0.0.0.0 in configs
    success, output, _ = run_cmd(ssh, "grep -r '0.0.0.0' /opt/phaze-vpn/client-configs 2>/dev/null | wc -l")
    try:
        bad_count = int(output.strip())
        if bad_count > 0:
            issues.append(f"❌ Client Configs: {bad_count} contain 0.0.0.0 (should be phazevpn.com)")
            print(f"  ❌ Client Configs: {bad_count} contain 0.0.0.0 (should be phazevpn.com)")
        else:
            good.append(f"✅ Client Configs: NO 0.0.0.0 found")
            print(f"  ✅ Client Configs: NO 0.0.0.0 found")
    except:
        pass
    
    print()
    
    # 12. Check Go Installation
    print("📋 12. GO INSTALLATION")
    print("-" * 80)
    success, output, _ = run_cmd(ssh, "/usr/local/go/bin/go version 2>&1 || go version 2>&1")
    if 'go version' in output.lower():
        version = output.strip()
        good.append(f"✅ Go: {version}")
        print(f"  ✅ Go: {version}")
    else:
        issues.append(f"❌ Go: NOT INSTALLED or NOT IN PATH")
        print(f"  ❌ Go: NOT INSTALLED or NOT IN PATH")
    
    print()
    
    # 13. Check Python Dependencies
    print("📋 13. PYTHON DEPENDENCIES")
    print("-" * 80)
    success, output, _ = run_cmd(ssh, "python3 -c 'import flask, bcrypt, paramiko' 2>&1")
    if success:
        good.append(f"✅ Python Dependencies: INSTALLED")
        print(f"  ✅ Python Dependencies: INSTALLED")
    else:
        issues.append(f"❌ Python Dependencies: MISSING")
        print(f"  ❌ Python Dependencies: MISSING")
        print(f"     {output[:100]}")
    
    print()
    
    # 14. Check SSL/TLS Certificates
    print("📋 14. SSL/TLS CERTIFICATES")
    print("-" * 80)
    cert_paths = [
        '/opt/phaze-vpn/certs/ca.crt',
        '/opt/phaze-vpn/certs/server.crt',
    ]
    
    for cert_path in cert_paths:
        success, output, _ = run_cmd(ssh, f"test -f {cert_path} && echo 'exists' || echo 'missing'")
        if 'exists' in output:
            good.append(f"✅ Certificate: {cert_path.split('/')[-1]}")
            print(f"  ✅ Certificate: {cert_path.split('/')[-1]}")
        else:
            issues.append(f"❌ Certificate: MISSING ({cert_path})")
            print(f"  ❌ Certificate: MISSING ({cert_path})")
    
    print()
    
    # SUMMARY
    print("=" * 80)
    print("📊 ASSESSMENT SUMMARY")
    print("=" * 80)
    print()
    print(f"✅ GOOD: {len(good)}")
    print(f"⚠️  WARNINGS: {len(warnings)}")
    print(f"❌ ISSUES: {len(issues)}")
    print()
    
    if issues:
        print("🚨 CRITICAL ISSUES:")
        print("-" * 80)
        for issue in issues:
            print(f"  {issue}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS:")
        print("-" * 80)
        for warning in warnings:
            print(f"  {warning}")
        print()
    
    if not issues and not warnings:
        print("🎉 EVERYTHING LOOKS GOOD!")
        print()
    
    # Recommendations
    print("=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    
    recommendations = []
    
    if any('NOT RUNNING' in i for i in issues):
        recommendations.append("1. Start all required services: systemctl start phazevpn-go.service shadowsocks-phazevpn.service phazevpn-web-portal.service")
    
    if any('NOT ENABLED' in w for w in warnings):
        recommendations.append("2. Enable services on boot: systemctl enable phazevpn-go.service shadowsocks-phazevpn.service phazevpn-web-portal.service")
    
    if any('IP Forwarding: DISABLED' in i for i in issues):
        recommendations.append("3. Enable IP forwarding: echo 1 > /proc/sys/net/ipv4/ip_forward && sysctl -w net.ipv4.ip_forward=1")
    
    if any('0.0.0.0' in i for i in issues):
        recommendations.append("4. Fix client configs: Replace 0.0.0.0 with phazevpn.com in all client configs")
    
    if any('MISSING' in i and 'Certificate' in i for i in issues):
        recommendations.append("5. Generate certificates: Run certificate generation script")
    
    if any('NOT INSTALLED' in i and 'Go' in i for i in issues):
        recommendations.append("6. Install Go: Download and install Go from golang.org")
    
    if any('MISSING' in i and 'Python Dependencies' in i for i in issues):
        recommendations.append("7. Install Python dependencies: pip3 install flask bcrypt paramiko")
    
    if any('NOT LISTENING' in i and 'Port 5000' in i for i in issues):
        recommendations.append("8. Start web portal: systemctl start phazevpn-web-portal.service")
    
    if recommendations:
        for rec in recommendations:
            print(f"  {rec}")
    else:
        print("  No critical recommendations at this time.")
    
    print()
    
    ssh.close()
    print("✅ Assessment complete!")

if __name__ == '__main__':
    assess()

