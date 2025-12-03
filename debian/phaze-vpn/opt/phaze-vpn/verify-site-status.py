#!/usr/bin/env python3
"""
Quick verification script to check site status
"""

from paramiko import SSHClient, AutoAddPolicy
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 70)
print("🔍 QUICK SITE STATUS CHECK")
print("=" * 70)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    # Check Flask app
    stdin, stdout, stderr = ssh.exec_command("pgrep -f 'app.py' | wc -l")
    app_count = int(stdout.read().decode().strip())
    print(f"Flask processes: {app_count} {'✅' if app_count > 0 else '❌'}")
    
    # Check port
    stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep ':8081' | wc -l || ss -tlnp 2>/dev/null | grep ':8081' | wc -l")
    port_listening = int(stdout.read().decode().strip())
    print(f"Port 8081 listening: {'✅' if port_listening > 0 else '❌'}")
    
    # Check nginx
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active nginx 2>&1")
    nginx_status = stdout.read().decode().strip()
    print(f"Nginx status: {nginx_status} {'✅' if nginx_status == 'active' else '❌'}")
    
    # Check systemd service
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1")
    service_status = stdout.read().decode().strip()
    print(f"Web portal service: {service_status} {'✅' if service_status == 'active' else '❌'}")
    
    # Test connection
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' -k https://127.0.0.1/ 2>&1")
    http_code = stdout.read().decode().strip()
    print(f"Site response: {http_code} {'✅' if http_code == '200' else '❌'}")
    
    # Check for errors in logs
    stdin, stdout, stderr = ssh.exec_command("tail -5 /tmp/web-portal.log 2>&1 | grep -i error | wc -l")
    error_count = int(stdout.read().decode().strip())
    print(f"Recent errors in logs: {error_count} {'⚠️' if error_count > 0 else '✅'}")
    
    print("")
    print("=" * 70)
    print("🌐 Site URL: https://phazevpn.duckdns.org")
    print("=" * 70)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

