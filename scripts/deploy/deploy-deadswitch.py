#!/usr/bin/env python3
"""
Deploy Dead Man's Switch to VPS
"""
import paramiko
import os
from pathlib import Path

VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = os.environ.get('VPS_PASS') or os.environ.get('VPS_PASSWORD', 'Jakes1328!@')

def connect_vps():
    """Connect to VPS using SSH key or password"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Try SSH keys first
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
    
    # Fall back to password
    if VPS_PASSWORD:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=10)
        return ssh
    
    raise Exception("Failed to connect to VPS")

def deploy():
    """Deploy dead man's switch to VPS"""
    print("🚀 Deploying Dead Man's Switch to VPS...")
    
    try:
        print(f"📡 Connecting to {VPS_HOST}...")
        ssh = connect_vps()
        print("✅ Connected!")
        
        # Create directory
        print("📁 Creating directories...")
        ssh.exec_command("mkdir -p /opt/phaze-vpn")
        
        # Upload dead man's switch
        print("📤 Uploading dead-mans-switch.py...")
        sftp = ssh.open_sftp()
        
        local_file = Path("dead-mans-switch.py")
        remote_file = "/opt/phaze-vpn/dead-mans-switch.py"
        
        sftp.put(str(local_file), remote_file)
        sftp.chmod(remote_file, 0o755)
        sftp.close()
        
        # Upload setup script
        print("📤 Uploading setup script...")
        sftp = ssh.open_sftp()
        local_setup = Path("setup-dead-mans-switch.sh")
        remote_setup = "/opt/phaze-vpn/setup-dead-mans-switch.sh"
        sftp.put(str(local_setup), remote_setup)
        sftp.chmod(remote_setup, 0o755)
        sftp.close()
        
        # Run setup script
        print("⚙️  Running setup script...")
        stdin, stdout, stderr = ssh.exec_command("bash /opt/phaze-vpn/setup-dead-mans-switch.sh")
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("✅ Dead Man's Switch deployed successfully!")
            print("\nStatus:")
            stdin, stdout, stderr = ssh.exec_command("systemctl status phazevpn-deadswitch --no-pager -l | head -20")
            print(stdout.read().decode())
        else:
            error = stderr.read().decode()
            print(f"⚠️  Setup had issues: {error}")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False
    
    return True

if __name__ == '__main__':
    deploy()


