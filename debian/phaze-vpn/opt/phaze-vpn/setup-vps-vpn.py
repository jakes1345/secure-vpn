#!/usr/bin/env python3
"""
Automated VPN Setup for OVH VPS
Sets up the complete VPN server on the VPS
"""

import paramiko
import os
import sys
import tarfile
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"
LOCAL_DIR = "/opt/phaze-vpn"

def print_step(step_num, total, message):
    print(f"✅ Step {step_num}/{total}: {message}...")
    sys.stdout.flush()

def execute_command(ssh, command, description=""):
    """Execute a command on the remote server"""
    if description:
        print(f"  → {description}")
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    
    # Wait for command to complete
    exit_status = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode()
    errors = stderr.read().decode()
    
    if exit_status != 0:
        print(f"  ⚠️  Warning: {errors}")
    
    return output, errors, exit_status

def main():
    print("=" * 60)
    print("🚀 Automated VPN Setup for OVH VPS")
    print("=" * 60)
    print("")
    
    # Connect to VPS
    print(f"📡 Connecting to {VPS_USER}@{VPS_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)
    
    print("")
    
    # Step 1: Update system
    print_step(1, 9, "Updating system packages")
    execute_command(ssh, "apt-get update -qq && apt-get upgrade -y -qq", "Updating packages")
    print("✅ System updated\n")
    
    # Step 2: Install dependencies
    print_step(2, 9, "Installing dependencies")
    execute_command(ssh, 
        "apt-get install -y python3 python3-pip python3-tk openssl openvpn easy-rsa iptables ufw net-tools curl wget git build-essential debhelper devscripts 2>&1 | tail -5",
        "Installing packages")
    print("✅ Dependencies installed\n")
    
    # Step 3: Create directories
    print_step(3, 9, "Creating VPN directories")
    execute_command(ssh, f"mkdir -p {VPN_DIR}/{{config,certs,client-configs,logs,scripts,backups}} && chmod 755 {VPN_DIR}")
    print("✅ Directories created\n")
    
    # Step 4: Transfer files
    print_step(4, 9, "Transferring VPN files")
    print("  → Creating file package...")
    
    # Create tarball
    os.chdir(LOCAL_DIR)
    tar_path = "/tmp/vpn-setup.tar.gz"
    
    with tarfile.open(tar_path, "w:gz") as tar:
        files_to_add = [
            "vpn-manager.py",
            "vpn-gui.py", 
            "client-download-server.py",
            "subscription-manager.py",
            "setup-routing.sh",
            "open-download-port.sh",
            "start-download-server-robust.sh",
            "generate-certs.sh",
            "manage-vpn.sh",
        ]
        
        for file in files_to_add:
            if os.path.exists(file):
                tar.add(file)
        
        # Add directories
        for dir_name in ["templates", "config"]:
            if os.path.exists(dir_name):
                tar.add(dir_name)
    
    print("  → Uploading files...")
    sftp = ssh.open_sftp()
    sftp.put(tar_path, f"/tmp/vpn-setup.tar.gz")
    sftp.close()
    
    print("  → Extracting files on VPS...")
    execute_command(ssh, 
        f"cd /tmp && tar -xzf vpn-setup.tar.gz && cp -r * {VPN_DIR}/ 2>/dev/null || true && "
        f"cp -r config/* {VPN_DIR}/config/ 2>/dev/null || true && "
        f"chmod +x {VPN_DIR}/*.sh {VPN_DIR}/*.py 2>/dev/null || true && "
        f"rm -f /tmp/vpn-setup.tar.gz")
    
    os.remove(tar_path)
    print("✅ Files transferred\n")
    
    # Step 5: Install systemd services
    print_step(5, 9, "Installing systemd services")
    
    vpn_service = f"""[Unit]
Description=SecureVPN Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={VPN_DIR}
ExecStart=/usr/bin/python3 {VPN_DIR}/vpn-manager.py start
ExecStop=/usr/bin/python3 {VPN_DIR}/vpn-manager.py stop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target"""
    
    download_service = f"""[Unit]
Description=SecureVPN Client Download Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={VPN_DIR}
ExecStart=/usr/bin/python3 {VPN_DIR}/client-download-server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target"""
    
    # Write services
    sftp = ssh.open_sftp()
    
    file = sftp.file("/etc/systemd/system/secure-vpn.service", "w")
    file.write(vpn_service)
    file.close()
    
    file = sftp.file("/etc/systemd/system/secure-vpn-download.service", "w")
    file.write(download_service)
    file.close()
    
    sftp.close()
    
    execute_command(ssh, "systemctl daemon-reload")
    print("✅ Services installed\n")
    
    # Step 6: Configure firewall
    print_step(6, 9, "Configuring firewall")
    execute_command(ssh, "ufw --force enable && ufw allow 22/tcp && ufw allow 1194/udp && ufw allow 8081/tcp")
    output, _, _ = execute_command(ssh, "ufw status | head -10")
    print(output)
    print("✅ Firewall configured\n")
    
    # Step 7: Generate certificates
    print_step(7, 9, "Generating certificates (this may take a few minutes)")
    output, errors, _ = execute_command(ssh, f"cd {VPN_DIR} && bash generate-certs.sh 2>&1 | tail -20")
    print(output)
    if errors:
        print(f"  Note: {errors}")
    print("✅ Certificates generated\n")
    
    # Step 8: Setup routing and configure VPN
    print_step(8, 9, "Configuring VPN and routing")
    execute_command(ssh, f"cd {VPN_DIR} && python3 vpn-manager.py set-server-ip {VPS_IP}")
    execute_command(ssh, f"cd {VPN_DIR} && python3 vpn-manager.py init")
    output, _, _ = execute_command(ssh, f"cd {VPN_DIR} && bash setup-routing.sh 2>&1 | tail -10")
    print(output)
    print("✅ VPN configured\n")
    
    # Step 9: Start services
    print_step(9, 9, "Starting VPN services")
    execute_command(ssh, "systemctl enable secure-vpn secure-vpn-download")
    execute_command(ssh, "systemctl start secure-vpn secure-vpn-download")
    time.sleep(3)
    
    output, _, _ = execute_command(ssh, "systemctl status secure-vpn --no-pager | head -15")
    print(output)
    print("✅ Services started\n")
    
    # Verify everything
    print("=" * 60)
    print("🔍 Verifying setup...")
    print("=" * 60)
    
    checks = [
        ("VPN Service", "systemctl is-active secure-vpn", "✅ VPN service is running", "❌ VPN service not running"),
        ("Download Service", "systemctl is-active secure-vpn-download", "✅ Download service is running", "❌ Download service not running"),
        ("OpenVPN Port", "netstat -tulpn | grep 1194", "✅ Port 1194 is listening", "⚠️  Port 1194 not listening"),
        ("Download Port", "netstat -tulpn | grep 8081", "✅ Port 8081 is listening", "⚠️  Port 8081 not listening"),
        ("IP Forwarding", "cat /proc/sys/net/ipv4/ip_forward", "✅ IP forwarding enabled", "❌ IP forwarding disabled"),
    ]
    
    for name, command, success_msg, fail_msg in checks:
        output, _, exit_status = execute_command(ssh, command)
        if exit_status == 0 and output.strip():
            print(f"{name}: {success_msg}")
        else:
            print(f"{name}: {fail_msg}")
    
    print("")
    print("=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print("")
    print(f"🌐 Your VPN Server is ready!")
    print(f"   Server IP: {VPS_IP}")
    print(f"   VPN Port: 1194/udp")
    print(f"   Download Server: http://{VPS_IP}:8081")
    print("")
    print("📝 Next Steps:")
    print(f"   1. Create a client:")
    print(f"      ssh {VPS_USER}@{VPS_IP}")
    print(f"      cd {VPN_DIR}")
    print(f"      python3 vpn-manager.py add-client test-client")
    print("")
    print(f"   2. Download client config:")
    print(f"      http://{VPS_IP}:8081/download?name=test-client")
    print("")
    
    ssh.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

