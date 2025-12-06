#!/usr/bin/env python3
"""
Automated PhazeVPN VPS Setup - Final Version
Uses paramiko (no sshpass needed)
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
VPS_PASS = "eRkkDQTUsjt2"
LOCAL_DIR = Path("/opt/phaze-vpn")
REMOTE_DIR = "/opt/phaze-vpn"

def install_paramiko():
    """Install paramiko if not available"""
    try:
        import paramiko
        return paramiko
    except ImportError:
        print("Installing paramiko (user install, no sudo needed)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "paramiko"], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import paramiko
        return paramiko

def run_remote(ssh, cmd, sudo=False):
    """Run a command on remote server"""
    if sudo:
        # Use sudo with password via stdin
        full_cmd = f"echo '{VPS_PASS}' | sudo -S {cmd}"
    else:
        full_cmd = cmd
    
    stdin, stdout, stderr = ssh.exec_command(full_cmd)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if exit_status != 0 and error and "password has expired" not in error.lower():
        print(f"⚠️  Warning: {error.strip()[:100]}")
    
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
        # Update system
        print("✅ Step 2/10: Updating system packages...")
        run_remote(ssh, "apt-get update -qq", sudo=True)
        run_remote(ssh, "apt-get upgrade -y -qq", sudo=True)
        print("✅ System updated\n")
        
        # Install dependencies
        print("✅ Step 3/10: Installing dependencies...")
        deps = "python3 python3-pip python3-tk openssl openvpn easy-rsa iptables ufw net-tools curl wget git build-essential debhelper devscripts"
        run_remote(ssh, f"apt-get install -y {deps}", sudo=True)
        print("✅ Dependencies installed\n")
        
        # Create directories
        print("✅ Step 4/10: Creating PhazeVPN directory...")
        run_remote(ssh, f"mkdir -p {REMOTE_DIR}/{{config,certs,client-configs,logs,scripts,backups}}", sudo=True)
        run_remote(ssh, f"chmod 755 {REMOTE_DIR}", sudo=True)
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
        
        # Transfer tarball using SFTP
        sftp = ssh.open_sftp()
        try:
            sftp.put(tar_path, "/tmp/phaze-vpn-setup.tar.gz")
        except Exception as e:
            print(f"⚠️  SFTP failed, trying alternative method: {e}")
            # Fallback: use scp via subprocess
            import subprocess
            subprocess.run(["scp", "-o", "StrictHostKeyChecking=no", tar_path, 
                          f"{VPS_USER}@{VPS_IP}:/tmp/phaze-vpn-setup.tar.gz"], 
                         input=VPS_PASS.encode(), check=False)
        finally:
            sftp.close()
        
        # Extract on remote
        run_remote(ssh, f"cd /tmp && tar -xzf phaze-vpn-setup.tar.gz && cp -r * {REMOTE_DIR}/ 2>/dev/null || true && cp -r config/* {REMOTE_DIR}/config/ 2>/dev/null || true && cp phaze-vpn.service phaze-vpn-download.service /etc/systemd/system/ 2>/dev/null || true", sudo=True)
        run_remote(ssh, f"chmod +x {REMOTE_DIR}/*.sh {REMOTE_DIR}/*.py 2>/dev/null || true", sudo=True)
        run_remote(ssh, f"chown -R root:root {REMOTE_DIR}", sudo=True)
        
        os.unlink(tar_path)
        print("✅ Files transferred\n")
        
        # Install systemd services
        print("✅ Step 6/10: Installing systemd services...")
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
        
        # Write service files
        sftp = ssh.open_sftp()
        with sftp.file("/tmp/phaze-vpn.service", 'w') as f:
            f.write(phaze_vpn_service)
        with sftp.file("/tmp/phaze-vpn-download.service", 'w') as f:
            f.write(phaze_download_service)
        sftp.close()
        
        run_remote(ssh, "cp /tmp/phaze-vpn.service /tmp/phaze-vpn-download.service /etc/systemd/system/", sudo=True)
        run_remote(ssh, "systemctl daemon-reload", sudo=True)
        print("✅ Services installed\n")
        
        # Configure firewall
        print("✅ Step 7/10: Configuring firewall...")
        run_remote(ssh, "ufw --force enable", sudo=True)
        run_remote(ssh, "ufw allow 22/tcp", sudo=True)
        run_remote(ssh, "ufw allow 1194/udp", sudo=True)
        run_remote(ssh, "ufw allow 8081/tcp", sudo=True)
        print("✅ Firewall configured\n")
        
        # Initialize VPN
        print("✅ Step 8/10: Setting server IP and initializing VPN...")
        run_remote(ssh, f"cd {REMOTE_DIR} && python3 vpn-manager.py set-server-ip {VPS_IP}", sudo=True)
        run_remote(ssh, f"cd {REMOTE_DIR} && python3 vpn-manager.py init", sudo=True)
        print("✅ VPN initialized\n")
        
        # Setup routing
        print("✅ Step 9/10: Setting up routing...")
        run_remote(ssh, f"cd {REMOTE_DIR} && bash setup-routing.sh", sudo=True)
        print("✅ Routing configured\n")
        
        # Start services
        print("✅ Step 10/10: Starting services...")
        run_remote(ssh, "systemctl enable phaze-vpn phaze-vpn-download", sudo=True)
        run_remote(ssh, "systemctl start phaze-vpn phaze-vpn-download", sudo=True)
        
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
        run_remote(ssh, "rm -f /tmp/phaze-vpn-setup.tar.gz /tmp/phaze-vpn.service /tmp/phaze-vpn-download.service")
        
    finally:
        ssh.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())


