#!/usr/bin/env python3
"""
Deploy latest code to VPS and ensure everything is working
"""

from paramiko import SSHClient, AutoAddPolicy, SFTPClient
from pathlib import Path
import os
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR_ON_VPS = "/opt/secure-vpn"
BASE_DIR = Path(__file__).parent

print("=" * 70)
print("🚀 DEPLOYING LATEST CODE TO VPS")
print("=" * 70)
print("")

# Files to sync
files_to_sync = {
    # Web Portal - Core Files
    "web-portal/app.py": f"{VPN_DIR_ON_VPS}/web-portal/app.py",
    "web-portal/email_api.py": f"{VPN_DIR_ON_VPS}/web-portal/email_api.py",
    "web-portal/email_mailjet.py": f"{VPN_DIR_ON_VPS}/web-portal/email_mailjet.py",
    "web-portal/email_smtp.py": f"{VPN_DIR_ON_VPS}/web-portal/email_smtp.py",
    "web-portal/email_outlook_oauth2.py": f"{VPN_DIR_ON_VPS}/web-portal/email_outlook_oauth2.py",
    "web-portal/mailjet_config.py": f"{VPN_DIR_ON_VPS}/web-portal/mailjet_config.py",
    "web-portal/smtp_config.py": f"{VPN_DIR_ON_VPS}/web-portal/smtp_config.py",
    "web-portal/outlook_oauth2_config.py": f"{VPN_DIR_ON_VPS}/web-portal/outlook_oauth2_config.py",
    "web-portal/payment_integrations.py": f"{VPN_DIR_ON_VPS}/web-portal/payment_integrations.py",
    "web-portal/secure_auth.py": f"{VPN_DIR_ON_VPS}/web-portal/secure_auth.py",
    "web-portal/requirements.txt": f"{VPN_DIR_ON_VPS}/web-portal/requirements.txt",
    
    # Web Portal - Templates (all of them)
    "web-portal/templates/base.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/base.html",
    "web-portal/templates/home.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/home.html",
    "web-portal/templates/login.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/login.html",
    "web-portal/templates/signup.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/signup.html",
    "web-portal/templates/dashboard.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/dashboard.html",
    "web-portal/templates/error.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/error.html",
    "web-portal/templates/faq.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/faq.html",
    "web-portal/templates/privacy-policy.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/privacy-policy.html",
    "web-portal/templates/terms.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/terms.html",
    "web-portal/templates/contact.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/contact.html",
    "web-portal/templates/blog.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/blog.html",
    "web-portal/templates/download.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/download.html",
    "web-portal/templates/pricing.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/pricing.html",
    "web-portal/templates/guide.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/guide.html",
    "web-portal/templates/forgot-password.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/forgot-password.html",
    "web-portal/templates/reset-password.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/reset-password.html",
    "web-portal/templates/profile.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/profile.html",
    "web-portal/templates/payment.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/payment.html",
    "web-portal/templates/payment-success.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/payment-success.html",
    "web-portal/templates/sitemap.xml": f"{VPN_DIR_ON_VPS}/web-portal/templates/sitemap.xml",
    
    # Admin templates
    "web-portal/templates/admin/dashboard.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/admin/dashboard.html",
    "web-portal/templates/admin/clients.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/admin/clients.html",
    "web-portal/templates/admin/users.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/admin/users.html",
    "web-portal/templates/admin/analytics.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/admin/analytics.html",
    "web-portal/templates/admin/activity.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/admin/activity.html",
    "web-portal/templates/admin/payments.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/admin/payments.html",
    "web-portal/templates/admin/payment-settings.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/admin/payment-settings.html",
    
    # User templates
    "web-portal/templates/user/dashboard.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/user/dashboard.html",
    
    # Moderator templates
    "web-portal/templates/moderator/dashboard.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/moderator/dashboard.html",
    
    # VPN Manager
    "vpn-manager.py": f"{VPN_DIR_ON_VPS}/vpn-manager.py",
    "config/server.conf": f"{VPN_DIR_ON_VPS}/config/server.conf",
}

try:
    print("📡 Connecting to VPS...")
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("   ✅ Connected!")
    print("")
    
    # Stop all Flask processes to avoid conflicts
    print("🛑 Stopping existing Flask processes...")
    ssh.exec_command("pkill -f 'app.py'")
    time.sleep(2)
    print("   ✅ Stopped")
    print("")
    
    # Create directories
    print("📁 Creating directories...")
    dirs_to_create = [
        f"{VPN_DIR_ON_VPS}/web-portal/templates/admin",
        f"{VPN_DIR_ON_VPS}/web-portal/templates/user",
        f"{VPN_DIR_ON_VPS}/web-portal/templates/moderator",
        f"{VPN_DIR_ON_VPS}/web-portal/templates/mobile",
        f"{VPN_DIR_ON_VPS}/config",
    ]
    for dir_path in dirs_to_create:
        ssh.exec_command(f"mkdir -p '{dir_path}'")
    print("   ✅ Directories ready")
    print("")
    
    # Sync files
    print("📤 Syncing files...")
    sftp = ssh.open_sftp()
    synced_count = 0
    skipped_count = 0
    
    try:
        for local_path, remote_path in files_to_sync.items():
            local_file = BASE_DIR / local_path
            if local_file.exists():
                print(f"   📄 {local_path}")
                # Create remote directory if needed
                remote_dir = os.path.dirname(remote_path)
                ssh.exec_command(f"mkdir -p '{remote_dir}'")
                # Upload file
                sftp.put(str(local_file), remote_path)
                # Make scripts executable
                if local_path.endswith('.sh') or local_path.endswith('.py'):
                    ssh.exec_command(f"chmod +x '{remote_path}'")
                synced_count += 1
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
        f"cd {VPN_DIR_ON_VPS}/web-portal && pip3 install -q -r requirements.txt 2>&1"
    )
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        print("   ✅ Packages installed")
    else:
        error = stderr.read().decode()
        print(f"   ⚠️  Warning: {error[:200]}")
    print("")
    
    # Restart web portal using systemd
    print("🔄 Restarting web portal service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl restart phazevpn-web 2>&1")
    restart_output = stdout.read().decode().strip()
    
    if restart_output:
        print(f"   {restart_output}")
    
    time.sleep(3)
    
    # Verify it's running
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1")
    service_status = stdout.read().decode().strip()
    
    if service_status == "active":
        print("   ✅ Service is active")
    else:
        print(f"   ⚠️  Service status: {service_status}")
        print("   💡 Starting service manually...")
        ssh.exec_command(f"cd {VPN_DIR_ON_VPS}/web-portal && nohup python3 app.py > /tmp/web-portal.log 2>&1 &")
        time.sleep(2)
    
    print("")
    
    # Reload nginx
    print("🔄 Reloading nginx...")
    ssh.exec_command("systemctl reload nginx")
    print("   ✅ Nginx reloaded")
    print("")
    
    # Test
    print("🧪 Testing site...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' -k https://127.0.0.1/ 2>&1")
    http_code = stdout.read().decode().strip()
    
    if http_code == "200":
        print("   ✅ Site is responding (200 OK)")
    else:
        print(f"   ⚠️  Site returned: {http_code}")
    print("")
    
    print("=" * 70)
    print("✅ DEPLOYMENT COMPLETE!")
    print("=" * 70)
    print("")
    print("🌐 Test the site:")
    print("   https://phazevpn.duckdns.org")
    print("")
    print("📋 Check status:")
    print("   systemctl status phazevpn-web")
    print("   tail -f /tmp/web-portal.log")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

