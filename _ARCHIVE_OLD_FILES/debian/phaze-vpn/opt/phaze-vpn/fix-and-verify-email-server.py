#!/usr/bin/env python3
"""
Comprehensive Email Server Check and Fix
Checks everything and fixes issues automatically
"""

import paramiko
import os
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    """Run command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if check and exit_status != 0:
        return False, output, error
    return exit_status == 0, output, error

def main():
    print("🔧 Email Server Comprehensive Check & Fix")
    print("=" * 60)
    
    # Connect to VPS
    print("\n🔌 Connecting to VPS...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected!")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    try:
        # 1. Check services status
        print("\n1️⃣ Checking service status...")
        services = ['postfix', 'dovecot', 'opendkim']
        for svc in services:
            success, output, _ = run_command(ssh, f"systemctl is-active {svc}", check=False)
            status = output.strip()
            if status == 'active':
                print(f"   ✅ {svc}: running")
            else:
                print(f"   ❌ {svc}: {status}")
                print(f"      Starting {svc}...")
                run_command(ssh, f"systemctl start {svc}")
                run_command(ssh, f"systemctl enable {svc}")
        
        # 2. Check Postfix configuration
        print("\n2️⃣ Checking Postfix configuration...")
        success, output, _ = run_command(ssh, "grep 'myhostname = mail.phazevpn.com' /etc/postfix/main.cf", check=False)
        if 'mail.phazevpn.com' in output:
            print("   ✅ Postfix configured for mail.phazevpn.com")
        else:
            print("   ⚠️  Postfix may not be fully configured")
        
        # 3. Check Postfix syntax
        print("\n3️⃣ Checking Postfix configuration syntax...")
        success, output, error = run_command(ssh, "postfix check", check=False)
        if success:
            print("   ✅ Postfix configuration is valid")
        else:
            print(f"   ❌ Postfix configuration errors:")
            print(f"      {error}")
        
        # 4. Check if Postfix is listening
        print("\n4️⃣ Checking if Postfix is listening on ports...")
        success, output, _ = run_command(ssh, "netstat -tlnp | grep ':25 '", check=False)
        if output.strip():
            print("   ✅ Postfix listening on port 25")
            print(f"      {output.strip()[:80]}")
        else:
            print("   ❌ Postfix not listening on port 25")
            print("      Restarting Postfix...")
            run_command(ssh, "systemctl restart postfix")
            time.sleep(2)
        
        # 5. Check SSL certificates
        print("\n5️⃣ Checking SSL certificates...")
        success, output, _ = run_command(ssh, "test -f /etc/letsencrypt/live/phazevpn.com/fullchain.pem && echo 'EXISTS' || echo 'NOT_FOUND'", check=False)
        if 'EXISTS' in output:
            print("   ✅ SSL certificates found")
        else:
            print("   ⚠️  SSL certificates not found")
            print("      Run: certbot --nginx -d phazevpn.com -d www.phazevpn.com -d mail.phazevpn.com")
        
        # 6. Check Dovecot configuration
        print("\n6️⃣ Checking Dovecot...")
        success, output, _ = run_command(ssh, "dovecot --version", check=False)
        if success:
            print(f"   ✅ Dovecot installed: {output.strip()}")
        else:
            print("   ❌ Dovecot not working")
        
        # 7. Check OpenDKIM
        print("\n7️⃣ Checking OpenDKIM...")
        success, output, _ = run_command(ssh, "test -f /etc/opendkim/mail.private && echo 'EXISTS' || echo 'NOT_FOUND'", check=False)
        if 'EXISTS' in output:
            print("   ✅ DKIM keys exist")
        else:
            print("   ❌ DKIM keys missing")
        
        # 8. Check admin user
        print("\n8️⃣ Checking admin user...")
        success, output, _ = run_command(ssh, "id admin", check=False)
        if success:
            print("   ✅ Admin user exists")
        else:
            print("   ❌ Admin user missing - creating...")
            run_command(ssh, "useradd -m -s /bin/bash -g users admin")
            run_command(ssh, "mkdir -p /home/admin/Maildir/{new,cur,tmp}")
            run_command(ssh, "chown -R admin:users /home/admin/Maildir")
            run_command(ssh, "chmod 700 /home/admin/Maildir")
        
        # 9. Check Maildir
        print("\n9️⃣ Checking Maildir...")
        success, output, _ = run_command(ssh, "test -d /home/admin/Maildir && echo 'EXISTS' || echo 'NOT_FOUND'", check=False)
        if 'EXISTS' in output:
            print("   ✅ Maildir exists")
        else:
            print("   ❌ Maildir missing - creating...")
            run_command(ssh, "mkdir -p /home/admin/Maildir/{new,cur,tmp}")
            run_command(ssh, "chown -R admin:users /home/admin/Maildir")
            run_command(ssh, "chmod 700 /home/admin/Maildir")
        
        # 10. Check firewall ports
        print("\n🔟 Checking firewall ports...")
        ports = ['25', '587', '465', '143', '993']
        for port in ports:
            success, output, _ = run_command(ssh, f"ufw status | grep '{port}/tcp'", check=False)
            if output.strip():
                print(f"   ✅ Port {port} is open")
            else:
                print(f"   ⚠️  Port {port} may not be open")
        
        # 11. Test Postfix response
        print("\n1️⃣1️⃣ Testing Postfix response...")
        test_cmd = 'timeout 3 bash -c "echo QUIT | telnet localhost 25 2>&1 | head -5"'
        success, output, _ = run_command(ssh, test_cmd, check=False)
        if '220' in output or 'ESMTP' in output:
            print("   ✅ Postfix is responding")
        else:
            print("   ⚠️  Postfix may not be responding correctly")
            print(f"      Output: {output[:100]}")
        
        # 12. Check recent logs for errors
        print("\n1️⃣2️⃣ Checking recent logs for errors...")
        success, output, _ = run_command(ssh, "tail -20 /var/log/mail.log 2>/dev/null | grep -i error | tail -5", check=False)
        if output.strip():
            print("   ⚠️  Recent errors found:")
            for line in output.strip().split('\n'):
                if line.strip():
                    print(f"      {line[:80]}")
        else:
            print("   ✅ No recent errors in logs")
        
        # 13. Restart services to ensure everything is running
        print("\n1️⃣3️⃣ Restarting services to ensure everything is fresh...")
        for svc in services:
            run_command(ssh, f"systemctl restart {svc}", check=False)
            time.sleep(1)
        print("   ✅ Services restarted")
        
        # 14. Final status check
        print("\n1️⃣4️⃣ Final status check...")
        for svc in services:
            success, output, _ = run_command(ssh, f"systemctl is-active {svc}", check=False)
            status = output.strip()
            if status == 'active':
                print(f"   ✅ {svc}: {status}")
            else:
                print(f"   ❌ {svc}: {status}")
        
        # 15. Get DKIM key
        print("\n1️⃣5️⃣ DKIM Key for Namecheap:")
        print("=" * 60)
        success, output, _ = run_command(ssh, "cat /etc/opendkim/mail.txt", check=False)
        if output.strip():
            print(output.strip())
            print("\n📋 Add this to Namecheap DNS:")
            print("   Host: mail._domainkey")
            print("   Type: TXT")
            print("   Value: (the entire TXT record above, all on one line)")
        else:
            print("   ⚠️  DKIM key file not found")
        
        print("\n" + "=" * 60)
        print("✅ Email Server Check Complete!")
        print("\n📧 Email Server Settings:")
        print("   SMTP: mail.phazevpn.com:587 (STARTTLS) or :465 (SSL)")
        print("   IMAP: mail.phazevpn.com:993 (SSL)")
        print("   Username: admin@phazevpn.com")
        print("   Password: (the one you set)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

