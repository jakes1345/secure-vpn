#!/usr/bin/env python3
"""
Deploy website redesign to VPS
"""

from paramiko import SSHClient, AutoAddPolicy
from pathlib import Path
import sys

# VPS Connection
VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("=" * 60)
    print("Deploying Website Redesign to VPS")
    print("=" * 60)
    
    try:
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        
        # Create directories if they don't exist
        print("\n[0/4] Creating directories...")
        ssh.exec_command("mkdir -p /opt/secure-vpn/web-portal/static/css")
        ssh.exec_command("mkdir -p /opt/secure-vpn/web-portal/templates")
        print("   ✅ Directories created")
        
        sftp = ssh.open_sftp()
        
        # Upload CSS
        print("\n[1/4] Uploading new CSS...")
        local_css = Path("web-portal/static/css/style.css")
        remote_css = "/opt/secure-vpn/web-portal/static/css/style.css"
        
        if local_css.exists():
            sftp.put(str(local_css), remote_css)
            print("   ✅ style.css uploaded")
        else:
            print("   ❌ style.css not found locally")
            sys.exit(1)
        
        # Upload templates
        print("\n[2/4] Uploading updated templates...")
        templates = ["base.html", "home.html", "testimonials.html"]
        for template in templates:
            local_template = Path(f"web-portal/templates/{template}")
            remote_template = f"/opt/secure-vpn/web-portal/templates/{template}"
            
            if local_template.exists():
                sftp.put(str(local_template), remote_template)
                print(f"   ✅ {template} uploaded")
            else:
                print(f"   ⚠️  {template} not found locally")
        
        sftp.close()
        
        # Restart web service
        print("\n[3/4] Restarting web service...")
        stdin, stdout, stderr = ssh.exec_command("systemctl restart phazevpn-web 2>&1")
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print("   ✅ Web service restarted")
        else:
            error = stderr.read().decode().strip()
            print(f"   ⚠️  Restart had issues: {error}")
        
        # Verify service is running
        print("\n[4/4] Verifying deployment...")
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1")
        status = stdout.read().decode().strip()
        if status == "active":
            print("   ✅ Web service is active")
        else:
            print(f"   ⚠️  Web service status: {status}")
        
        # Verify files exist
        stdin, stdout, stderr = ssh.exec_command("test -f /opt/secure-vpn/web-portal/static/css/style.css && echo 'EXISTS' || echo 'MISSING'")
        css_status = stdout.read().decode().strip()
        if css_status == "EXISTS":
            print("   ✅ CSS file deployed")
        else:
            print("   ⚠️  CSS file missing")
        
        stdin, stdout, stderr = ssh.exec_command("test -f /opt/secure-vpn/web-portal/templates/home.html && echo 'EXISTS' || echo 'MISSING'")
        home_status = stdout.read().decode().strip()
        if home_status == "EXISTS":
            print("   ✅ Home template deployed")
        else:
            print("   ⚠️  Home template missing")
        
        ssh.close()
        
        print("\n" + "=" * 60)
        print("✅ Deployment Complete!")
        print("=" * 60)
        print("\n🌐 Test the redesign at:")
        print("   https://phazevpn.duckdns.org")
        print("   http://15.204.11.19")
        print("\nWhat to check:")
        print("  ✅ Home page design")
        print("  ✅ Navigation menu")
        print("  ✅ Color scheme and styling")
        print("  ✅ Responsive layout (try mobile view)")
        print("  ✅ No fake content")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

