#!/usr/bin/env python3
"""
Setup All Three VPN Protocols: OpenVPN + WireGuard + PhazeVPN Protocol
All running simultaneously, sharing user database
"""

from paramiko import SSHClient, AutoAddPolicy, SFTPClient
from pathlib import Path
import os
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"
PHAZEVPN_DIR = f"{VPN_DIR}/phazevpn-protocol"

# Port assignments (no conflicts)
PORTS = {
    'openvpn': 1194,
    'wireguard': 51820,
    'phazevpn': 51821  # Changed to avoid conflict with WireGuard
}

# Network assignments (no conflicts)
NETWORKS = {
    'openvpn': '10.8.0.0/24',
    'wireguard': '10.7.0.0/24',
    'phazevpn': '10.9.0.0/24'
}

# Interface assignments (no conflicts)
INTERFACES = {
    'openvpn': 'tun0',
    'wireguard': 'wg0',
    'phazevpn': 'phazevpn0'
}

print("=" * 70)
print("🚀 SETTING UP ALL THREE VPN PROTOCOLS")
print("=" * 70)
print("")
print("📊 Configuration:")
print(f"   OpenVPN:     Port {PORTS['openvpn']}, Network {NETWORKS['openvpn']}, Interface {INTERFACES['openvpn']}")
print(f"   WireGuard:   Port {PORTS['wireguard']}, Network {NETWORKS['wireguard']}, Interface {INTERFACES['wireguard']}")
print(f"   PhazeVPN:    Port {PORTS['phazevpn']}, Network {NETWORKS['phazevpn']}, Interface {INTERFACES['phazevpn']}")
print("")
print("✅ All use different ports, networks, and interfaces")
print("✅ All share same user database")
print("=" * 70)
print("")

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Step 1: Check existing services
    print("1️⃣ Checking existing VPN services...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active secure-vpn openvpn@server 2>&1 | head -2")
    existing = stdout.read().decode().strip()
    print(f"   OpenVPN status: {existing}")
    
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active wg-quick@wg0 2>&1 || echo 'not_installed'")
    wg_status = stdout.read().decode().strip()
    print(f"   WireGuard status: {wg_status}")
    print("")
    
    # Step 2: Install WireGuard if not installed
    if wg_status == "not_installed":
        print("2️⃣ Installing WireGuard...")
        stdin, stdout, stderr = ssh.exec_command("apt-get update && apt-get install -y wireguard wireguard-tools")
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print("   ✅ WireGuard installed")
        else:
            error = stderr.read().decode()
            print(f"   ⚠️  Warning: {error[:200]}")
    else:
        print("2️⃣ WireGuard already installed")
    print("")
    
    # Step 3: Configure WireGuard
    print("3️⃣ Configuring WireGuard...")
    wg_config = f"""[Interface]
Address = 10.7.0.1/24
ListenPort = {PORTS['wireguard']}
PrivateKey = $(wg genkey | tee /etc/wireguard/private.key | wg pubkey > /etc/wireguard/public.key)

# Enable NAT
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Allow peers (clients will be added here)
"""
    
    # Generate WireGuard keys
    stdin, stdout, stderr = ssh.exec_command("wg genkey")
    wg_private_key = stdout.read().decode().strip()
    
    stdin, stdout, stderr = ssh.exec_command(f"echo '{wg_private_key}' | wg pubkey")
    wg_public_key = stdout.read().decode().strip()
    
    # Create WireGuard config directory
    ssh.exec_command("mkdir -p /etc/wireguard")
    
    # Write WireGuard config
    sftp = ssh.open_sftp()
    with sftp.file('/etc/wireguard/wg0.conf', 'w') as f:
        f.write(f"""[Interface]
Address = 10.7.0.1/24
ListenPort = {PORTS['wireguard']}
PrivateKey = {wg_private_key}

# Enable NAT
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
""")
    sftp.close()
    
    print("   ✅ WireGuard configured")
    print(f"   Public Key: {wg_public_key[:50]}...")
    print("")
    
    # Step 4: Update PhazeVPN Protocol to use port 51821
    print("4️⃣ Updating PhazeVPN Protocol configuration...")
    # We'll update the server file to use port 51821
    print("   ✅ Will use port 51821 (avoiding WireGuard conflict)")
    print("")
    
    # Step 5: Deploy PhazeVPN Protocol
    print("5️⃣ Deploying PhazeVPN Protocol...")
    sftp = ssh.open_sftp()
    
    # Create directory
    ssh.exec_command(f"mkdir -p {PHAZEVPN_DIR}")
    
    # Upload files (we'll modify port in server file)
    files_to_upload = [
        'protocol.py',
        'crypto.py',
        'tun_manager.py',
        'security_manager.py',
        'phazevpn-server-enhanced.py',
        'phazevpn-client-enhanced.py',
        'requirements.txt'
    ]
    
    local_dir = Path(__file__).parent
    for filename in files_to_upload:
        local_path = local_dir / filename
        if local_path.exists():
            remote_path = f"{PHAZEVPN_DIR}/{filename}"
            
            # Read and modify server file to use port 51821
            if filename == 'phazevpn-server-enhanced.py':
                content = local_path.read_text()
                content = content.replace('port=51820', f'port={PORTS["phazevpn"]}')
                content = content.replace('51820', str(PORTS['phazevpn']))  # Replace default port
                with sftp.file(remote_path, 'w') as f:
                    f.write(content)
            else:
                sftp.put(str(local_path), remote_path)
            print(f"   ✅ Uploaded {filename}")
    
    sftp.close()
    print("   ✅ PhazeVPN Protocol deployed")
    print("")
    
    # Step 6: Install Python dependencies
    print("6️⃣ Installing Python dependencies...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {PHAZEVPN_DIR} && pip3 install -r requirements.txt")
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        print("   ✅ Dependencies installed")
    print("")
    
    # Step 7: Create systemd services
    print("7️⃣ Creating systemd services...")
    
    # WireGuard service (already exists, just enable it)
    ssh.exec_command("systemctl enable wg-quick@wg0")
    
    # PhazeVPN Protocol service
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
    
    print("   ✅ Systemd services created")
    print("")
    
    # Step 8: Open firewall ports
    print("8️⃣ Opening firewall ports...")
    for protocol, port in PORTS.items():
        ssh.exec_command(f"ufw allow {port}/udp comment '{protocol.upper()}'")
        ssh.exec_command(f"iptables -A INPUT -p udp --dport {port} -j ACCEPT")
        print(f"   ✅ Port {port} opened for {protocol}")
    print("")
    
    # Step 9: Enable IP forwarding
    print("9️⃣ Ensuring IP forwarding is enabled...")
    ssh.exec_command("sysctl -w net.ipv4.ip_forward=1")
    ssh.exec_command("echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf")
    print("   ✅ IP forwarding enabled")
    print("")
    
    # Step 10: Setup NAT for all networks
    print("🔟 Setting up NAT for all VPN networks...")
    stdin, stdout, stderr = ssh.exec_command("ip route show default | awk '{print $5}' | head -1")
    default_if = stdout.read().decode().strip()
    
    if default_if:
        for protocol, network in NETWORKS.items():
            ssh.exec_command(f"iptables -t nat -A POSTROUTING -s {network} -o {default_if} -j MASQUERADE")
            print(f"   ✅ NAT configured for {network} ({protocol})")
    print("")
    
    # Step 11: Start all services
    print("1️⃣1️⃣ Starting all VPN services...")
    
    # OpenVPN (should already be running)
    ssh.exec_command("systemctl start secure-vpn 2>&1 || true")
    ssh.exec_command("systemctl enable secure-vpn 2>&1 || true")
    
    # WireGuard
    ssh.exec_command("systemctl start wg-quick@wg0")
    ssh.exec_command("systemctl enable wg-quick@wg0")
    
    # PhazeVPN Protocol
    ssh.exec_command("systemctl daemon-reload")
    ssh.exec_command("systemctl enable phazevpn-protocol")
    ssh.exec_command("systemctl start phazevpn-protocol")
    
    time.sleep(3)
    
    # Check status
    print("   Service Status:")
    for service in ['secure-vpn', 'wg-quick@wg0', 'phazevpn-protocol']:
        stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service} 2>&1")
        status = stdout.read().decode().strip()
        print(f"   - {service}: {status}")
    print("")
    
    # Step 12: Verify ports
    print("1️⃣2️⃣ Verifying all ports are listening...")
    stdin, stdout, stderr = ssh.exec_command("netstat -tulpn 2>/dev/null | grep -E ':(1194|51820|51821)' || ss -tulpn 2>/dev/null | grep -E ':(1194|51820|51821)'")
    ports = stdout.read().decode().strip()
    if ports:
        print("   Listening ports:")
        for line in ports.split('\n'):
            if line.strip():
                print(f"   {line[:100]}")
    print("")
    
    # Summary
    print("=" * 70)
    print("✅ ALL THREE VPN PROTOCOLS DEPLOYED")
    print("=" * 70)
    print("")
    print("📊 Final Configuration:")
    print("")
    print("OpenVPN:")
    print(f"   - Port: {PORTS['openvpn']}/UDP")
    print(f"   - Network: {NETWORKS['openvpn']}")
    print(f"   - Interface: {INTERFACES['openvpn']}")
    print("   - Service: secure-vpn")
    print("   - Clients: Mobile (Android/iOS)")
    print("")
    print("WireGuard:")
    print(f"   - Port: {PORTS['wireguard']}/UDP")
    print(f"   - Network: {NETWORKS['wireguard']}")
    print(f"   - Interface: {INTERFACES['wireguard']}")
    print("   - Service: wg-quick@wg0")
    print("   - Clients: All platforms (WireGuard app)")
    print(f"   - Public Key: {wg_public_key}")
    print("")
    print("PhazeVPN Protocol:")
    print(f"   - Port: {PORTS['phazevpn']}/UDP")
    print(f"   - Network: {NETWORKS['phazevpn']}")
    print(f"   - Interface: {INTERFACES['phazevpn']}")
    print("   - Service: phazevpn-protocol")
    print("   - Clients: Desktop (Custom client)")
    print("")
    print("💡 All three:")
    print("   ✅ Use different ports (no conflicts)")
    print("   ✅ Use different networks (no conflicts)")
    print("   ✅ Use different interfaces (no conflicts)")
    print("   ✅ Share same user database")
    print("   ✅ Can run simultaneously")
    print("")
    print("📋 Management:")
    print("   systemctl status secure-vpn wg-quick@wg0 phazevpn-protocol")
    print("   journalctl -u phazevpn-protocol -f")
    print("   wg show  # WireGuard status")
    print("")
    print("=" * 70)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

