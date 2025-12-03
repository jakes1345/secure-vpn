#!/usr/bin/env python3
"""
Test SSH password connection to VPS
Handles special characters in passwords correctly
"""

import sys
import paramiko
import socket

VPS_IP = "15.204.11.19"
VPS_USER = "root"
PASSWORD = "Jakes1328!@"

def test_password():
    print("🔍 Testing SSH password connection...")
    print(f"   Server: {VPS_USER}@{VPS_IP}")
    print(f"   Password: {'*' * len(PASSWORD)}")
    print()
    
    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print("📡 Connecting...")
        
        # Try to connect
        ssh.connect(
            VPS_IP,
            username=VPS_USER,
            password=PASSWORD,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        
        print("✅ SUCCESS! Password works!")
        print()
        
        # Run a test command
        stdin, stdout, stderr = ssh.exec_command("uname -a")
        output = stdout.read().decode().strip()
        print(f"System info: {output}")
        print()
        
        # Check if we're in rescue mode
        stdin, stdout, stderr = ssh.exec_command("hostname && whoami && pwd")
        system_info = stdout.read().decode().strip()
        print(f"System details:")
        print(f"  {system_info}")
        print()
        
        if "[RESCUE]" in system_info or "rescue" in system_info.lower():
            print("⚠️  WARNING: Still in rescue mode!")
        else:
            print("✅ VPS is in normal mode")
        
        ssh.close()
        return True
        
    except paramiko.AuthenticationException:
        print("❌ AUTHENTICATION FAILED!")
        print()
        print("Possible issues:")
        print("  1. Password is incorrect")
        print("  2. Password wasn't saved correctly during chroot")
        print("  3. Need to reset password again in rescue mode")
        print()
        print("Try this:")
        print("  - Go back to rescue mode")
        print("  - Mount the disk and chroot")
        print("  - Run 'passwd' again")
        print("  - Make sure you see 'password updated successfully' message")
        return False
        
    except socket.timeout:
        print("❌ CONNECTION TIMEOUT!")
        print("   Can't reach the server. Check:")
        print("   - Is the VPS running?")
        print("   - Is the IP correct?")
        print("   - Is SSH enabled?")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}")
        print(f"   {str(e)}")
        return False

if __name__ == "__main__":
    success = test_password()
    sys.exit(0 if success else 1)

