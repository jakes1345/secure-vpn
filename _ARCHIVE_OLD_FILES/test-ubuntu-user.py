#!/usr/bin/env python3
"""Test SSH connection with ubuntu user (default on Ubuntu 22.04)"""

import paramiko
import sys

VPS_IP = "15.204.11.19"
PASSWORD = "Jakes1328!@"

def test_ubuntu_user():
    print("🔍 Testing SSH connection with 'ubuntu' user...")
    print(f"   Server: ubuntu@{VPS_IP}")
    print()
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print("📡 Connecting as ubuntu user...")
        ssh.connect(
            VPS_IP,
            username="ubuntu",
            password=PASSWORD,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        
        print("✅ SUCCESS! Password works with ubuntu user!")
        print()
        
        stdin, stdout, stderr = ssh.exec_command("whoami && uname -a")
        output = stdout.read().decode().strip()
        print(f"Connected as: {output}")
        
        ssh.close()
        return True
        
    except paramiko.AuthenticationException:
        print("❌ AUTHENTICATION FAILED with ubuntu user too")
        print()
        print("The password doesn't work. You need to:")
        print("  1. Go back to rescue mode")
        print("  2. Reset password again")
        print("  3. Make sure you see 'password updated successfully'")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_ubuntu_user()
    sys.exit(0 if success else 1)

