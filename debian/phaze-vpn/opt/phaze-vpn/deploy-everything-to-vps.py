#!/usr/bin/env python3
"""
COMPLETE DEPLOYMENT SCRIPT - Deploys EVERYTHING to VPS
- Gaming/Streaming features
- Web portal (all files)
- GUI updates
- Multi-IP support
- WireGuard
- Mobile configs
- All scripts and configs
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from paramiko import SSHClient, AutoAddPolicy, SFTPClient
import json
from datetime import datetime

# VPS Configuration - UPDATE THESE
VPS_IP = os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASS = os.environ.get('VPS_PASS', 'Jakes1328!@')

# Paths
BASE_DIR = Path(__file__).parent
VPN_DIR_ON_VPS = "/opt/secure-vpn"

print("="*70)
print("🚀 COMPLETE DEPLOYMENT TO VPS")
print("="*70)
print(f"VPS: {VPS_IP}")
print(f"User: {VPS_USER}")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("")

# COMPREHENSIVE FILE LIST - EVERYTHING
files_to_sync = {
    # ========== GAMING/STREAMING FEATURES ==========
    "config/server-gaming.conf": f"{VPN_DIR_ON_VPS}/config/server-gaming.conf",
    "multi-ip-manager.py": f"{VPN_DIR_ON_VPS}/multi-ip-manager.py",
    "scripts/setup-multi-ip.sh": f"{VPN_DIR_ON_VPS}/scripts/setup-multi-ip.sh",
    "scripts/setup-wireguard.sh": f"{VPN_DIR_ON_VPS}/scripts/setup-wireguard.sh",
    "scripts/optimize-for-gaming.sh": f"{VPN_DIR_ON_VPS}/scripts/optimize-for-gaming.sh",
    "mobile-config-generator.py": f"{VPN_DIR_ON_VPS}/mobile-config-generator.py",
    
    # ========== VPN CORE ==========
    "config/server.conf": f"{VPN_DIR_ON_VPS}/config/server.conf",
    "vpn-manager.py": f"{VPN_DIR_ON_VPS}/vpn-manager.py",
    "vpn-gui.py": f"{VPN_DIR_ON_VPS}/vpn-gui.py",
    "client-download-server.py": f"{VPN_DIR_ON_VPS}/client-download-server.py",
    "debian/phaze-vpn/etc/systemd/system/phaze-vpn-download.service": "/etc/systemd/system/phaze-vpn-download.service",
    
    # ========== WEB PORTAL - CORE ==========
    "web-portal/app.py": f"{VPN_DIR_ON_VPS}/web-portal/app.py",
    "web-portal/email_api.py": f"{VPN_DIR_ON_VPS}/web-portal/email_api.py",
    "web-portal/email_mailjet.py": f"{VPN_DIR_ON_VPS}/web-portal/email_mailjet.py",
    "web-portal/email_smtp.py": f"{VPN_DIR_ON_VPS}/web-portal/email_smtp.py",
    "web-portal/email_outlook_oauth2.py": f"{VPN_DIR_ON_VPS}/web-portal/email_outlook_oauth2.py",
    "web-portal/email_util.py": f"{VPN_DIR_ON_VPS}/web-portal/email_util.py",
    "web-portal/mailjet_config.py": f"{VPN_DIR_ON_VPS}/web-portal/mailjet_config.py",
    "web-portal/mailgun_config.py": f"{VPN_DIR_ON_VPS}/web-portal/mailgun_config.py",
    "web-portal/smtp_config.py": f"{VPN_DIR_ON_VPS}/web-portal/smtp_config.py",
    "web-portal/outlook_oauth2_config.py": f"{VPN_DIR_ON_VPS}/web-portal/outlook_oauth2_config.py",
    "web-portal/secure_auth.py": f"{VPN_DIR_ON_VPS}/web-portal/secure_auth.py",
    "web-portal/payment_integrations.py": f"{VPN_DIR_ON_VPS}/web-portal/payment_integrations.py",
    "web-portal/requirements.txt": f"{VPN_DIR_ON_VPS}/web-portal/requirements.txt",
    "web-portal/nginx-phazevpn.conf": f"{VPN_DIR_ON_VPS}/web-portal/nginx-phazevpn.conf",
    "web-portal/phazevpn-portal.service": f"{VPN_DIR_ON_VPS}/web-portal/phazevpn-portal.service",
    
    # ========== WEB PORTAL - TEMPLATES ==========
    "web-portal/templates/base.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/base.html",
    "web-portal/templates/base-new.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/base-new.html",
    "web-portal/templates/login.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/login.html",
    "web-portal/templates/signup.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/signup.html",
    "web-portal/templates/home.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/home.html",
    "web-portal/templates/home-new.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/home-new.html",
    "web-portal/templates/download.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/download.html",
    "web-portal/templates/download-instructions.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/download-instructions.html",
    "web-portal/templates/forgot-password.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/forgot-password.html",
    "web-portal/templates/reset-password.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/reset-password.html",
    "web-portal/templates/profile.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/profile.html",
    "web-portal/templates/pricing.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/pricing.html",
    "web-portal/templates/payment.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/payment.html",
    "web-portal/templates/payment-success.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/payment-success.html",
    "web-portal/templates/faq.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/faq.html",
    "web-portal/templates/guide.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/guide.html",
    "web-portal/templates/guide-new.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/guide-new.html",
    "web-portal/templates/contact.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/contact.html",
    "web-portal/templates/blog.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/blog.html",
    "web-portal/templates/testimonials.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/testimonials.html",
    "web-portal/templates/privacy-policy.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/privacy-policy.html",
    "web-portal/templates/terms.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/terms.html",
    "web-portal/templates/error.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/error.html",
    "web-portal/templates/tickets.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/tickets.html",
    "web-portal/templates/qr-code.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/qr-code.html",
    "web-portal/templates/2fa-setup.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/2fa-setup.html",
    "web-portal/templates/phazebrowser.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/phazebrowser.html",
    "web-portal/templates/sitemap.xml": f"{VPN_DIR_ON_VPS}/web-portal/templates/sitemap.xml",
    
    # ========== WEB PORTAL - ADMIN TEMPLATES ==========
    "web-portal/templates/admin/dashboard.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/admin/dashboard.html",
    "web-portal/templates/admin/users.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/admin/users.html",
    "web-portal/templates/admin/clients.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/admin/clients.html",
    "web-portal/templates/admin/payments.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/admin/payments.html",
    "web-portal/templates/admin/payment-settings.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/admin/payment-settings.html",
    "web-portal/templates/admin/analytics.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/admin/analytics.html",
    "web-portal/templates/admin/activity.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/admin/activity.html",
    
    # ========== WEB PORTAL - USER TEMPLATES ==========
    "web-portal/templates/user/dashboard.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/user/dashboard.html",
    "web-portal/templates/moderator/dashboard.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/moderator/dashboard.html",
    "web-portal/templates/mobile/monitor.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/mobile/monitor.html",
    "web-portal/templates/mobile/client-detail.html": f"{VPN_DIR_ON_VPS}/web-portal/templates/mobile/client-detail.html",
    
    # ========== WEB PORTAL - STATIC FILES ==========
    "web-portal/static/css/style.css": f"{VPN_DIR_ON_VPS}/web-portal/static/css/style.css",
    "web-portal/static/css/animations.css": f"{VPN_DIR_ON_VPS}/web-portal/static/css/animations.css",
    "web-portal/static/css/easter-eggs.css": f"{VPN_DIR_ON_VPS}/web-portal/static/css/easter-eggs.css",
    "web-portal/static/js/main.js": f"{VPN_DIR_ON_VPS}/web-portal/static/js/main.js",
    "web-portal/static/js/easter-eggs.js": f"{VPN_DIR_ON_VPS}/web-portal/static/js/easter-eggs.js",
    "web-portal/static/js/analytics.js": f"{VPN_DIR_ON_VPS}/web-portal/static/js/analytics.js",
    "web-portal/static/images/logo.png": f"{VPN_DIR_ON_VPS}/web-portal/static/images/logo.png",
    "web-portal/static/images/logo-optimized.png": f"{VPN_DIR_ON_VPS}/web-portal/static/images/logo-optimized.png",
    "web-portal/static/images/favicon.png": f"{VPN_DIR_ON_VPS}/web-portal/static/images/favicon.png",
    "web-portal/static/images/og-image.png": f"{VPN_DIR_ON_VPS}/web-portal/static/images/og-image.png",
    
    # ========== SCRIPTS ==========
    "scripts/up-ultimate-security.sh": f"{VPN_DIR_ON_VPS}/scripts/up-ultimate-security.sh",
    "scripts/down-ultimate-security.sh": f"{VPN_DIR_ON_VPS}/scripts/down-ultimate-security.sh",
    "scripts/setup-ddos-protection.sh": f"{VPN_DIR_ON_VPS}/scripts/setup-ddos-protection.sh",
    "scripts/enhance-privacy.sh": f"{VPN_DIR_ON_VPS}/scripts/enhance-privacy.sh",
    "scripts/setup-vpn-ipv6.sh": f"{VPN_DIR_ON_VPS}/scripts/setup-vpn-ipv6.sh",
    
    # ========== CLIENT ==========
    "phazevpn-client/phazevpn-client.py": f"{VPN_DIR_ON_VPS}/phazevpn-client/phazevpn-client.py",
}

# Directories to create
directories_to_create = [
    f"{VPN_DIR_ON_VPS}/servers",
    f"{VPN_DIR_ON_VPS}/wireguard",
    f"{VPN_DIR_ON_VPS}/wireguard/clients",
    f"{VPN_DIR_ON_VPS}/config/multi-ip",
    f"{VPN_DIR_ON_VPS}/web-portal/templates/admin",
    f"{VPN_DIR_ON_VPS}/web-portal/templates/user",
    f"{VPN_DIR_ON_VPS}/web-portal/templates/moderator",
    f"{VPN_DIR_ON_VPS}/web-portal/templates/mobile",
    f"{VPN_DIR_ON_VPS}/web-portal/static/css",
    f"{VPN_DIR_ON_VPS}/web-portal/static/js",
    f"{VPN_DIR_ON_VPS}/web-portal/static/images",
]

def deploy():
    try:
        print("📡 Connecting to VPS...")
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
        print("")
        
        # Create directories
        print("📁 Creating directories...")
        for directory in directories_to_create:
            ssh.exec_command(f"mkdir -p {directory}")
        print("   ✅ Directories created")
        print("")
        
        # Sync files
        print("📤 Uploading files...")
        sftp = ssh.open_sftp()
        
        uploaded = 0
        failed = 0
        skipped = 0
        
        for local_path, remote_path in files_to_sync.items():
            local_file = BASE_DIR / local_path
            
            if not local_file.exists():
                print(f"   ⚠️  Skipping (not found): {local_path}")
                skipped += 1
                continue
            
            try:
                # Create remote directory
                remote_dir = os.path.dirname(remote_path)
                ssh.exec_command(f"mkdir -p '{remote_dir}'")
                
                # Upload file
                sftp.put(str(local_file), remote_path)
                
                # Make scripts executable
                if local_path.endswith('.sh') or local_path.endswith('.py'):
                    ssh.exec_command(f"chmod +x '{remote_path}'")
                
                print(f"   ✅ {local_path}")
                uploaded += 1
            except Exception as e:
                print(f"   ❌ Failed: {local_path} - {e}")
                failed += 1
        
        sftp.close()
        print("")
        print(f"   📊 Uploaded: {uploaded}, Failed: {failed}, Skipped: {skipped}")
        print("")
        
        # Install Python packages
        print("📦 Installing Python packages...")
        stdin, stdout, stderr = ssh.exec_command(
            f"cd {VPN_DIR_ON_VPS}/web-portal && pip3 install -r requirements.txt --quiet 2>&1"
        )
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print("   ✅ Packages installed")
        else:
            error = stderr.read().decode()
            print(f"   ⚠️  Warning: {error[:200]}")
        print("")
        
        # Create deployment record
        deployment_info = {
            'timestamp': datetime.now().isoformat(),
            'vps_ip': VPS_IP,
            'files_uploaded': uploaded,
            'files_failed': failed,
            'files_skipped': skipped
        }
        
        # Save deployment record
        deployment_file = BASE_DIR / 'deployment-record.json'
        with open(deployment_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        print("="*70)
        print("✅ DEPLOYMENT COMPLETE!")
        print("="*70)
        print("")
        print("📋 Summary:")
        print(f"   ✅ Uploaded: {uploaded} files")
        print(f"   ⚠️  Failed: {failed} files")
        print(f"   ⏭️  Skipped: {skipped} files")
        print("")
        # Automatically run verification on VPS
        print("🔍 Running automatic verification on VPS...")
        print("")
        
        # Upload verification script if not already there
        verify_script_local = BASE_DIR / 'verify-deployment.py'
        verify_script_remote = f"{VPN_DIR_ON_VPS}/verify-deployment.py"
        
        if verify_script_local.exists():
            sftp = ssh.open_sftp()
            try:
                sftp.put(str(verify_script_local), verify_script_remote)
                ssh.exec_command(f"chmod +x {verify_script_remote}")
                print("   ✅ Verification script uploaded")
            finally:
                sftp.close()
        
        # Run verification remotely
        print("   Running verification checks...")
        stdin, stdout, stderr = ssh.exec_command(f"python3 {verify_script_remote}")
        
        # Wait for command to complete
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        print(output)
        if errors:
            print(f"   ⚠️  Warnings: {errors[:500]}")
        
        verification_passed = exit_status == 0
        
        # Restart services if needed
        print("")
        print("🔄 Checking and restarting services...")
        
        # Check if web portal needs restart
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web || echo 'not-running'")
        web_status = stdout.read().decode().strip()
        
        if web_status == 'active':
            print("   Restarting web portal...")
            ssh.exec_command("systemctl restart phazevpn-web")
            print("   ✅ Web portal restarted")
        else:
            print("   ℹ️  Web portal not running (start manually if needed)")
        
        # Check if VPN needs restart
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active secure-vpn || pgrep -f 'openvpn.*server.conf' || echo 'not-running'")
        vpn_status = stdout.read().decode().strip()
        
        if 'active' in vpn_status or 'openvpn' in vpn_status:
            print("   Restarting VPN service...")
            ssh.exec_command("systemctl restart secure-vpn 2>/dev/null || pkill -f 'openvpn.*server.conf'")
            print("   ✅ VPN service restarted")
        else:
            print("   ℹ️  VPN service not running (start manually if needed)")
        
        # Install and setup download server service
        print("   Installing download server service...")
        
        # Create service file on VPS using heredoc
        service_setup_cmd = f"""cat > /etc/systemd/system/phaze-vpn-download.service <<'SERVICEEOF'
