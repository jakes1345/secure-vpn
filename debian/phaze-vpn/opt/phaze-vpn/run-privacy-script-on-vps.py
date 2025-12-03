#!/usr/bin/env python3
"""
Run privacy enhancement script on VPS
"""

import sys

try:
    import paramiko
except ImportError:
    print("❌ Error: paramiko not installed")
    sys.exit(1)

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_PATH = "/opt/secure-vpn"

print("🔧 Running privacy enhancement script on VPS...")
print("")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    # Run the script
    command = f"cd {VPS_PATH} && sudo ./scripts/enhance-privacy.sh"
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    
    # Stream output in real-time
    print("Output:")
    print("-" * 50)
    for line in iter(stdout.readline, ""):
        if line:
            print(line.rstrip())
    
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status == 0:
        print("-" * 50)
        print("✅ Privacy enhancement script completed!")
    else:
        error = stderr.read().decode()
        print(f"⚠️  Exit code: {exit_status}")
        if error:
            print(f"Error: {error}")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

