#!/usr/bin/env python3
"""
Automated OVH VPS Setup Script for PhazeVPN
This script does EVERYTHING automatically
"""

import os
import sys
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "ubuntu"
VPS_PASS = "QwX8MJJH3fSE"
LOCAL_DIR = Path("/opt/phaze-vpn")
REMOTE_DIR = "/opt/phaze-vpn"

def install_paramiko():
    """Install paramiko if not available"""
    try:
        import paramiko
        return paramiko
    except ImportError:
        print("Installing paramiko...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "paramiko"])
        import paramiko
        return paramiko

def run_remote(ssh, cmd, sudo=False, use_sudo_stdin=False):
    """Run a command on remote server"""
    if sudo and use_sudo_stdin:
        # Use stdin for password
        stdin, stdout, stderr = ssh.exec_command(f"sudo -S {cmd}", get_pty=True)
        stdin.write(f"{VPS_PASS}\n")
        stdin.flush()
    elif sudo:
        # Try without password first (if NOPASSWD is set)
        stdin, stdout, stderr = ssh.exec_command(f"sudo {cmd}")
    else:
        stdin, stdout, stderr = ssh.exec_command(cmd)
    
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if exit_status != 0 and error:
        print(f"⚠️  Warning: {error.strip()}")
    
    return output, exit_status

def main():
    print("==========================================")
    print("🚀 Automated PhazeVPN VPS Setup")
    print("==========================================")
    print(f"\nVPS: {VPS_USER}@{VPS_IP}\n")
    
    # Install paramiko
    try:
        paramiko = install_paramiko()
    except Exception as e:
        print(f"❌ Failed to install paramiko: {e}")
        print("Please install manually: pip3 install paramiko")
        return 1
    
    # Connect to VPS
    print("✅ Step 1/10: Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("✅ Connected!\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return 1
    
    try:
        # Check if password needs to be changed
        print("🔍 Checking password status...")
        test_output, _ = run_remote(ssh, "echo 'test'")
        if "password has expired" in test_output.lower() or "password change required" in test_output.lower():
            print("⚠️  Password has expired. Attempting to change it...")
            print("   (This may require manual intervention)")
            # Try to change password non-interactively
            stdin, stdout, stderr = ssh.exec_command(f"passwd", get_pty=True)
            stdin.write(f"{VPS_PASS}\n{VPS_PASS}\n{VPS_PASS}\n")
            stdin.flush()
            time.sleep(2)
        
        # Update system
        print("✅ Step 2/10: Updating system packages...")
        run_remote(ssh, "apt-get update -qq && apt-get upgrade -y -qq", sudo=True, use_sudo_stdin=True)
        print("✅ System updated\n")
        
        # Install dependencies
        print("✅ Step 3/10: Installing dependencies...")
        deps = "python3 python3-pip python3-tk openssl openvpn easy-rsa iptables ufw net-tools curl wget git build-essential debhelper devscripts"
        run_remote(ssh, f"apt-get install -y {deps}", sudo=True, use_sudo_stdin=True)
        print("✅ Dependencies installed\n")
        
        # Create directories
        print("✅ Step 4/10: Creating PhazeVPN directory...")
        run_remote(ssh, f"mkdir -p {REMOTE_DIR}/{{config,certs,client-configs,logs,scripts,backups}}", sudo=True, use_sudo_stdin=True)
        run_remote(ssh, f"chmod 755 {REMOTE_DIR}", sudo=True, use_sudo_stdin=True)
        print("✅ Directory created\n")
        
        # Transfer files
        print("✅ Step 5/10: Transferring PhazeVPN files...")
        files_to_transfer = [
            "vpn-manager.py",
            "vpn-gui.py",
            "client-download-server.py",
            "subscription-manager.py",
            "setup-routing.sh",
            "open-download-port.sh",
            "start-download-server-robust.sh",
            "generate-certs.sh",
        ]
        
        # Create tarball
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
            tar_path = tmp.name
            with tarfile.open(tar_path, 'w:gz') as tar:
                # Add Python files
                for f in files_to_transfer:
                    file_path = LOCAL_DIR / f
                    if file_path.exists():
                        tar.add(file_path, arcname=f)
                
                # Add config directory
                config_dir = LOCAL_DIR / "config"
                if config_dir.exists():
                    tar.add(config_dir, arcname="config")
                
                # Add service files
                for svc in ["phaze-vpn.service", "phaze-vpn-download.service"]:
                    svc_path = LOCAL_DIR / "debian" / svc
                    if svc_path.exists():
                        tar.add(svc_path, arcname=svc)
        
        # Transfer tarball
        sftp = ssh.open_sftp()
        sftp.put(tar_path, "/tmp/phaze-vpn-files.tar.gz")
        sftp.close()
        
        # Extract on remote
        run_remote(ssh, f"cd /tmp && mkdir -p phaze-extract && cd phaze-extract && tar -xzf ../phaze-vpn-files.tar.gz && cp -r * {REMOTE_DIR}/ 2>/dev/null || true && cp -r config/* {REMOTE_DIR}/config/ 2>/dev/null || true && cp phaze-vpn.service phaze-vpn-download.service /etc/systemd/system/ 2>/dev/null || true", sudo=True, use_sudo_stdin=True)
        run_remote(ssh, f"chmod +x {REMOTE_DIR}/*.sh {REMOTE_DIR}/*.py 2>/dev/null || true", sudo=True, use_sudo_stdin=True)
        run_remote(ssh, f"chown -R root:root {REMOTE_DIR}", sudo=True, use_sudo_stdin=True)
        
        os.unlink(tar_path)
        print("✅ Files transferred\n")
        
        # Install systemd services
        print("✅ Step 6/10: Installing systemd services...")
        # Ensure services exist
        phaze_vpn_service = f"""[Unit]
Description=PhazeVPN Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={REMOTE_DIR}
ExecStart=/usr/bin/python3 {REMOTE_DIR}/vpn-manager.py start
ExecStop=/usr/bin/python3 {REMOTE_DIR}/vpn-manager.py stop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target"""
        
        phaze_download_service = f"""[Unit]
Description=PhazeVPN Client Download Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={REMOTE_DIR}
ExecStart=/usr/bin/python3 {REMOTE_DIR}/client-download-server.py
Restart=always
RestartSec=5
StartLimitInterval=0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"""
        
        sftp = ssh.open_sftp()
        with sftp.file("/tmp/phaze-vpn.service", 'w') as f:
            f.write(phaze_vpn_service)
        with sftp.file("/tmp/phaze-vpn-download.service", 'w') as f:
            f.write(phaze_download_service)
        sftp.close()
        
        run_remote(ssh, "cp /tmp/phaze-vpn.service /tmp/phaze-vpn-download.service /etc/systemd/system/", sudo=True, use_sudo_stdin=True)
        run_remote(ssh, "systemctl daemon-reload", sudo=True, use_sudo_stdin=True)
        print("✅ Services installed\n")
        
        # Configure firewall
        print("✅ Step 7/10: Configuring firewall...")
        run_remote(ssh, "ufw --force enable", sudo=True, use_sudo_stdin=True)
        run_remote(ssh, "ufw allow 22/tcp", sudo=True, use_sudo_stdin=True)
        run_remote(ssh, "ufw allow 1194/udp", sudo=True, use_sudo_stdin=True)
        run_remote(ssh, "ufw allow 8081/tcp", sudo=True, use_sudo_stdin=True)
        print("✅ Firewall configured\n")
        
        # Initialize VPN
        print("✅ Step 8/10: Setting server IP and initializing VPN...")
        run_remote(ssh, f"cd {REMOTE_DIR} && python3 vpn-manager.py set-server-ip {VPS_IP}", sudo=True, use_sudo_stdin=True)
        run_remote(ssh, f"cd {REMOTE_DIR} && python3 vpn-manager.py init", sudo=True, use_sudo_stdin=True)
        print("✅ VPN initialized\n")
        
        # Setup routing
        print("✅ Step 9/10: Setting up routing...")
        run_remote(ssh, f"cd {REMOTE_DIR} && bash setup-routing.sh", sudo=True, use_sudo_stdin=True)
        print("✅ Routing configured\n")
        
        # Start services
        print("✅ Step 10/10: Starting services...")
        run_remote(ssh, "systemctl enable phaze-vpn phaze-vpn-download", sudo=True, use_sudo_stdin=True)
        run_remote(ssh, "systemctl start phaze-vpn phaze-vpn-download", sudo=True, use_sudo_stdin=True)
        
        import time
        time.sleep(3)
        
        # Check status
        status1, _ = run_remote(ssh, "systemctl is-active phaze-vpn")
        status2, _ = run_remote(ssh, "systemctl is-active phaze-vpn-download")
        
        print("✅ Services started\n")
        
        print("==========================================")
        print("✅ Setup Complete!")
        print("==========================================")
        print(f"\n📊 Service Status:")
        print(f"   VPN Server: {status1.strip()}")
        print(f"   Download Server: {status2.strip()}")
        print(f"\n🌐 Download Server:")
        print(f"   http://{VPS_IP}:8081")
        print(f"\n📝 Next Steps:")
        print(f"   1. Create a test client:")
        print(f"      ssh {VPS_USER}@{VPS_IP}")
        print(f"      sudo python3 /opt/phaze-vpn/vpn-manager.py add-client test-client")
        print(f"\n   2. Download config:")
        print(f"      http://{VPS_IP}:8081/download?name=test-client")
        print(f"\n🎉 PhazeVPN is now running on your OVH VPS!")
        
        # Cleanup
        run_remote(ssh, "rm -f /tmp/phaze-vpn-files.tar.gz /tmp/phaze-vpn.service /tmp/phaze-vpn-download.service")
        
    finally:
        ssh.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

