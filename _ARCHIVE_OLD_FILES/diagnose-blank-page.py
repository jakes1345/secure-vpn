#!/usr/bin/env python3
"""
Diagnose blank page - Flask is running but page is blank
"""

import paramiko
import requests
import urllib3
urllib3.disable_warnings()

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 80)
    print("🔍 DIAGNOSING BLANK PAGE ISSUE")
    print("=" * 80)
    print()
    
    # Connect to VPS
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    print("1️⃣ Testing Flask app directly (port 5000)...")
    success, output, error = run_command(ssh, "curl -s http://127.0.0.1:5000/ | head -50")
    if success and output:
        if len(output) > 100:
            print(f"    ✅ Flask app is responding (got {len(output)} bytes)")
            print(f"    First 200 chars: {output[:200]}")
        else:
            print(f"    ⚠️  Flask app responded but content is short: {output}")
    else:
        print(f"    ❌ Flask app not responding: {error}")
    
    print()
    
    print("2️⃣ Checking Flask app logs...")
    success, output, error = run_command(ssh, "journalctl -u secure-vpn-web-portal -n 50 --no-pager 2>&1 || tail -50 /tmp/flask-app.log 2>&1 || dmesg | grep -i python | tail -10")
    if output:
        print(f"    {output[:500]}")
    
    print()
    
    print("3️⃣ Testing through Nginx...")
    success, output, error = run_command(ssh, "curl -s -H 'Host: phazevpn.duckdns.org' http://127.0.0.1/ | head -50")
    if success and output:
        if len(output) > 100:
            print(f"    ✅ Nginx proxy is working (got {len(output)} bytes)")
            print(f"    First 200 chars: {output[:200]}")
        else:
            print(f"    ⚠️  Nginx returned short content: {output}")
    else:
        print(f"    ⚠️  Nginx test failed: {error}")
    
    print()
    
    print("4️⃣ Checking Flask app Python errors...")
    success, output, error = run_command(ssh, "ps aux | grep 'python.*app.py' | grep -v grep")
    if output:
        pid = output.split()[1]
        print(f"    Flask PID: {pid}")
        success, output, error = run_command(ssh, f"lsof -p {pid} 2>&1 | head -20")
        if output:
            print(f"    Files open: {output[:300]}")
    
    print()
    
    print("5️⃣ Testing template files...")
    success, output, error = run_command(ssh, "test -f /opt/secure-vpn/web-portal/templates/base.html && echo 'exists' || echo 'missing'")
    if 'missing' in output:
        print("    ❌ base.html template is missing!")
    else:
        print("    ✅ base.html exists")
    
    success, output, error = run_command(ssh, "test -f /opt/secure-vpn/web-portal/templates/home.html && echo 'exists' || echo 'missing'")
    if 'missing' in output:
        print("    ❌ home.html template is missing!")
    else:
        print("    ✅ home.html exists")
    
    print()
    
    print("6️⃣ Checking for template syntax errors...")
    success, output, error = run_command(ssh, "python3 -c \"from jinja2 import Template; Template(open('/opt/secure-vpn/web-portal/templates/base.html').read())\" 2>&1")
    if success:
        print("    ✅ base.html template syntax is valid")
    else:
        print(f"    ❌ Template syntax error: {output[:200]}")
    
    print()
    
    print("=" * 80)
    print("✅ DIAGNOSIS COMPLETE")
    print("=" * 80)
    
    ssh.close()

if __name__ == "__main__":
    main()

