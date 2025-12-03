#!/usr/bin/env python3
"""Quick check of deployment status on VPS"""

import paramiko
import os
from pathlib import Path

VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD')
PROTOCOL_DIR = "/opt/phaze-vpn/phazevpn-protocol-go"

def connect_vps():
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
    
    return None

def main():
    print("🔍 Checking deployment status...\n")
    
    ssh = connect_vps()
    if not ssh:
        print("❌ Could not connect to VPS")
        return
    
    try:
        # Check Go
        stdin, stdout, stderr = ssh.exec_command("/usr/local/go/bin/go version 2>&1 || echo 'NOT INSTALLED'")
        go_status = stdout.read().decode().strip()
        print(f"📦 Go: {go_status}")
        
        # Check binary
        stdin, stdout, stderr = ssh.exec_command(f"test -f {PROTOCOL_DIR}/phazevpn-server-go && echo 'EXISTS' || echo 'MISSING'")
        binary_status = stdout.read().decode().strip()
        print(f"🔨 Binary: {binary_status}")
        
        # Check services
        services = ["phazevpn-go.service", "wg-quick@wg0.service", "shadowsocks-phazevpn.service"]
        print("\n📊 Services:")
        for service in services:
            stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service} 2>&1")
            status = stdout.read().decode().strip()
            print(f"  - {service}: {status}")
        
        # Check processes
        print("\n🔄 Processes:")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E '[p]hazevpn-server-go|[w]g-quick|[s]s-server' | head -5")
        processes = stdout.read().decode().strip()
        if processes:
            print(processes)
        else:
            print("  No processes found")
        
        # Check ports
        print("\n🔌 Ports:")
        stdin, stdout, stderr = ssh.exec_command("netstat -tuln 2>/dev/null | grep -E '(51820|8388)' || ss -tuln 2>/dev/null | grep -E '(51820|8388)' || echo 'No ports listening'")
        ports = stdout.read().decode().strip()
        print(ports if ports else "  No ports listening")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

