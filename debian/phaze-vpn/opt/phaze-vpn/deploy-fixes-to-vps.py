#!/usr/bin/env python3
"""
Deploy VPN fixes and content updates to VPS
"""

from paramiko import SSHClient, AutoAddPolicy
from pathlib import Path
import sys

# VPS Connection
VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = input("Enter VPS root password: ").strip()

def main():
    print("=" * 60)
    print("Deploying Fixes to VPS")
    print("=" * 60)
    
    try:
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        
        sftp = ssh.open_sftp()
        
        # Upload fixed app.py
        print("\n[1/3] Uploading fixed app.py...")
        local_app = Path("web-portal/app.py")
        remote_app = "/opt/secure-vpn/web-portal/app.py"
        
        if local_app.exists():
            sftp.put(str(local_app), remote_app)
            print("   ✅ app.py uploaded")
        else:
            print("   ❌ app.py not found locally")
            sys.exit(1)
        
        # Upload fixed templates
        print("\n[2/3] Uploading fixed templates...")
        templates = ["testimonials.html", "home.html"]
        for template in templates:
            local_template = Path(f"web-portal/templates/{template}")
            remote_template = f"/opt/secure-vpn/web-portal/templates/{template}"
            
            if local_template.exists():
                sftp.put(str(local_template), remote_template)
                print(f"   ✅ {template} uploaded")
            else:
                print(f"   ⚠️  {template} not found locally")
        
        sftp.close()
        
        # Check VPN service name
        print("\n[3/3] Checking VPN services...")
        stdin, stdout, stderr = ssh.exec_command("systemctl list-units --type=service --all | grep -iE '(vpn|openvpn)' | head -5")
        services = stdout.read().decode().strip()
        if services:
            print(f"   Available VPN services:\n{services}")
        else:
            print("   ⚠️  No VPN services found")
        
        # Check which service is actually running
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active secure-vpn 2>&1")
        secure_vpn_status = stdout.read().decode().strip()
        print(f"   secure-vpn status: {secure_vpn_status}")
        
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active openvpn 2>&1")
        openvpn_status = stdout.read().decode().strip()
        print(f"   openvpn status: {openvpn_status}")
        
        # Restart web service
        print("\n🔄 Restarting web service...")
        stdin, stdout, stderr = ssh.exec_command("systemctl restart phazevpn-web 2>&1")
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print("   ✅ Web service restarted")
        else:
            error = stderr.read().decode().strip()
            print(f"   ⚠️  Restart had issues: {error}")
        
        # Verify service is running
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1")
        status = stdout.read().decode().strip()
        if status == "active":
            print("   ✅ Web service is active")
        else:
            print(f"   ⚠️  Web service status: {status}")
        
        ssh.close()
        
        print("\n" + "=" * 60)
        print("✅ Deployment Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("   1. Test VPN start/stop from dashboard")
        print("   2. Visit: https://phazevpn.duckdns.org/testimonials")
        print("   3. Visit: https://phazevpn.duckdns.org")
        print("   4. Verify no fake content appears")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

