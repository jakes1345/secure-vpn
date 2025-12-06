#!/usr/bin/env python3
"""
Deploy all updates to VPS
- Web portal fixes
- Email configuration
- Client enhancements
"""

import os
import sys
from pathlib import Path
from paramiko import SSHClient, AutoAddPolicy, SFTPClient

# VPS Configuration
VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"  # Root password

# Paths
BASE_DIR = Path(__file__).parent
WEB_PORTAL_DIR = BASE_DIR / "web-portal"
VPN_DIR_ON_VPS = "/opt/secure-vpn"

print("==========================================")
print("🚀 DEPLOYING ALL UPDATES TO VPS")
print("==========================================")
print("")

# Files to sync - ALL VPN FILES
files_to_sync = {
    # VPN Server Configs
    "config/server.conf": f"{VPN_DIR_ON_VPS}/config/server.conf",
    "vpn-manager.py": f"{VPN_DIR_ON_VPS}/vpn-manager.py",
    
    # Web Portal - Core Files
    "web-portal/app.py": f"{VPN_DIR_ON_VPS}/web-portal/app.py",
    "web-portal/email_api.py": f"{VPN_DIR_ON_VPS}/web-portal/email_api.py",
    "web-portal/email_mailjet.py": f"{VPN_DIR_ON_VPS}/web-portal/email_mailjet.py",
    "web-portal/mailjet_config.py": f"{VPN_DIR_ON_VPS}/web-portal/mailjet_config.py",
    "web-portal/email_util.py": f"{VPN_DIR_ON_VPS}/web-portal/email_util.py",
    "web-portal/email_smtp.py": f"{VPN_DIR_ON_VPS}/web-portal/email_smtp.py",
    "web-portal/smtp_config.py": f"{VPN_DIR_ON_VPS}/web-portal/smtp_config.py",
    "web-portal/secure_auth.py": f"{VPN_DIR_ON_VPS}/web-portal/secure_auth.py",
    "web-portal/requirements.txt": f"{VPN_DIR_ON_VPS}/web-portal/requirements.txt",
    "web-portal/payment_integrations.py": f"{VPN_DIR_ON_VPS}/web-portal/payment_integrations.py",
    
    # Web Portal - Templates
    "web-portal/templates/login.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/login.html",
    "web-portal/templates/signup.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/signup.html",
    "web-portal/templates/forgot-password.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/forgot-password.html",
    "web-portal/templates/reset-password.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/reset-password.html",
    "web-portal/templates/download.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/download.html",
    "web-portal/templates/base.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/base.html",
    "web-portal/templates/home.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/home.html",
    "web-portal/templates/faq.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/faq.html",
    "web-portal/templates/privacy-policy.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/privacy-policy.html",
    "web-portal/templates/terms.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/terms.html",
    "web-portal/templates/contact.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/contact.html",
    "web-portal/templates/blog.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/blog.html",
    "web-portal/templates/testimonials.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/testimonials.html",
    "web-portal/templates/pricing.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/pricing.html",
    "web-portal/templates/guide.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/guide.html",
    "web-portal/templates/error.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/error.html",
    
    # Client
    "phazevpn-client/phazevpn-client.py": f"{VPN_DIR_ON_VPS}/phazevpn-client/phazevpn-client.py",
    
    # Security Scripts
    "scripts/up-ultimate-security.sh": f"{VPN_DIR_ON_VPS}/scripts/up-ultimate-security.sh",
    "scripts/down-ultimate-security.sh": f"{VPN_DIR_ON_VPS}/scripts/down-ultimate-security.sh",
    "scripts/setup-ddos-protection.sh": f"{VPN_DIR_ON_VPS}/scripts/setup-ddos-protection.sh",
    "scripts/enhance-privacy.sh": f"{VPN_DIR_ON_VPS}/scripts/enhance-privacy.sh",
    "scripts/setup-vpn-ipv6.sh": f"{VPN_DIR_ON_VPS}/scripts/setup-vpn-ipv6.sh",
    
    # GUI
    "vpn-gui.py": f"{VPN_DIR_ON_VPS}/vpn-gui.py",
    
    # Client Download Server
    "client-download-server.py": f"{VPN_DIR_ON_VPS}/client-download-server.py",
}

