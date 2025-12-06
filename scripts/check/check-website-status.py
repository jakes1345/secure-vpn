#!/usr/bin/env python3
"""
Check website status - diagnose blank page issue
"""

import paramiko
import requests
from pathlib import Path

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description):
    """Run command on VPS"""
    print(f"  {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 80)
    print("🔍 CHECKING WEBSITE STATUS - DIAGNOSING BLANK PAGE")
    print("=" * 80)
    print()
    
    # Connect to VPS
    print("🔌 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    print()
    
    # Check if web portal is running
    print("1️⃣ Checking web portal service...")
    success, output, error = run_command(ssh, "systemctl status secure-vpn-web-portal 2>&1 | head -10", "Checking web portal service")
    print(f"   {output}")
    
    print()
    
    # Check if nginx is running
    print("2️⃣ Checking Nginx...")
    success, output, error = run_command(ssh, "systemctl status nginx 2>&1 | head -5", "Checking Nginx")
    print(f"   {output}")
    
    print()
    
    # Check nginx error logs
    print("3️⃣ Checking Nginx error logs...")
    success, output, error = run_command(ssh, "tail -20 /var/log/nginx/error.log", "Checking error logs")
    if output:
        print(f"   {output}")
    else:
        print("   No recent errors")
    
    print()
    
    # Check if port 80/443 is listening
    print("4️⃣ Checking if ports are listening...")
    success, output, error = run_command(ssh, "netstat -tlnp | grep -E ':80|:443'", "Checking ports")
    print(f"   {output}")
    
    print()
    
    # Check Flask app logs
    print("5️⃣ Checking Flask app logs...")
    success, output, error = run_command(ssh, "journalctl -u secure-vpn-web-portal -n 30 --no-pager 2>&1", "Checking Flask logs")
    if output:
        print(f"   {output[:500]}")
    else:
        print("   No logs found")
    
    print()
    
    # Try to access the site
    print("6️⃣ Testing website access...")
    try:
        response = requests.get("https://phazevpn.duckdns.org", timeout=10, verify=False)
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Length: {len(response.text)} bytes")
        if len(response.text) < 100:
            print(f"   Content: {response.text[:200]}")
        else:
            print(f"   First 200 chars: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Failed to access: {e}")
    
    print()
    print("=" * 80)
    print("✅ DIAGNOSIS COMPLETE")
    print("=" * 80)
    
    ssh.close()

if __name__ == "__main__":
    main()

