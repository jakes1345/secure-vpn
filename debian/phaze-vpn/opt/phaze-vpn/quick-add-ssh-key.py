#!/usr/bin/env python3
"""
Quick SSH Key Setup - Python version (no sshpass needed)
Adds SSH key to VPS using temporary password
"""

import sys
import os
import subprocess
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "ubuntu"
KEY_NAME = "phaze-vpn-vps-key"
KEY_PATH = Path.home() / ".ssh" / KEY_NAME

def install_paramiko():
    """Install paramiko if needed"""
    try:
        import paramiko
        return paramiko
    except ImportError:
        print("Installing paramiko...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "paramiko"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import paramiko
        return paramiko

def main():
    # Get password from argument or environment
    if len(sys.argv) > 1:
        password = sys.argv[1]
    elif "OVH_PASSWORD" in os.environ:
        password = os.environ["OVH_PASSWORD"]
    else:
        print("Usage: ./quick-add-ssh-key.py <password>")
        print("Or: OVH_PASSWORD=<password> ./quick-add-ssh-key.py")
        return 1
    
    print("==========================================")
    print("⚡ Quick SSH Key Setup")
    print("==========================================")
    print("")
    
    # Generate key if it doesn't exist
    if not KEY_PATH.exists():
        print("📝 Generating SSH key...")
        subprocess.run([
            "ssh-keygen", "-t", "ed25519", "-f", str(KEY_PATH),
            "-N", "", "-C", "phaze-vpn-vps"
        ], check=True, stdout=subprocess.DEVNULL)
        print("✅ Key generated!")
    
    # Read public key
    pub_key_path = KEY_PATH.with_suffix(".pub")
    with open(pub_key_path, 'r') as f:
        public_key = f.read().strip()
    
    print(f"\n📋 Your public key:")
    print(public_key)
    print("")
    
    # Connect and add key
    print("🔄 Connecting to VPS and adding key...")
    
    try:
        paramiko = install_paramiko()
    except Exception as e:
        print(f"❌ Failed to install paramiko: {e}")
        return 1
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect with password
        ssh.connect(VPS_IP, username=VPS_USER, password=password, timeout=10)
        print("✅ Connected!")
        
        # Create .ssh directory if it doesn't exist
        stdin, stdout, stderr = ssh.exec_command("mkdir -p ~/.ssh && chmod 700 ~/.ssh")
        stdout.channel.recv_exit_status()
        
        # Read existing authorized_keys
        stdin, stdout, stderr = ssh.exec_command("cat ~/.ssh/authorized_keys 2>/dev/null || echo ''")
        existing_keys = stdout.read().decode().strip()
        
        # Check if key already exists
        if public_key in existing_keys:
            print("✅ Key already exists on server!")
        else:
            # Add key
            new_keys = existing_keys + "\n" + public_key if existing_keys else public_key
            stdin, stdout, stderr = ssh.exec_command("cat > ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys")
            stdin.write(new_keys + "\n")
            stdin.channel.shutdown_write()
            stdout.channel.recv_exit_status()
            print("✅ Key added to server!")
        
        ssh.close()
        
        # Test key-based connection
        print("\n🔄 Testing SSH key authentication...")
        test_result = subprocess.run([
            "ssh", "-i", str(KEY_PATH), "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=5", f"{VPS_USER}@{VPS_IP}",
            "echo '✅ SSH key authentication works!'"
        ], capture_output=True, timeout=10)
        
        if test_result.returncode == 0:
            print("✅ Connection test successful!")
            print("")
            print("==========================================")
            print("🎉 Setup Complete!")
            print("==========================================")
            print("")
            print("You can now connect without password:")
            print(f"   ssh -i {KEY_PATH} {VPS_USER}@{VPS_IP}")
            print("")
            print("Or run the automated setup:")
            print("   ./auto-setup-with-ssh-key.sh")
            return 0
        else:
            print("⚠️  Key added but test connection failed")
            print("This might be normal - try connecting manually:")
            print(f"   ssh -i {KEY_PATH} {VPS_USER}@{VPS_IP}")
            return 0
            
    except paramiko.AuthenticationException:
        print("❌ Authentication failed - password might be expired or incorrect")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        try:
            ssh.close()
        except:
            pass

if __name__ == "__main__":
    sys.exit(main())

