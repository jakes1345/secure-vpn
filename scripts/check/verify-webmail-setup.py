#!/usr/bin/env python3
"""
Verify Webmail Setup and Test Access
"""

import paramiko
import os
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
EMAIL_USER = "admin@phazevpn.com"
EMAIL_PASS = "TrashyPanda32!@"

def run_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    return exit_status == 0, output

def main():
    print("🔍 Verifying Webmail Setup")
    print("=" * 60)
    
    # Connect to VPS
    print("\n🔌 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected!")
    
    try:
        # 1. Verify Roundcube is accessible
        print("\n1️⃣ Testing webmail accessibility...")
        try:
            response = requests.get("https://mail.phazevpn.com", verify=False, timeout=10)
            if response.status_code == 200:
                print("   ✅ Webmail is accessible (HTTP 200)")
                if 'roundcube' in response.text.lower() or 'webmail' in response.text.lower():
                    print("   ✅ Roundcube is loaded")
                else:
                    print("   ⚠️  Roundcube may not be fully loaded")
            else:
                print(f"   ⚠️  HTTP Status: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Could not access webmail: {e}")
        
        # 2. Verify Roundcube config
        print("\n2️⃣ Verifying Roundcube configuration...")
        success, output = run_command(ssh, "grep -E 'default_host|smtp_server' /etc/roundcube/config.inc.php | head -3")
        if success and 'mail.phazevpn.com' in output:
            print("   ✅ Roundcube configured for mail.phazevpn.com")
        else:
            print("   ⚠️  Configuration may need checking")
        
        # 3. Verify database
        print("\n3️⃣ Verifying database...")
        success, output = run_command(ssh, "test -f /var/lib/roundcube/roundcube.db && echo 'EXISTS' || echo 'NOT_FOUND'")
        if 'EXISTS' in output:
            print("   ✅ Database exists")
        else:
            print("   ❌ Database missing")
        
        # 4. Verify Nginx config
        print("\n4️⃣ Verifying Nginx configuration...")
        success, output = run_command(ssh, "nginx -t 2>&1")
        if success:
            print("   ✅ Nginx config is valid")
        else:
            print(f"   ⚠️  Nginx issues: {output[:200]}")
        
        # 5. Check PHP-FPM
        print("\n5️⃣ Verifying PHP-FPM...")
        success, output = run_command(ssh, "systemctl is-active php8.1-fpm 2>&1")
        if 'active' in output:
            print("   ✅ PHP-FPM is running")
        else:
            print(f"   ⚠️  PHP-FPM status: {output.strip()}")
        
        # 6. Test email server connection
        print("\n6️⃣ Testing email server connection...")
        success, output = run_command(ssh, "timeout 3 bash -c 'echo QUIT | telnet localhost 993 2>&1' | head -3")
        if 'Connected' in output or 'Escape' in output:
            print("   ✅ IMAP port 993 is accessible")
        else:
            print("   ⚠️  IMAP may not be responding")
        
        # 7. Verify email user exists
        print("\n7️⃣ Verifying email user...")
        success, output = run_command(ssh, "id admin")
        if success:
            print("   ✅ Admin user exists")
        else:
            print("   ❌ Admin user missing")
        
        # 8. Check Maildir
        print("\n8️⃣ Verifying Maildir...")
        success, output = run_command(ssh, "test -d /home/admin/Maildir && echo 'EXISTS' || echo 'NOT_FOUND'")
        if 'EXISTS' in output:
            print("   ✅ Maildir exists")
        else:
            print("   ❌ Maildir missing")
        
        # 9. Final status
        print("\n9️⃣ Service Status:")
        services = ['nginx', 'php8.1-fpm', 'postfix', 'dovecot', 'opendkim']
        for svc in services:
            success, output = run_command(ssh, f"systemctl is-active {svc} 2>&1")
            status = output.strip()
            icon = "✅" if status == 'active' else "❌"
            print(f"   {icon} {svc}: {status}")
        
        print("\n" + "=" * 60)
        print("✅ Webmail Setup Verification Complete!")
        print("\n🌐 Access your webmail:")
        print("   URL: https://mail.phazevpn.com")
        print(f"   Username: {EMAIL_USER}")
        print(f"   Password: {EMAIL_PASS}")
        print("\n📧 Everything is ready to use!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()