try:
    print("📡 Connecting to VPS...")
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("   ✅ Connected!")
    print("")
    
    # Create directories if needed
    print("📁 Creating directories...")
    ssh.exec_command(f"mkdir -p {VPN_DIR_ON_VPS}/web-portal/templates")
    ssh.exec_command(f"mkdir -p {VPN_DIR_ON_VPS}/phazevpn-client")
    ssh.exec_command(f"mkdir -p {VPN_DIR_ON_VPS}/config")
    ssh.exec_command(f"mkdir -p {VPN_DIR_ON_VPS}/scripts")
    ssh.exec_command(f"mkdir -p {VPN_DIR_ON_VPS}/logs")
    print("   ✅ Directories ready")
    print("")
    
    # Sync files using SFTP
    print("📤 Syncing files...")
    sftp = ssh.open_sftp()
    synced_count = 0
    skipped_count = 0
    try:
        for local_path, remote_path in files_to_sync.items():
            local_file = BASE_DIR / local_path
            if local_file.exists():
                print(f"   📄 {local_path} → {remote_path}")
                # Create remote directory if needed
                remote_dir = os.path.dirname(remote_path)
                ssh.exec_command(f"mkdir -p '{remote_dir}'")
                # Upload file
                sftp.put(str(local_file), remote_path)
                # Make scripts executable
                if local_path.endswith('.sh'):
                    ssh.exec_command(f"chmod +x '{remote_path}'")
                synced_count += 1
                print(f"      ✅ Synced")
            else:
                print(f"   ⚠️  {local_path} not found (skipping)")
                skipped_count += 1
    finally:
        sftp.close()
    print("")
    print(f"   📊 Synced: {synced_count} files, Skipped: {skipped_count} files")
    print("")
    
    # Install Python packages
    print("📦 Installing Python packages...")
    stdin, stdout, stderr = ssh.exec_command(
        f"cd {VPN_DIR_ON_VPS}/web-portal && pip3 install -r requirements.txt --quiet"
    )
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        print("   ✅ Packages installed")
    else:
        error = stderr.read().decode()
        print(f"   ⚠️  Warning: {error[:200]}")
    print("")
    
    # Restart web portal if running
    print("🔄 Checking web portal service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web || echo 'not-running'")
    service_status = stdout.read().decode().strip()
    
    if service_status == "active":
        print("   🔄 Restarting web portal service...")
        ssh.exec_command("systemctl restart phazevpn-web")
        print("   ✅ Service restarted")
    else:
        print("   ℹ️  Web portal service not running (start manually if needed)")
    print("")
    
    print("==========================================")
    print("✅ DEPLOYMENT COMPLETE!")
    print("==========================================")
    print("")
    print("📋 What was deployed:")
    print("   ✅ VPN server config (server.conf)")
    print("   ✅ VPN manager (vpn-manager.py)")
    print("   ✅ Web portal (all files)")
    print("   ✅ Email API (Mailjet configured)")
    print("   ✅ Security scripts (up/down scripts)")
    print("   ✅ Client files (phazevpn-client.py)")
    print("   ✅ GUI (vpn-gui.py)")
    print("")
    print("📝 Next steps:")
    print("   1. Restart OpenVPN if config changed:")
    print("      systemctl restart openvpn@server")
    print("      OR: pkill openvpn && cd /opt/secure-vpn && openvpn --config config/server.conf --daemon")
    print("")
    print("   2. Restart web portal if needed:")
    print("      pkill -f 'app.py'")
    print("      cd /opt/secure-vpn/web-portal && nohup python3 app.py > /dev/null 2>&1 &")
    print("")
    print("   3. Test everything:")
    print("      - Web portal: https://phazevpn.duckdns.org")
    print("      - VPN connection: Connect a client")
    print("      - Email: Register a new user")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

