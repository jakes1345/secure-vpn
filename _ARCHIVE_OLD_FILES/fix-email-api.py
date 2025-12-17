#!/usr/bin/env python3
"""
Fix Email API - Check and fix API issues
"""

import paramiko
import sys

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status == 0, output, error

def main():
    print("🔧 Fixing Email API...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # Check API status
        print("\n1️⃣ Checking API status...")
        success, output, error = run_command(ssh, "systemctl status phazevpn-email-api | head -20")
        print(output)
        
        # Check API logs
        print("\n2️⃣ Checking API logs...")
        success, output, error = run_command(ssh, "journalctl -u phazevpn-email-api -n 30 --no-pager")
        print(output)
        
        # Check if API file exists
        print("\n3️⃣ Checking API file...")
        success, output, error = run_command(ssh, "ls -la /opt/phazevpn-email/api/")
        print(output)
        
        # Check API content
        print("\n4️⃣ Checking API code...")
        success, output, error = run_command(ssh, "head -50 /opt/phazevpn-email/api/app.py")
        print(output)
        
        # Restart API
        print("\n5️⃣ Restarting API...")
        run_command(ssh, "systemctl restart phazevpn-email-api")
        print("✅ API restarted")
        
        # Wait a bit
        import time
        time.sleep(3)
        
        # Check status again
        print("\n6️⃣ Checking API status after restart...")
        success, output, error = run_command(ssh, "systemctl status phazevpn-email-api | head -15")
        print(output)
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

