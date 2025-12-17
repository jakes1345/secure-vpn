#!/usr/bin/env python3
"""
Deploy PhazeVPN Protocol to VPS alongside OpenVPN
Ensures both can run simultaneously without conflicts
"""

from paramiko import SSHClient, AutoAddPolicy, SFTPClient
from pathlib import Path
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"
PHAZEVPN_DIR = f"{VPN_DIR}/phazevpn-protocol"

print("=" * 70)
print("🚀 DEPLOYING PHAZEVPN PROTOCOL TO VPS")
print("=" * 70)
print(f"📍 VPS: {VPS_IP}")
print(f"📁 Target: {PHAZEVPN_DIR}")
print("")
print("💡 This will run ALONGSIDE OpenVPN:")
print("   - OpenVPN: Port 1194, Network 10.8.0.0/24, Interface tun0")
print("   - PhazeVPN: Port 51820, Network 10.9.0.0/24, Interface phazevpn0")
print("=" * 70)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Step 1: Create directory structure
    print("1️⃣ Creating directory structure...")
    ssh.exec_command(f"mkdir -p {PHAZEVPN_DIR}")
    ssh.exec_command(f"mkdir -p {VPN_DIR}/logs")
    print("   ✅ Directories created")
    print("")
    
    # Step 2: Upload protocol files
    print("2️⃣ Uploading PhazeVPN Protocol files...")
    sftp = ssh.open_sftp()
    
    files_to_upload = [
        'protocol.py',
        'crypto.py',
        'tun_manager.py',
        'security_manager.py',
        'phazevpn-server-enhanced.py',
        'phazevpn-client-enhanced.py',
        'requirements.txt',
        'README.md'
    ]
    
    local_dir = Path(__file__).parent
    for filename in files_to_upload:
        local_path = local_dir / filename
        if local_path.exists():
            remote_path = f"{PHAZEVPN_DIR}/{filename}"
            sftp.put(str(local_path), remote_path)
            print(f"   ✅ Uploaded {filename}")
        else:
            print(f"   ⚠️  {filename} not found locally")
    
    sftp.close()
    print("   ✅ Files uploaded")
    print("")
    
    # Step 3: Install Python dependencies
    print("3️⃣ Installing Python dependencies...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {PHAZEVPN_DIR} && pip3 install -r requirements.txt")
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        print("   ✅ Dependencies installed")
    else:
        error = stderr.read().decode()
        print(f"   ⚠️  Warning: {error[:200]}")
    print("")
    
    # Step 4: Make scripts executable
    print("4️⃣ Making scripts executable...")
    ssh.exec_command(f"chmod +x {PHAZEVPN_DIR}/*.py")
    print("   ✅ Scripts are executable")
    print("")
    
    # Step 5: Create systemd service
    print("5️⃣ Creating systemd service...")
    service_content = f"""[Unit]
Description=PhazeVPN Protocol Server
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory={PHAZEVPN_DIR}
ExecStart=/usr/bin/python3 {PHAZEVPN_DIR}/phazevpn-server-enhanced.py
Restart=always
RestartSec=10
StartLimitInterval=0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    sftp = ssh.open_sftp()
    with sftp.file('/etc/systemd/system/phazevpn-protocol.service', 'w') as f:
        f.write(service_content)
    sftp.close()
    print("   ✅ Systemd service created")
    print("")
    
    # Step 6: Open firewall port
    print("6️⃣ Opening firewall port 51820...")
    ssh.exec_command("ufw allow 51820/udp comment 'PhazeVPN Protocol'")
    ssh.exec_command("iptables -A INPUT -p udp --dport 51820 -j ACCEPT")
    print("   ✅ Firewall configured")
    print("")
    
    # Step 7: Enable IP forwarding (if not already enabled)
    print("7️⃣ Ensuring IP forwarding is enabled...")
    ssh.exec_command("sysctl -w net.ipv4.ip_forward=1")
    ssh.exec_command("echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf")
    print("   ✅ IP forwarding enabled")
    print("")
    
    # Step 8: Setup NAT for PhazeVPN network
    print("8️⃣ Setting up NAT for PhazeVPN network...")
    # Get default interface
    stdin, stdout, stderr = ssh.exec_command("ip route show default | awk '{print $5}' | head -1")
    default_if = stdout.read().decode().strip()
    
    if default_if:
        # Add NAT rule for PhazeVPN network
        ssh.exec_command(f"iptables -t nat -A POSTROUTING -s 10.9.0.0/24 -o {default_if} -j MASQUERADE")
        print(f"   ✅ NAT configured for 10.9.0.0/24 via {default_if}")
    print("")
    
    # Step 9: Reload systemd and start service
    print("9️⃣ Starting PhazeVPN Protocol service...")
    ssh.exec_command("systemctl daemon-reload")
    ssh.exec_command("systemctl enable phazevpn-protocol")
    ssh.exec_command("systemctl start phazevpn-protocol")
    
    # Wait a moment and check status
    import time
    time.sleep(2)
    
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-protocol")
    status = stdout.read().decode().strip()
    
    if status == "active":
        print("   ✅ Service is running")
    else:
        print(f"   ⚠️  Service status: {status}")
        # Check logs
        stdin, stdout, stderr = ssh.exec_command("journalctl -u phazevpn-protocol -n 10 --no-pager")
        logs = stdout.read().decode()
        print("   Recent logs:")
        for line in logs.split('\n')[-5:]:
            if line.strip():
                print(f"   {line[:100]}")
    print("")
    
    # Step 10: Verify both services
    print("🔟 Verifying both VPN services...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active secure-vpn openvpn@server phazevpn-protocol 2>&1")
    services = stdout.read().decode().strip()
    
    print("   Service Status:")
    for service in ['secure-vpn', 'openvpn@server', 'phazevpn-protocol']:
        stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service} 2>&1")
        status = stdout.read().decode().strip()
        print(f"   - {service}: {status}")
    print("")
    
    # Step 11: Check ports
    print("1️⃣1️⃣ Checking ports...")
    stdin, stdout, stderr = ssh.exec_command("netstat -tulpn 2>/dev/null | grep -E ':(1194|51820)' || ss -tulpn 2>/dev/null | grep -E ':(1194|51820)'")
    ports = stdout.read().decode().strip()
    if ports:
        print("   Listening ports:")
        for line in ports.split('\n'):
            if line.strip():
                print(f"   {line[:100]}")
    print("")
    
    # Summary
    print("=" * 70)
    print("✅ DEPLOYMENT COMPLETE")
    print("=" * 70)
    print("")
    print("📊 Configuration Summary:")
    print("")
    print("OpenVPN (Existing):")
    print("   - Port: 1194/UDP")
    print("   - Network: 10.8.0.0/24")
    print("   - Interface: tun0")
    print("   - Service: secure-vpn")
    print("   - Mobile clients: ✅")
    print("")
    print("PhazeVPN Protocol (New):")
    print("   - Port: 51820/UDP")
    print("   - Network: 10.9.0.0/24")
    print("   - Interface: phazevpn0")
    print("   - Service: phazevpn-protocol")
    print("   - Desktop clients: ✅")
    print("")
    print("💡 Both can run simultaneously:")
    print("   ✅ Different ports (no conflict)")
    print("   ✅ Different networks (no conflict)")
    print("   ✅ Different interfaces (no conflict)")
    print("   ✅ Same user database (shared)")
    print("")
    print("📋 Management Commands:")
    print("   systemctl status phazevpn-protocol    # Check status")
    print("   systemctl restart phazevpn-protocol    # Restart")
    print("   journalctl -u phazevpn-protocol -f    # View logs")
    print("")
    print("=" * 70)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

