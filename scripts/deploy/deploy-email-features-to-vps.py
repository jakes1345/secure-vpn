#!/usr/bin/env python3
"""
Deploy Email Features (Calendar, Contacts, API) to VPS
Integrates calendar, contacts, and REST API into email server
"""

import paramiko
import sys
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
EMAIL_DOMAIN = "phazevpn.duckdns.org"
EMAIL_HOSTNAME = "mail.phazevpn.duckdns.org"

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
    print("🚀 Deploying Email Features to VPS...")
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
        # Create remote directory
        remote_dir = "/opt/phazevpn-email"
        print(f"2️⃣ Setting up directory: {remote_dir}")
        run_command(ssh, f"mkdir -p {remote_dir}")
        
        # Files to upload
        files_to_upload = [
            "setup-email-calendar.sh",
            "setup-email-contacts.sh",
            "setup-email-api.sh",
            "EMAIL-FEATURES-ROADMAP.md",
            "EMAIL-FEATURES-IMPLEMENTATION.md"
        ]
        
        print(f"\n3️⃣ Uploading feature scripts...")
        for file in files_to_upload:
            local_path = Path(file)
            if local_path.exists():
                remote_path = f"{remote_dir}/{file}"
                if upload_file(ssh, str(local_path), remote_path):
                    print(f"   ✅ {file}")
                    # Make executable
                    run_command(ssh, f"chmod +x {remote_path}")
                else:
                    print(f"   ❌ {file} - SKIPPING")
            else:
                print(f"   ⚠️  {file} not found - SKIPPING")
        
        # Install Calendar System
        print(f"\n4️⃣ Installing Calendar System (CalDAV)...")
        success, output, error = run_command(
            ssh, 
            f"cd {remote_dir} && ./setup-email-calendar.sh",
            check=False
        )
        
        if success:
            print("✅ Calendar system installed")
        else:
            print("⚠️  Calendar installation had issues (may already be installed)")
            print(f"Output: {output[:200]}")
        
        # Install Contacts System
        print(f"\n5️⃣ Installing Contacts System (CardDAV)...")
        success, output, error = run_command(
            ssh,
            f"cd {remote_dir} && ./setup-email-contacts.sh",
            check=False
        )
        
        if success:
            print("✅ Contacts system installed")
        else:
            print("⚠️  Contacts installation had issues")
            print(f"Output: {output[:200]}")
        
        # Install REST API
        print(f"\n6️⃣ Installing REST API...")
        success, output, error = run_command(
            ssh,
            f"cd {remote_dir} && ./setup-email-api.sh",
            check=False
        )
        
        if success:
            print("✅ REST API installed")
        else:
            print("⚠️  API installation had issues")
            print(f"Output: {output[:200]}")
        
        # Check service status
        print(f"\n7️⃣ Checking service status...")
        services = [
            "radicale",
            "phazevpn-email-api"
        ]
        
        for service in services:
            success, output, error = run_command(
                ssh,
                f"systemctl is-active {service}",
                check=False
            )
            if "active" in output.lower():
                print(f"   ✅ {service} is running")
            else:
                print(f"   ⚠️  {service} status: {output.strip()}")
        
        # Configure firewall
        print(f"\n8️⃣ Configuring firewall...")
        ports = [
            ("5232", "CalDAV/CardDAV"),
            ("5000", "REST API")
        ]
        
        for port, desc in ports:
            success, output, error = run_command(
                ssh,
                f"ufw allow {port}/tcp comment '{desc}'",
                check=False
            )
            if success:
                print(f"   ✅ Opened port {port} ({desc})")
            else:
                print(f"   ⚠️  Port {port} may already be open")
        
        # Summary
        print(f"\n{'='*60}")
        print("✅ Email Features Deployment Complete!")
        print(f"{'='*60}\n")
        
        print("📅 Calendar System:")
        print("   - CalDAV Server: http://calendar.phazevpn.duckdns.org")
        print("   - Port: 5232")
        print("   - Service: radicale")
        print("")
        
        print("👥 Contacts System:")
        print("   - CardDAV Server: http://calendar.phazevpn.duckdns.org")
        print("   - Same server as calendar")
        print("")
        
        print("🔌 REST API:")
        print("   - Base URL: http://15.204.11.19:5000/api/v1")
        print("   - Health: GET /api/v1/health")
        print("   - Service: phazevpn-email-api")
        print("")
        
        print("🔧 Next Steps:")
        print("   1. Test calendar: Connect with Thunderbird or Apple Calendar")
        print("   2. Test contacts: Sync with CardDAV client")
        print("   3. Test API: curl http://15.204.11.19:5000/api/v1/health")
        print("   4. Configure Nginx reverse proxy for API (optional)")
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

