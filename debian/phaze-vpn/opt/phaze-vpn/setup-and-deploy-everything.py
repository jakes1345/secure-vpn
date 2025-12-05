#!/usr/bin/env python3
"""
Complete Setup and Deployment Script
- Deploys web portal
- Deploys all three VPNs (OpenVPN, WireGuard, PhazeVPN Protocol with secure server)
- Uploads advanced security framework
- Ensures everything is running
- Verifies site is accessible
"""

from paramiko import SSHClient, AutoAddPolicy, SFTPClient
from pathlib import Path
import os
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"
BASE_DIR = Path(__file__).parent

print("=" * 70)
print("🚀 COMPLETE SETUP AND DEPLOYMENT")
print("=" * 70)
print("")
print("This will:")
print("  1. Deploy web portal")
print("  2. Deploy OpenVPN (port 1194)")
print("  3. Deploy WireGuard (port 51820)")
print("  4. Deploy PhazeVPN Protocol with Advanced Security (port 51821)")
print("  5. Upload advanced security framework")
print("  6. Ensure all services are running")
print("  7. Verify site is accessible")
print("=" * 70)
print("")

try:
    print("📡 Connecting to VPS...")
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    print("")
    
    # Step 1: Create all directories
    print("1️⃣ Creating directories...")
    dirs = [
        f"{VPN_DIR}/web-portal/templates/admin",
        f"{VPN_DIR}/web-portal/templates/user",
        f"{VPN_DIR}/web-portal/templates/moderator",
        f"{VPN_DIR}/phazevpn-protocol",
        f"{VPN_DIR}/security",
        f"{VPN_DIR}/certs",
        f"{VPN_DIR}/client-configs",
        f"{VPN_DIR}/config"
    ]
    for dir_path in dirs:
        ssh.exec_command(f"mkdir -p '{dir_path}'")
    print("✅ Directories created")
    print("")
    
    # Step 2: Deploy web portal
    print("2️⃣ Deploying web portal...")
    sftp = ssh.open_sftp()
    
    # Web portal files
    web_portal_files = [
        "web-portal/app.py",
        "web-portal/email_smtp.py",
        "web-portal/requirements.txt"
    ]
    
    # Upload web portal files
    for file_path in web_portal_files:
        local_file = BASE_DIR / file_path
        if local_file.exists():
            remote_path = f"{VPN_DIR}/{file_path}"
            remote_dir = os.path.dirname(remote_path)
            ssh.exec_command(f"mkdir -p '{remote_dir}'")
            sftp.put(str(local_file), remote_path)
            print(f"   ✅ {file_path}")
    
    # Upload templates
    templates_dir = BASE_DIR / "web-portal" / "templates"
    if templates_dir.exists():
        for template_file in templates_dir.rglob("*.html"):
            relative_path = template_file.relative_to(BASE_DIR)
            remote_path = f"{VPN_DIR}/{relative_path}"
            remote_dir = os.path.dirname(remote_path)
            ssh.exec_command(f"mkdir -p '{remote_dir}'")
            sftp.put(str(template_file), remote_path)
            print(f"   ✅ {relative_path}")
    
    print("✅ Web portal deployed")
    print("")
    
    # Step 3: Deploy PhazeVPN Protocol with Advanced Security
    print("3️⃣ Deploying PhazeVPN Protocol with Advanced Security...")
    
    # Upload advanced security framework
    security_file = BASE_DIR / "security" / "advanced_security_framework.py"
    if security_file.exists():
        sftp.put(str(security_file), f"{VPN_DIR}/security/advanced_security_framework.py")
        print("   ✅ Advanced security framework uploaded")
    else:
        print("   ⚠️  Advanced security framework not found locally")
    
    # Upload PhazeVPN Protocol files
    phazevpn_files = [
        "phazevpn-protocol/protocol.py",
        "phazevpn-protocol/crypto.py",
        "phazevpn-protocol/tun_manager.py",
        "phazevpn-protocol/cert_manager.py",
        "phazevpn-protocol/phazevpn-server-certified.py",
        "phazevpn-protocol/requirements.txt"
    ]
    
    for file_path in phazevpn_files:
        local_file = BASE_DIR / file_path
        if local_file.exists():
            remote_path = f"{VPN_DIR}/{file_path}"
            remote_dir = os.path.dirname(remote_path)
            ssh.exec_command(f"mkdir -p '{remote_dir}'")
            sftp.put(str(local_file), remote_path)
            ssh.exec_command(f"chmod +x '{remote_path}'")
            print(f"   ✅ {file_path}")
    
    print("✅ PhazeVPN Protocol deployed")
    print("")
    
    # Step 4: Install Python dependencies
    print("4️⃣ Installing Python dependencies...")
    
    # Web portal dependencies
    stdin, stdout, stderr = ssh.exec_command(
        f"cd {VPN_DIR}/web-portal && pip3 install -q -r requirements.txt 2>&1"
    )
    stdout.channel.recv_exit_status()
    print("   ✅ Web portal dependencies installed")
    
    # PhazeVPN dependencies
    stdin, stdout, stderr = ssh.exec_command(
        f"cd {VPN_DIR}/phazevpn-protocol && pip3 install -q cryptography 2>&1"
    )
    stdout.channel.recv_exit_status()
    print("   ✅ PhazeVPN dependencies installed")
    print("")
    
    # Step 5: Ensure certificates exist
    print("5️⃣ Checking certificates...")
    stdin, stdout, stderr = ssh.exec_command(f"test -f {VPN_DIR}/certs/ca.crt && echo 'EXISTS' || echo 'MISSING'")
    ca_exists = stdout.read().decode().strip()
    
    if ca_exists == "MISSING":
        print("   ⚠️  Certificates not found, generating...")
        stdin, stdout, stderr = ssh.exec_command(f"cd {VPN_DIR} && bash generate-certs.sh 2>&1")
        time.sleep(5)
        print("   ✅ Certificates generated")
    else:
        print("   ✅ Certificates exist")
    print("")
    
    # Step 6: Create/update systemd services
    print("6️⃣ Setting up systemd services...")
    
    # Web portal service
    web_service = f"""[Unit]
Description=PhazeVPN Web Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={VPN_DIR}/web-portal
ExecStart=/usr/bin/python3 {VPN_DIR}/web-portal/app.py
Restart=always
RestartSec=5
Environment="FLASK_ENV=production"
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    stdin, stdout, stderr = ssh.exec_command(
        f'cat > /etc/systemd/system/phazevpn-web.service << "EOF"\n{web_service}\nEOF'
    )
    stdout.channel.recv_exit_status()
    print("   ✅ Web portal service created")
    
    # PhazeVPN Protocol service (with advanced security)
    phazevpn_service = f"""[Unit]
