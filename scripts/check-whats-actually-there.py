#!/usr/bin/env python3
"""
Check what's actually in the dashboard file
"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    # Check what's in the dashboard
    success, dashboard, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/templates/admin/dashboard.html", check=False)
    
    print("Checking dashboard contents:")
    print(f"Has 'System Information': {'System Information' in dashboard}")
    print(f"Has 'updateSystemInfo': {'updateSystemInfo' in dashboard}")
    print(f"Has 'updateTicketCount': {'updateTicketCount' in dashboard}")
    print(f"Has 'function updateSystemInfo': {'function updateSystemInfo' in dashboard}")
    print(f"Has 'function updateTicketCount': {'function updateTicketCount' in dashboard}")
    
    # Show relevant sections
    if 'System Information' in dashboard:
        lines = dashboard.split('\n')
        for i, line in enumerate(lines):
            if 'System Information' in line:
                print(f"\nFound 'System Information' at line {i+1}")
                print("Context:")
                for j in range(max(0, i-2), min(len(lines), i+10)):
                    print(f"{j+1:4d}: {lines[j]}")
                break
    
    if 'updateSystemInfo' in dashboard:
        lines = dashboard.split('\n')
        for i, line in enumerate(lines):
            if 'function updateSystemInfo' in line:
                print(f"\nFound 'function updateSystemInfo' at line {i+1}")
                print("Context:")
                for j in range(max(0, i-2), min(len(lines), i+15)):
                    print(f"{j+1:4d}: {lines[j]}")
                break
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")

