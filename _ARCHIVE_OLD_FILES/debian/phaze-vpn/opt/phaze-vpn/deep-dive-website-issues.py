#!/usr/bin/env python3
"""
Deep dive investigation of website blank page issue
Comprehensive diagnosis of all potential problems
"""

import paramiko
import requests
import urllib3
urllib3.disable_warnings()
from pathlib import Path

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command, timeout=10)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 80)
    print("🔍 DEEP DIVE - COMPREHENSIVE WEBSITE DIAGNOSIS")
    print("=" * 80)
    print()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    issues = []
    fixes = []
    
    # ========================================================================
    # 1. CHECK FLASK PROCESS STATUS
    # ========================================================================
    print("1️⃣ FLASK PROCESS ANALYSIS")
    print("-" * 80)
    
    success, output, error = run_command(ssh, "ps aux | grep -E 'python.*app.py|flask|gunicorn' | grep -v grep")
    if output:
        lines = output.split('\n')
        for line in lines:
            parts = line.split()
            pid = parts[1] if len(parts) > 1 else '?'
            cmd = ' '.join(parts[10:]) if len(parts) > 10 else line
            print(f"   ✅ Flask process found:")
            print(f"      PID: {pid}")
            print(f"      CMD: {cmd[:80]}")
            
            # Check if process is actually listening
            success2, output2, error2 = run_command(ssh, f"lsof -p {pid} 2>&1 | grep -E 'TCP|LISTEN|5000' | head -5")
            if output2:
                print(f"      Network: {output2[:100]}")
            else:
                issues.append("Flask process exists but may not be listening on port 5000")
                print(f"      ⚠️  Process exists but not listening on port 5000")
    else:
        issues.append("Flask app is not running")
        print(f"   ❌ Flask process not found!")
    
    print()
    
    # ========================================================================
    # 2. CHECK PORT 5000 STATUS
    # ========================================================================
    print("2️⃣ PORT 5000 ANALYSIS")
    print("-" * 80)
    
    success, output, error = run_command(ssh, "netstat -tlnp 2>&1 | grep :5000")
    if output:
        print(f"   ✅ Port 5000 is in use:")
        print(f"      {output}")
        
        # Get process using port 5000
        if 'python' in output.lower():
            print(f"      ✅ Python/Flask is listening")
        else:
            issues.append("Port 5000 is in use by something other than Flask")
            print(f"      ⚠️  Port 5000 used by non-Python process")
    else:
        issues.append("Port 5000 is not listening")
        print(f"   ❌ Port 5000 is NOT listening!")
    
    print()
    
    # ========================================================================
    # 3. TEST FLASK APP DIRECTLY
    # ========================================================================
    print("3️⃣ FLASK APP DIRECT TEST")
    print("-" * 80)
    
    success, output, error = run_command(ssh, "timeout 5 curl -v http://127.0.0.1:5000/ 2>&1 | head -30")
    if success and output:
        if 'HTTP/1.0 200' in output or 'HTTP/1.1 200' in output:
            print(f"   ✅ Flask app responds with HTTP 200")
            
            # Check content length
            if 'Content-Length: 0' in output or 'Content-Length:0' in output:
                issues.append("Flask returns HTTP 200 but with 0 bytes content (blank response)")
                print(f"   ⚠️  Flask returns 0 bytes - BLANK RESPONSE!")
            else:
                # Get actual content
                success2, output2, error2 = run_command(ssh, "curl -s http://127.0.0.1:5000/ | head -50")
                if output2 and len(output2) > 100:
                    print(f"   ✅ Flask returns content ({len(output2)} bytes)")
                    print(f"      First 100 chars: {output2[:100]}")
                else:
                    issues.append("Flask returns minimal or no content")
                    print(f"   ⚠️  Flask returns minimal content: {output2[:100] if output2 else 'empty'}")
        else:
            issues.append(f"Flask returns non-200 status")
            print(f"   ⚠️  Flask returned non-200: {output[:200]}")
    else:
        issues.append("Flask app not responding on port 5000")
        print(f"   ❌ Flask app NOT responding!")
        print(f"      Error: {error[:200] if error else 'timeout/connection refused'}")
    
    print()
    
    # ========================================================================
    # 4. CHECK FLASK LOGS
    # ========================================================================
    print("4️⃣ FLASK LOG ANALYSIS")
    print("-" * 80)
    
    log_files = [
        "/tmp/flask-app.log",
        "/opt/secure-vpn/web-portal/flask.log",
        "/var/log/flask-app.log",
    ]
    
    for log_file in log_files:
        success, output, error = run_command(ssh, f"test -f {log_file} && tail -50 {log_file} 2>&1 | head -50 || echo 'not found'")
        if output and 'not found' not in output.lower():
            print(f"   📋 Log file: {log_file}")
            print(f"      Last 20 lines:")
            lines = output.split('\n')[-20:]
            for line in lines:
                if 'error' in line.lower() or 'exception' in line.lower() or 'traceback' in line.lower():
                    print(f"      ❌ ERROR: {line[:150]}")
                    issues.append(f"Flask error in logs: {line[:100]}")
                elif 'started' in line.lower() or 'running' in line.lower():
                    print(f"      ✅ {line[:150]}")
                else:
                    print(f"      {line[:150]}")
            break
    
    # Check systemd journal
    success, output, error = run_command(ssh, "journalctl -u secure-vpn-web-portal -n 30 --no-pager 2>&1 | tail -30")
    if output and 'No entries' not in output:
        print(f"   📋 Systemd journal:")
        print(f"      {output[:500]}")
    
    print()
    
    # ========================================================================
    # 5. CHECK NGINX CONFIGURATION
    # ========================================================================
    print("5️⃣ NGINX CONFIGURATION ANALYSIS")
    print("-" * 80)
    
    # Check all Nginx configs
    success, output, error = run_command(ssh, "ls -la /etc/nginx/sites-enabled/")
    print(f"   Active sites:")
    print(f"      {output}")
    
    # Check main config
    config_files = [
        "/etc/nginx/sites-enabled/securevpn",
        "/etc/nginx/sites-enabled/default",
        "/etc/nginx/sites-enabled/phazevpn",
    ]
    
    for config_file in config_files:
        success, output, error = run_command(ssh, f"test -f {config_file} && cat {config_file} || echo 'not found'")
        if output and 'not found' not in output.lower():
            print(f"\n   📄 Config file: {config_file}")
            
            # Check for proxy_pass
            if 'proxy_pass' in output:
                proxy_lines = [line for line in output.split('\n') if 'proxy_pass' in line.lower()]
                print(f"      ✅ Has proxy_pass:")
                for line in proxy_lines:
                    print(f"         {line.strip()}")
                    
                    if '127.0.0.1:5000' in line or 'localhost:5000' in line:
                        print(f"            ✅ Points to Flask on port 5000")
                    else:
                        issues.append(f"Nginx proxy_pass doesn't point to Flask: {line.strip()}")
                        print(f"            ⚠️  Doesn't point to Flask port 5000!")
            else:
                issues.append(f"Nginx config missing proxy_pass to Flask")
                print(f"      ❌ No proxy_pass found!")
            
            # Check for root directive (might be serving files instead)
            if 'root /var/www' in output or 'root /opt' in output:
                root_lines = [line for line in output.split('\n') if 'root' in line.lower() and not 'root /usr' in line.lower()]
                if root_lines:
                    print(f"      ⚠️  Has 'root' directive (might serve files instead of proxy):")
                    for line in root_lines[:3]:
                        print(f"         {line.strip()}")
                    issues.append("Nginx has 'root' directive which might override proxy_pass")
            
            # Check location blocks
            if 'location /' in output:
                location_lines = []
                in_location = False
                for line in output.split('\n'):
                    if 'location /' in line:
                        in_location = True
                        location_lines.append(line.strip())
                    elif in_location and line.strip().startswith('location'):
                        break
                    elif in_location and line.strip() and not line.strip().startswith('#'):
                        location_lines.append(f"  {line.strip()}")
                
                print(f"      Location / block:")
                for line in location_lines[:10]:
                    print(f"         {line}")
    
    print()
    
    # ========================================================================
    # 6. TEST NGINX RESPONSE
    # ========================================================================
    print("6️⃣ NGINX RESPONSE ANALYSIS")
    print("-" * 80)
    
    # Test through Nginx
    success, output, error = run_command(ssh, "curl -v -H 'Host: phazevpn.duckdns.org' http://127.0.0.1/ 2>&1 | head -40")
    if success and output:
        print(f"   Nginx response headers:")
        header_lines = [line for line in output.split('\n') if ':' in line or 'HTTP/' in line][:15]
        for line in header_lines:
            print(f"      {line}")
        
        # Check if it's serving files or proxying
        if 'Content-Type: text/html' in output or 'Content-Type: application/octet-stream' in output:
            if 'Content-Length: 0' in output:
                issues.append("Nginx returns 0 bytes content")
                print(f"   ⚠️  Nginx returns 0 bytes")
            else:
                # Get actual content
                success2, output2, error2 = run_command(ssh, "curl -s -H 'Host: phazevpn.duckdns.org' http://127.0.0.1/ | head -50")
                if output2:
                    if len(output2) > 100 and '<!DOCTYPE' in output2:
                        print(f"   ✅ Nginx returns HTML ({len(output2)} bytes)")
                        print(f"      First 100 chars: {output2[:100]}")
                    elif 'APT Repository' in output2 or 'Repository' in output2:
                        issues.append("Nginx is serving APT repository page instead of Flask app")
                        print(f"   ❌ Nginx serving APT repo page instead of Flask!")
                        print(f"      Content: {output2[:200]}")
                    else:
                        print(f"   ⚠️  Nginx returns: {output2[:200]}")
    
    print()
    
    # ========================================================================
    # 7. CHECK FILE PERMISSIONS
    # ========================================================================
    print("7️⃣ FILE PERMISSIONS CHECK")
    print("-" * 80)
    
    check_files = [
        "/opt/secure-vpn/web-portal/app.py",
        "/opt/secure-vpn/web-portal/templates/base.html",
        "/opt/secure-vpn/web-portal/templates/home.html",
        "/opt/secure-vpn/web-portal/static/css/style.css",
    ]
    
    for file_path in check_files:
        success, output, error = run_command(ssh, f"ls -la {file_path} 2>&1")
        if output and 'No such file' not in output:
            print(f"   ✅ {file_path}")
            print(f"      {output}")
        else:
            issues.append(f"File missing or inaccessible: {file_path}")
            print(f"   ❌ {file_path} - MISSING or inaccessible")
    
    print()
    
    # ========================================================================
    # 8. CHECK PYTHON DEPENDENCIES
    # ========================================================================
    print("8️⃣ PYTHON DEPENDENCIES CHECK")
    print("-" * 80)
    
    deps = ['flask', 'jinja2', 'bcrypt', 'qrcode']
    for dep in deps:
        success, output, error = run_command(ssh, f"python3 -c 'import {dep}; print({dep}.__version__)' 2>&1")
        if success and output:
            print(f"   ✅ {dep}: {output}")
        else:
            issues.append(f"Missing Python dependency: {dep}")
            print(f"   ❌ {dep}: NOT INSTALLED or ERROR")
            print(f"      {error[:100]}")
    
    print()
    
    # ========================================================================
    # 9. TEST TEMPLATE RENDERING
    # ========================================================================
    print("9️⃣ TEMPLATE RENDERING TEST")
    print("-" * 80)
    
    success, output, error = run_command(ssh, """python3 << 'PYEOF'
import sys
sys.path.insert(0, '/opt/secure-vpn/web-portal')
try:
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader('/opt/secure-vpn/web-portal/templates'))
    template = env.get_template('base.html')
    result = template.render()
    print(f'Template renders: {len(result)} bytes')
    print(f'First 100 chars: {result[:100]}')
except Exception as e:
    print(f'ERROR: {e}')
PYEOF
""")
    if success and output:
        if 'ERROR' in output:
            issues.append(f"Template rendering error: {output}")
            print(f"   ❌ Template error: {output}")
        else:
            print(f"   ✅ Templates work: {output}")
    else:
        print(f"   ⚠️  Template test failed: {error[:200]}")
    
    print()
    
    # ========================================================================
    # 10. SUMMARY AND FIXES
    # ========================================================================
    print("=" * 80)
    print("📊 ISSUE SUMMARY")
    print("=" * 80)
    print()
    
    if issues:
        print(f"❌ Found {len(issues)} issue(s):")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print()
        
        print("🔧 RECOMMENDED FIXES:")
        print()
        
        if any('Flask app is not running' in issue for issue in issues):
            print("   1. START FLASK APP:")
            print("      cd /opt/secure-vpn/web-portal")
            print("      python3 app.py > /tmp/flask-app.log 2>&1 &")
            fixes.append("Start Flask app")
        
        if any('proxy_pass' in issue.lower() for issue in issues):
            print("   2. FIX NGINX CONFIG:")
            print("      - Remove 'root' directives for main location")
            print("      - Add proxy_pass http://127.0.0.1:5000")
            print("      - Keep /repo location for APT repository")
            fixes.append("Fix Nginx proxy configuration")
        
        if any('Port 5000 is not listening' in issue for issue in issues):
            print("   3. CHECK FLASK BINDING:")
            print("      - Ensure Flask binds to 0.0.0.0:5000")
            print("      - Check for port conflicts")
            fixes.append("Check Flask port binding")
        
        if any('serving APT repository page' in issue for issue in issues):
            print("   4. FIX NGINX PRIORITY:")
            print("      - Location /repo should come first")
            print("      - Location / should proxy to Flask")
            fixes.append("Fix Nginx location priority")
    else:
        print("✅ No obvious issues found - might be a runtime error")
    
    print()
    print("=" * 80)
    
    ssh.close()

if __name__ == "__main__":
    main()

