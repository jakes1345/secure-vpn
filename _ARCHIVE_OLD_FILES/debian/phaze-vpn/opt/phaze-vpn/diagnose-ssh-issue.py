#!/usr/bin/env python3
"""
Diagnose SSH connection issues
Check if it's a password problem or SSH configuration problem
"""

import paramiko
import socket

VPS_IP = "15.204.11.19"
PASSWORD = "Jakes1328!@"

def test_connection(username, password):
    print(f"\n🔍 Testing: {username}@{VPS_IP}")
    print(f"   Password: {'*' * len(password)}")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh.connect(
            VPS_IP,
            username=username,
            password=password,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        
        print(f"   ✅ SUCCESS! Connected as {username}")
        
        # Get system info
        stdin, stdout, stderr = ssh.exec_command("hostname && whoami && uname -a")
        info = stdout.read().decode().strip()
        print(f"   System: {info}")
        
        ssh.close()
        return True
        
    except paramiko.AuthenticationException:
        print(f"   ❌ Authentication failed - wrong password or user disabled")
        return False
    except paramiko.SSHException as e:
        print(f"   ⚠️  SSH error: {e}")
        if "not allowed" in str(e).lower():
            print(f"   → Root login might be disabled in SSH config")
        return False
    except socket.timeout:
        print(f"   ❌ Connection timeout")
        return False
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("SSH Connection Diagnosis")
    print("=" * 60)
    
    print("\nTesting root user...")
    root_works = test_connection("root", PASSWORD)
    
    print("\nTesting ubuntu user...")
    ubuntu_works = test_connection("ubuntu", PASSWORD)
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    if root_works:
        print("✅ Root login works! Use: ssh root@15.204.11.19")
    elif ubuntu_works:
        print("✅ Ubuntu user works! Use: ssh ubuntu@15.204.11.19")
        print("⚠️  Root login is disabled - use ubuntu user instead")
    else:
        print("❌ Neither user works")
        print("\nThe password change didn't work. You need to:")
        print("1. Go back to rescue mode")
        print("2. Reset password using chpasswd method")
        print("3. Enable root login in SSH config")
        print("4. Exit rescue mode and reboot")

