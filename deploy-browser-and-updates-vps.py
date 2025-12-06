#!/usr/bin/env python3
"""
Deploy Browser and All Updates to VPS
Deploys phazebrowser.py and all web portal updates
"""

import paramiko
import os
from pathlib import Path
import time

# VPS Connection Details
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = 'Jakes1328!@'

def connect_vps():
    """Connect to VPS"""
    print(f"🔌 Connecting to {VPS_HOST} as {VPS_USER}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=15)
        print("✅ Connected successfully!\n")
        return ssh
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        raise

def run_command(ssh, command, description, show_output=True):
    """Run command and show output"""
    print(f"  ⚙️  {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if exit_status == 0:
        print(f"  ✅ Success")
        if show_output and output.strip():
            print(f"     {output.strip()[:300]}")
        return True, output
    else:
        print(f"  ❌ Failed: {error[:200]}")
        return False, error

def upload_file(ssh, local_path, remote_path):
    """Upload file to VPS"""
    print(f"  📤 Uploading {local_path.name}...")
    sftp = ssh.open_sftp()
    try:
        # Create remote directory if needed
        remote_dir = '/'.join(remote_path.split('/')[:-1])
        run_command(ssh, f"mkdir -p {remote_dir}", f"Creating {remote_dir}", show_output=False)
        
        sftp.put(str(local_path), remote_path)
        print(f"  ✅ Uploaded to {remote_path}")
        return True
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return False
    finally:
        sftp.close()

def main():
    print("="*80)
    print("🚀 DEPLOYING BROWSER AND UPDATES TO VPS")
    print("="*80)
    print()
    
    ssh = connect_vps()
    
    try:
        # 1. Pull latest from GitHub
        print("\n📥 [1/6] Pulling latest from GitHub...")
        run_command(ssh, "cd /opt/phaze-vpn && git pull origin main", "Pulling updates")
        
        # 2. Deploy browser
        print("\n🌐 [2/6] Deploying PhazeBrowser...")
        local_browser = Path(__file__).parent / "phazebrowser.py"
        if local_browser.exists():
            upload_file(ssh, local_browser, "/opt/phaze-vpn/phazebrowser.py")
            run_command(ssh, "chmod +x /opt/phaze-vpn/phazebrowser.py", "Making executable")
        else:
            print("  ⚠️  phazebrowser.py not found locally, using git version")
        
        # 3. Deploy web portal updates
        print("\n🌐 [3/6] Deploying Web Portal Updates...")
        web_portal_files = [
            "web-portal/app.py",
            "web-portal/requirements.txt",
            "web-portal/mysql_db.py",
            "web-portal/file_locking.py",
            "web-portal/rate_limiting.py",
        ]
        
        for file_path in web_portal_files:
            local_file = Path(__file__).parent / file_path
            if local_file.exists():
                remote_file = f"/opt/phaze-vpn/{file_path}"
                upload_file(ssh, local_file, remote_file)
        
        # 4. Deploy templates
        print("\n📄 [4/6] Deploying Templates...")
        template_files = [
            "web-portal/templates/base.html",
            "web-portal/templates/login.html",
            "web-portal/templates/signup.html",
            "web-portal/templates/contact.html",
            "web-portal/templates/forgot-password.html",
            "web-portal/templates/reset-password.html",
        ]
        
        for file_path in template_files:
            local_file = Path(__file__).parent / file_path
            if local_file.exists():
                remote_file = f"/opt/phaze-vpn/{file_path}"
                upload_file(ssh, local_file, remote_file)
        
        # 5. Install/Update Python dependencies
        print("\n📦 [5/6] Installing Python Dependencies...")
        run_command(ssh, "cd /opt/phaze-vpn/web-portal && pip3 install -r requirements.txt --upgrade", "Installing dependencies")
        
        # 6. Restart services
        print("\n🔄 [6/6] Restarting Services...")
        run_command(ssh, "systemctl restart phazevpn-portal", "Restarting web portal")
        run_command(ssh, "systemctl restart nginx", "Restarting nginx")
        
        print("\n" + "="*80)
        print("✅ DEPLOYMENT COMPLETE!")
        print("="*80)
        print("\nDeployed:")
        print("  ✅ PhazeBrowser (Ghost Mode + uBlock)")
        print("  ✅ Web Portal Updates")
        print("  ✅ Templates")
        print("  ✅ Dependencies")
        print("  ✅ Services Restarted")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        raise
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