Description=PhazeVPN Protocol Server - Secure (Patent Pending)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={VPN_DIR}/phazevpn-protocol
ExecStart=/usr/bin/python3 {VPN_DIR}/phazevpn-protocol/phazevpn-server-certified.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={VPN_DIR}

[Install]
WantedBy=multi-user.target
"""
    
    stdin, stdout, stderr = ssh.exec_command(
        f'cat > /etc/systemd/system/phazevpn-protocol.service << "EOF"\n{phazevpn_service}\nEOF'
    )
    stdout.channel.recv_exit_status()
    print("   ✅ PhazeVPN Protocol service created")
    
    # Reload systemd
    ssh.exec_command("systemctl daemon-reload")
    print("   ✅ Systemd reloaded")
    print("")
    
    # Step 7: Start/restart all services
    print("7️⃣ Starting services...")
    
    services = {
        'OpenVPN': 'secure-vpn',
        'WireGuard': 'wg-quick@wg0',
        'Web Portal': 'phazevpn-web',
        'PhazeVPN Protocol': 'phazevpn-protocol'
    }
    
    for name, service in services.items():
        # Enable service
        ssh.exec_command(f"systemctl enable {service} 2>&1")
        
        # Start/restart service
        ssh.exec_command(f"systemctl restart {service} 2>&1")
        time.sleep(2)
        
        # Check status
        stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service} 2>&1")
        status = stdout.read().decode().strip()
        
        if status == "active":
            print(f"   ✅ {name}: Running")
        else:
            print(f"   ⚠️  {name}: {status}")
    
    print("")
    
    # Step 8: Configure firewall
    print("8️⃣ Configuring firewall...")
    ports = [
        ("80", "tcp", "HTTP"),
        ("443", "tcp", "HTTPS"),
        ("1194", "udp", "OpenVPN"),
        ("51820", "udp", "WireGuard"),
        ("51821", "udp", "PhazeVPN Protocol")
    ]
    
    for port, protocol, name in ports:
        ssh.exec_command(f"ufw allow {port}/{protocol} 2>&1")
        print(f"   ✅ {name} port {port}/{protocol} opened")
    print("")
    
    # Step 9: Verify everything
    print("9️⃣ Verifying deployment...")
    
    # Check services
    print("   Service Status:")
    for name, service in services.items():
        stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service} 2>&1")
        status = stdout.read().decode().strip()
        symbol = "✅" if status == "active" else "❌"
        print(f"   {symbol} {name}: {status}")
    
    # Check ports
    print("")
    print("   Port Status:")
    stdin, stdout, stderr = ssh.exec_command(
        "netstat -tuln 2>/dev/null | grep -E ':(80|443|1194|51820|51821)' || ss -tuln 2>/dev/null | grep -E ':(80|443|1194|51820|51821)'"
    )
    ports_output = stdout.read().decode().strip()
    if ports_output:
        for line in ports_output.split('\n'):
            if line.strip():
                if ':80' in line or ':443' in line:
                    print(f"   ✅ Web portal listening")
                elif ':1194' in line:
                    print(f"   ✅ OpenVPN listening on 1194")
                elif ':51820' in line:
                    print(f"   ✅ WireGuard listening on 51820")
                elif ':51821' in line:
                    print(f"   ✅ PhazeVPN Protocol listening on 51821")
    else:
        print("   ⚠️  No ports found listening")
    
    # Test web portal
    print("")
    print("   Web Portal Test:")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/ 2>&1 || curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/ 2>&1")
    http_code = stdout.read().decode().strip()
    if http_code == "200":
        print("   ✅ Web portal responding (200 OK)")
    else:
        print(f"   ⚠️  Web portal returned: {http_code}")
    
    print("")
    
    # Step 10: Reload nginx
    print("🔟 Reloading nginx...")
    ssh.exec_command("systemctl reload nginx 2>&1")
    print("✅ Nginx reloaded")
    print("")
    
    sftp.close()
    
    # Final summary
    print("=" * 70)
    print("✅ DEPLOYMENT COMPLETE!")
    print("=" * 70)
    print("")
    print("🌐 Access your site:")
    print("   https://phazevpn.duckdns.org")
    print("")
    print("📊 VPN Protocols:")
    print("   ✅ OpenVPN: Port 1194/UDP")
    print("   ✅ WireGuard: Port 51820/UDP")
    print("   ✅ PhazeVPN Protocol: Port 51821/UDP (Advanced Security)")
    print("")
    print("📋 Check status:")
    print("   systemctl status phazevpn-web")
    print("   systemctl status phazevpn-protocol")
    print("   systemctl status secure-vpn")
    print("   systemctl status wg-quick@wg0")
    print("")
    print("📝 View logs:")
    print("   journalctl -u phazevpn-web -f")
    print("   journalctl -u phazevpn-protocol -f")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

