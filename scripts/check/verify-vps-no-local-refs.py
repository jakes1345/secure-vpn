#!/usr/bin/env python3
"""
Verify VPS has NO local PC references
"""

import paramiko
import os
from pathlib import Path
import re

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
VPS_DIR = "/opt/phaze-vpn"

def connect_vps():
    """Connect to VPS"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key_paths = [
        Path.home() / '.ssh' / 'id_rsa',
        Path.home() / '.ssh' / 'id_ed25519',
    ]
    
    for key_path in key_paths:
        if key_path.exists() and key_path.is_file():
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
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, timeout=10)
        return ssh
    except:
        pass
    
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    return None

def main():
    print("="*70)
    print("VERIFYING VPS HAS NO LOCAL PC REFERENCES")
    print("="*70)
    print("")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    print("✅ Connected to VPS")
    print("")
    
    # Patterns to search for
    bad_patterns = [
        r'/media/jack',
        r'/home/jack',
        r'jack-MS-7C95',
        r'jack@jack-MS-7C95',
    ]
    
    issues_found = []
    
    # Check critical files
    critical_files = [
        f"{VPS_DIR}/web-portal/app.py",
        f"{VPS_DIR}/vpn-gui.py",
        f"{VPS_DIR}/vpn-manager.py",
        f"{VPS_DIR}/web-portal/nginx-phazevpn.conf",
        f"/etc/systemd/system/phazevpn-portal.service",
    ]
    
    print("🔍 Checking critical files...")
    for file_path in critical_files:
        check_cmd = f"test -f {file_path} && echo 'EXISTS' || echo 'MISSING'"
        stdin, stdout, stderr = ssh.exec_command(check_cmd)
        exists = stdout.read().decode().strip()
        
        if exists == 'EXISTS':
            for pattern in bad_patterns:
                grep_cmd = f"grep -n '{pattern}' {file_path} 2>/dev/null | head -3"
                stdin, stdout, stderr = ssh.exec_command(grep_cmd)
                matches = stdout.read().decode().strip()
                if matches:
                    issues_found.append(f"{file_path}: {pattern}")
                    print(f"   ❌ Found {pattern} in {file_path}")
                    for line in matches.split('\n')[:2]:
                        print(f"      {line}")
    
    # Check web-portal directory
    print("")
    print("🔍 Checking web-portal directory...")
    check_cmd = f"""
grep -r "/media/jack\\|/home/jack\\|jack-MS-7C95" {VPS_DIR}/web-portal/*.py {VPS_DIR}/web-portal/*.conf 2>/dev/null | head -5
"""
    stdin, stdout, stderr = ssh.exec_command(check_cmd)
    matches = stdout.read().decode().strip()
    if matches:
        print("   ⚠️  Found local references:")
        for line in matches.split('\n')[:5]:
            print(f"      {line}")
            issues_found.append(line)
    else:
        print("   ✅ No local PC references found")
    
    print("")
    print("="*70)
    if issues_found:
        print(f"⚠️  FOUND {len(issues_found)} ISSUES")
        print("="*70)
        print("")
        print("Issues found:")
        for issue in issues_found[:10]:
            print(f"  - {issue}")
    else:
        print("✅ NO LOCAL PC REFERENCES FOUND!")
        print("="*70)
        print("")
        print("All files are configured for VPS only.")
        print("Nothing points to your local PC.")
    print("")
    
    ssh.close()

if __name__ == '__main__':
    main()