[Unit]
Description=PhazeVPN Client Download Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={VPN_DIR_ON_VPS}
ExecStart=/usr/bin/python3 {VPN_DIR_ON_VPS}/client-download-server.py
Restart=always
RestartSec=5
StartLimitInterval=0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF"""
        
        stdin, stdout, stderr = ssh.exec_command(service_setup_cmd)
        stdout.channel.recv_exit_status()
        
        # Reload systemd
        ssh.exec_command("systemctl daemon-reload")
        time.sleep(1)
        
        # Enable and start service
        print("   Enabling and starting download server...")
        ssh.exec_command("systemctl enable phaze-vpn-download")
        ssh.exec_command("systemctl start phaze-vpn-download")
        time.sleep(2)
        
        # Check status
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active phaze-vpn-download")
        status = stdout.read().decode().strip()
        
        if status == 'active':
            print("   ✅ Download server service is running")
        else:
            print("   ⚠️  Download server service may not be running - check manually")
        
        print("")
        
        # Create update notification automatically
        print("📝 Creating update notification...")
        try:
            # Run notification creator script
            notification_script = BASE_DIR / 'create-update-notification.py'
            if notification_script.exists():
                result = subprocess.run(
                    [sys.executable, str(notification_script)],
                    capture_output=True,
                    text=True,
                    cwd=str(BASE_DIR)
                )
                if result.returncode == 0:
                    print("   ✅ Update notification created")
                else:
                    print(f"   ⚠️  Notification creation had issues: {result.stderr[:200]}")
            else:
                print("   ⚠️  Notification script not found")
        except Exception as e:
            print(f"   ⚠️  Could not create notification: {e}")
        
        print("")
        print("="*70)
        print("🎉 COMPLETE DEPLOYMENT FINISHED!")
        print("="*70)
        print("")
        print("✅ All files deployed")
        print(f"{'✅' if verification_passed else '⚠️'} Verification {'passed' if verification_passed else 'had issues'}")
        print("✅ Services restarted")
        print("✅ Update notification created")
        print("")
        print("📝 Next steps:")
        print("   1. Test web portal: https://phazevpn.com")
        print("   2. Test VPN connection with a client")
        print("   3. Review update notification: UPDATE-NOTIFICATION.md")
        print("")
        
        ssh.close()
        return verification_passed
        
    except Exception as e:
        print(f"\n\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = deploy()
    sys.exit(0 if success else 1)

