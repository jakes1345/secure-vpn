#!/usr/bin/env python3
"""
VPS Communication Helper
Beautiful, reliable communication with VPS server
"""

import subprocess
import paramiko
import os
from pathlib import Path

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASSWORD = "Jakes1328!@"

def ssh_to_vps(command):
    """Execute command on VPS via SSH - beautiful and reliable"""
    try:
        # Method 1: Use paramiko (Python SSH - most reliable)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=5)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        ssh.close()
        return {'success': True, 'output': output, 'error': error}
    except Exception as e:
        # Method 2: Fallback to sshpass
        try:
            result = subprocess.run(['sshpass', '-p', VPS_PASSWORD, 'ssh',
                                   '-o', 'StrictHostKeyChecking=no',
                                   '-o', 'ConnectTimeout=5',
                                   f'{VPS_USER}@{VPS_HOST}', command],
                                  capture_output=True, text=True, timeout=10)
            return {'success': result.returncode == 0,
                   'output': result.stdout.strip(),
                   'error': result.stderr.strip()}
        except FileNotFoundError:
            # Method 3: Try SSH key
            try:
                result = subprocess.run(['ssh', '-o', 'StrictHostKeyChecking=no',
                                       '-o', 'ConnectTimeout=5',
                                       f'{VPS_USER}@{VPS_HOST}', command],
                                      capture_output=True, text=True, timeout=10)
                return {'success': result.returncode == 0,
                       'output': result.stdout.strip(),
                       'error': result.stderr.strip()}
            except:
                return {'success': False, 'output': '', 'error': str(e)}

def check_vpn_status():
    """Check if VPN is running on VPS"""
    result = ssh_to_vps('/usr/local/bin/check-vpn-status')
    if result['success']:
        return result['output'].strip() == 'running'
    return False

def start_vpn():
    """Start VPN on VPS"""
    result = ssh_to_vps('/usr/local/bin/start-vpn')
    return result['success'] and ('started' in result['output'] or '✅' in result['output'])

def stop_vpn():
    """Stop VPN on VPS"""
    result = ssh_to_vps('/usr/local/bin/stop-vpn')
    return result['success'] and ('stopped' in result['output'] or '✅' in result['output'])

def restart_vpn():
    """Restart VPN on VPS"""
    stop_vpn()
    import time
    time.sleep(2)
    return start_vpn()
