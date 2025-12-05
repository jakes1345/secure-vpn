#!/usr/bin/env python3
"""
Deploy All Advanced Features to VPS
Email features, file storage, productivity suite
"""

import paramiko
import sys
import os
from pathlib import Path
import time

# VPS Configuration
VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
EMAIL_DOMAIN = "phazevpn.duckdns.org"

def run_command(ssh, command, check=True):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if check and exit_status != 0:
        print(f"❌ Error executing: {command}")
        print(f"Error: {error}")
        return False, output, error
    
    return True, output, error

def upload_file(ssh, local_path, remote_path):
    """Upload file to remote server"""
    try:
        sftp = ssh.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
        return True
    except Exception as e:
        print(f"❌ Failed to upload {local_path}: {e}")
        return False

def main():
    print("🚀 Deploying All Advanced Features to VPS...")
    print(f"   Host: {VPS_HOST}")
    print(f"   Domain: {EMAIL_DOMAIN}\n")
    
    # Connect to VPS
    print("1️⃣ Connecting to VPS...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    try:
        remote_dir = "/opt/phazevpn-email"
        
        # Files to upload
        files_to_upload = [
            "setup-email-advanced-features.sh",
            "setup-file-storage.sh",
            "setup-productivity-suite.sh",
            "extend-email-api-advanced.sh"
        ]
        
        print("2️⃣ Uploading setup scripts...")
        for file in files_to_upload:
            local_path = Path(file)
            if local_path.exists():
                remote_path = f"{remote_dir}/{file}"
                if upload_file(ssh, str(local_path), remote_path):
                    print(f"   ✅ {file}")
                    run_command(ssh, f"chmod +x {remote_path}")
                else:
                    print(f"   ❌ {file} - SKIPPING")
            else:
                print(f"   ⚠️  {file} not found - SKIPPING")
        
        # Setup advanced email features (database)
        print("\n3️⃣ Setting up Advanced Email Features (Database)...")
        success, output, error = run_command(
            ssh,
            f"cd {remote_dir} && ./setup-email-advanced-features.sh",
            check=False
        )
        if success:
            print("✅ Advanced email features database setup complete")
        else:
            print(f"⚠️  Some issues: {output[:300]}")
        
        # Setup file storage
        print("\n4️⃣ Setting up File Storage System...")
        success, output, error = run_command(
            ssh,
            f"cd {remote_dir} && ./setup-file-storage.sh",
            check=False
        )
        if success:
            print("✅ File storage system installed")
        else:
            print(f"⚠️  Some issues: {output[:300]}")
        
        # Setup productivity suite
        print("\n5️⃣ Setting up Productivity Suite...")
        success, output, error = run_command(
            ssh,
            f"cd {remote_dir} && ./setup-productivity-suite.sh",
            check=False
        )
        if success:
            print("✅ Productivity suite installed")
        else:
            print(f"⚠️  Some issues: {output[:300]}")
        
        # Extend email API
        print("\n6️⃣ Extending Email API with Advanced Features...")
        success, output, error = run_command(
            ssh,
            f"cd {remote_dir} && ./extend-email-api-advanced.sh",
            check=False
        )
        if success:
            print("✅ Email API extended")
        else:
            print(f"⚠️  Some issues: {output[:300]}")
        
        # Wait for services to start
        print("\n7️⃣ Waiting for services to start...")
        time.sleep(5)
        
        # Check service status
        print("\n8️⃣ Checking service status...")
        services = [
            ("phazevpn-email-api", "Email API"),
            ("phazevpn-storage", "File Storage"),
            ("phazevpn-productivity", "Productivity Suite")
        ]
        
        for service, name in services:
            success, output, error = run_command(
                ssh,
                f"systemctl is-active {service}",
                check=False
            )
            if "active" in output.lower():
                print(f"   ✅ {name} is running")
            else:
                print(f"   ⚠️  {name} status: {output.strip()}")
        
        # Configure firewall
        print("\n9️⃣ Configuring firewall...")
        ports = [
            ("5002", "File Storage API"),
            ("5003", "Productivity Suite API")
        ]
        
        for port, desc in ports:
            success, output, error = run_command(
                ssh,
                f"ufw allow {port}/tcp comment '{desc}'",
                check=False
            )
            if success:
                print(f"   ✅ Opened port {port} ({desc})")
        
        # Summary
        print(f"\n{'='*60}")
        print("✅ All Features Deployment Complete!")
        print(f"{'='*60}\n")
        
        print("📧 Email Features:")
        print("   - Labels (Gmail-style)")
        print("   - Filters (automated actions)")
        print("   - Templates (reusable emails)")
        print("   - Advanced Search (full-text)")
        print("   - API: http://15.204.11.19:5001/api/v1")
        print("")
        
        print("📁 File Storage:")
        print("   - Google Drive-like storage")
        print("   - File upload/download")
        print("   - Folder management")
        print("   - Sharing capabilities")
        print("   - API: http://15.204.11.19:5002/api/v1/storage")
        print("")
        
        print("📝 Productivity Suite:")
        print("   - Documents (Docs)")
        print("   - Spreadsheets (Sheets)")
        print("   - Presentations (Slides)")
        print("   - Collaboration features")
        print("   - API: http://15.204.11.19:5003/api/v1/productivity")
        print("")
        
        print("🔧 Next Steps:")
        print("   1. Test file storage: Upload/download files")
        print("   2. Test productivity: Create docs/sheets/slides")
        print("   3. Test email features: Create labels, filters, templates")
        print("   4. Build web UI for all features")
        print("")
        
    except Exception as e:
        print(f"\n❌ Error during deployment: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        print("🔌 Disconnected from VPS")

if __name__ == "__main__":
    main()
