#!/usr/bin/env python3
"""
Diagnose VPS SSH connection issues
"""

import paramiko
import socket
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"

def test_connectivity():
    """Test if VPS is reachable"""
    print("Testing connectivity...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((VPS_IP, 22))
        sock.close()
        
        if result == 0:
            print(f"✅ Port 22 (SSH) is OPEN on {VPS_IP}")
            return True
        else:
            print(f"❌ Port 22 (SSH) is CLOSED on {VPS_IP}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect: {e}")
        return False

def test_ssh_password(password):
    """Test SSH with password"""
    print(f"\nTesting SSH with password authentication...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=password, timeout=10)
        print("✅ Password authentication works!")
        ssh.close()
        return True
    except paramiko.AuthenticationException:
        print("❌ Password authentication failed (wrong password)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_ssh_key(key_file):
    """Test SSH with key file"""
    print(f"\nTesting SSH with key file: {key_file}")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, key_filename=key_file, timeout=10)
        print("✅ Key authentication works!")
        ssh.close()
        return True
    except Exception as e:
        print(f"❌ Key authentication failed: {e}")
        return False

def check_ssh_config():
    """Check SSH configuration"""
    print("\nChecking SSH configuration...")
    
    # Common SSH key locations
    key_files = [
        os.path.expanduser("~/.ssh/id_rsa"),
        os.path.expanduser("~/.ssh/id_ed25519"),
        os.path.expanduser("~/.ssh/id_ecdsa"),
    ]
    
    print("\nAvailable SSH keys:")
    for key_file in key_files:
        if os.path.exists(key_file):
            print(f"  ✅ {key_file}")
        else:
            print(f"  ❌ {key_file} (not found)")

def main():
    """Main diagnostic"""
    print("=" * 60)
    print("🔍 VPS SSH Connection Diagnostic")
    print("=" * 60)
    print(f"\nVPS: {VPS_USER}@{VPS_IP}")
    
    # Test connectivity
    if not test_connectivity():
        print("\n❌ VPS SSH port is not accessible!")
        print("\nPossible solutions:")
        print("  1. Check VPS provider dashboard")
        print("  2. Check firewall rules")
        print("  3. Check if VPS is running")
        return 1
    
    # Check SSH keys
    check_ssh_config()
    
    # Try to get password from environment or prompt
    import os
    password = os.getenv("VPS_PASSWORD")
    
    if password:
        test_ssh_password(password)
    else:
        print("\n⚠️  No password provided (set VPS_PASSWORD env var)")
    
    # Try SSH keys
    import os
    key_files = [
        os.path.expanduser("~/.ssh/id_rsa"),
        os.path.expanduser("~/.ssh/id_ed25519"),
    ]
    
    for key_file in key_files:
        if os.path.exists(key_file):
            if test_ssh_key(key_file):
                print(f"\n✅ Success! Use this key: {key_file}")
                return 0
    
    print("\n" + "=" * 60)
    print("❌ DIAGNOSIS COMPLETE")
    print("=" * 60)
    print("\nPossible solutions:")
    print("  1. Check VPS provider console/control panel")
    print("  2. Reset SSH password via VPS provider")
    print("  3. Add your SSH key via VPS provider")
    print("  4. Check if SSH service is running on VPS")
    print("\nTo test with password:")
    print("  export VPS_PASSWORD='your_password'")
    print("  python3 diagnose-vps-ssh.py")
    
    return 1

if __name__ == "__main__":
    import os
    sys.exit(main())

