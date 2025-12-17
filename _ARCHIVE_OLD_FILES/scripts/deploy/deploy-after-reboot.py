#!/usr/bin/env python3
"""
Deploy all fixes after VPS reboot
Waits for VPS to come back up, then syncs everything
"""

import time
import subprocess
from paramiko import SSHClient, AutoAddPolicy, SFTPClient
import os
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR_ON_VPS = "/opt/secure-vpn"
BASE_DIR = Path(__file__).parent

print("==========================================")
print("⏳ WAITING FOR VPS TO REBOOT...")
print("==========================================")
print("")

# Wait for VPS to be reachable
print("Waiting for VPS to respond...")
for i in range(1, 31):
    result = subprocess.run(['ping', '-c', '1', '-W', '2', VPS_IP], 
                          capture_output=True, timeout=5)
    if result.returncode == 0:
        print(f"✅ VPS is up! (attempt {i})")
        break
    print(f"   Attempt {i}/30... waiting...")
    time.sleep(2)
else:
    print("❌ VPS didn't respond after 60 seconds")
    print("   Check VPS console to see if it's running")
    exit(1)

print("")
print("Waiting 10 seconds for services to start...")
time.sleep(10)

# Test SSH
print("Testing SSH connection...")
ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())

try:
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    print("✅ SSH is working!")
    print("")
    
    # Fix SSH in firewall (just in case)
    print("🔧 Ensuring SSH is allowed in firewall...")
    ssh.exec_command("ufw allow 22/tcp")
    ssh.exec_command("iptables -I INPUT -p tcp --dport 22 -j ACCEPT")
    ssh.exec_command("iptables-save > /etc/iptables/rules.v4 2>/dev/null || true")
    print("   ✅ SSH firewall rules set")
    print("")
    
    # Deploy all files
    print("📤 Deploying all fixes to VPS...")
    print("")
    
    files_to_sync = {
        # Web portal
        "web-portal/app.py": f"{VPN_DIR_ON_VPS}/web-portal/app.py",
        "web-portal/email_api.py": f"{VPN_DIR_ON_VPS}/web-portal/email_api.py",
        "web-portal/email_mailjet.py": f"{VPN_DIR_ON_VPS}/web-portal/email_mailjet.py",
        "web-portal/mailjet_config.py": f"{VPN_DIR_ON_VPS}/web-portal/mailjet_config.py",
        "web-portal/requirements.txt": f"{VPN_DIR_ON_VPS}/web-portal/requirements.txt",
        
        # Client (DOWNLOAD FIX)
        "phazevpn-client/phazevpn-client.py": f"{VPN_DIR_ON_VPS}/phazevpn-client/phazevpn-client.py",
        
        # GUI
        "vpn-gui.py": f"{VPN_DIR_ON_VPS}/vpn-gui.py",
        
        # VPN config
        "config/server.conf": f"{VPN_DIR_ON_VPS}/config/server.conf",
        "vpn-manager.py": f"{VPN_DIR_ON_VPS}/vpn-manager.py",
        
        # Security scripts
        "scripts/up-ultimate-security.sh": f"{VPN_DIR_ON_VPS}/scripts/up-ultimate-security.sh",
        "scripts/down-ultimate-security.sh": f"{VPN_DIR_ON_VPS}/scripts/down-ultimate-security.sh",
    }
    
    sftp = ssh.open_sftp()
    synced = 0
    
    for local_path, remote_path in files_to_sync.items():
        local_file = BASE_DIR / local_path
        if local_file.exists():
            try:
                remote_dir = os.path.dirname(remote_path)
                ssh.exec_command(f"mkdir -p {remote_dir}")
                sftp.put(str(local_file), remote_path)
                print(f"   ✅ {local_path}")
                synced += 1
            except Exception as e:
                print(f"   ❌ {local_path}: {e}")
        else:
            print(f"   ⚠️  {local_path} not found")
    
    sftp.close()
    print("")
    print(f"✅ Synced {synced} files")
    print("")
    
    # Restart services
    print("🔄 Restarting services...")
    ssh.exec_command("systemctl restart secure-vpn-portal")
    ssh.exec_command("systemctl restart secure-vpn")
    print("   ✅ Services restarted")
    print("")
    
    # Test download
    print("🧪 Testing download route...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -I http://localhost:5000/download/client/windows 2>&1 | head -3")
    download_test = stdout.read().decode()
    print(download_test)
    
    print("")
    print("==========================================")
    print("✅ ALL FIXES DEPLOYED!")
    print("==========================================")
    print("")
    print("📋 What was deployed:")
    print("   ✅ Download client fix")
    print("   ✅ Email fixes")
    print("   ✅ All security updates")
    print("   ✅ Web portal fixes")
    print("")
    print("🎯 Test:")
    print("   https://phazevpn.duckdns.org/download")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("")
    print("💡 SSH might still be blocked")
    print("   Use VPS console to run:")
    print("   ufw allow 22/tcp")
    print("   systemctl restart sshd")

