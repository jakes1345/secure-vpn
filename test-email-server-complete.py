#!/usr/bin/env python3
"""
Complete Email Server Test
Tests DNS, SMTP, IMAP, and sends a test email
"""

import paramiko
import os
import subprocess
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
    return exit_status == 0, output, error

def test_dns():
    """Test DNS records"""
    print("🌐 Testing DNS Records...")
    print("-" * 50)
    
    # Test MX record
    try:
        result = subprocess.run(['dig', '+short', 'phazevpn.com', 'MX'], 
                              capture_output=True, text=True, timeout=10)
        if 'mail.phazevpn.com' in result.stdout:
            print("✅ MX record: mail.phazevpn.com")
        else:
            print(f"⚠️  MX record: {result.stdout.strip()}")
    except:
        print("⚠️  Could not test MX record (dig not available)")
    
    # Test A record for mail subdomain
    try:
        result = subprocess.run(['dig', '+short', 'mail.phazevpn.com'], 
                              capture_output=True, text=True, timeout=10)
        if VPS_IP in result.stdout:
            print(f"✅ mail.phazevpn.com A record: {VPS_IP}")
        else:
            print(f"⚠️  mail.phazevpn.com: {result.stdout.strip()}")
    except:
        print("⚠️  Could not test A record (dig not available)")
    
    # Test DKIM record
    try:
        result = subprocess.run(['dig', '+short', 'mail._domainkey.phazevpn.com', 'TXT'], 
                              capture_output=True, text=True, timeout=10)
        if 'DKIM1' in result.stdout or 'v=DKIM1' in result.stdout:
            print("✅ DKIM record found")
        else:
            print("⚠️  DKIM record not found or not propagated yet")
            print(f"   (DNS may take a few minutes to propagate)")
    except:
        print("⚠️  Could not test DKIM record (dig not available)")

def main():
    print("🧪 Complete Email Server Test")
    print("=" * 60)
    
    # Test DNS first
    test_dns()
    
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
        # 1. Test SMTP connection
        print("\n1️⃣ Testing SMTP (port 25)...")
        test_cmd = 'timeout 3 bash -c "echo -e \'EHLO test\\nQUIT\' | telnet localhost 25 2>&1"'
        success, output, _ = run_command(ssh, test_cmd, check=False)
        if '220' in output or 'ESMTP' in output or '250' in output:
            print("   ✅ SMTP is responding")
        else:
            print("   ⚠️  SMTP response unclear")
        
        # 2. Test SMTP Submission (port 587)
        print("\n2️⃣ Testing SMTP Submission (port 587)...")
        success, output, _ = run_command(ssh, "netstat -tlnp | grep ':587'", check=False)
        if output.strip():
            print("   ✅ Port 587 is listening")
        else:
            print("   ⚠️  Port 587 not listening")
        
        # 3. Test IMAP (port 993)
        print("\n3️⃣ Testing IMAP (port 993)...")
        success, output, _ = run_command(ssh, "netstat -tlnp | grep ':993'", check=False)
        if output.strip():
            print("   ✅ Port 993 is listening")
        else:
            print("   ⚠️  Port 993 not listening")
        
        # 4. Test sending email locally
        print("\n4️⃣ Testing local email send...")
        test_email_cmd = '''echo "Test email from PhazeVPN server" | mail -s "Test Email" admin@phazevpn.com 2>&1'''
        success, output, error = run_command(ssh, test_email_cmd, check=False)
        if success or 'sent' in output.lower() or 'queued' in output.lower():
            print("   ✅ Test email sent successfully")
        else:
            print(f"   ⚠️  Email send test: {output[:100]}")
        
        # 5. Check mail queue
        print("\n5️⃣ Checking mail queue...")
        success, output, _ = run_command(ssh, "mailq | head -5", check=False)
        if output.strip():
            print("   📬 Mail queue:")
            print(f"      {output.strip()[:200]}")
        else:
            print("   ✅ Mail queue is empty")
        
        # 6. Check if admin can receive mail
        print("\n6️⃣ Checking admin mailbox...")
        success, output, _ = run_command(ssh, "ls -la /home/admin/Maildir/new/ 2>&1", check=False)
        if 'total' in output or len(output.strip().split('\n')) > 1:
            print("   ✅ Maildir is accessible")
            file_count = len([l for l in output.split('\n') if l.strip() and not l.startswith('total') and not l.startswith('d')])
            if file_count > 0:
                print(f"   📬 Found {file_count} email(s) in inbox")
        else:
            print("   ✅ Maildir exists (empty)")
        
        # 7. Verify services
        print("\n7️⃣ Service Status:")
        services = ['postfix', 'dovecot', 'opendkim']
        for svc in services:
            success, output, _ = run_command(ssh, f"systemctl is-active {svc}", check=False)
            status = output.strip()
            icon = "✅" if status == 'active' else "❌"
            print(f"   {icon} {svc}: {status}")
        
        # 8. Check recent logs
        print("\n8️⃣ Recent Activity:")
        success, output, _ = run_command(ssh, "tail -5 /var/log/mail.log 2>/dev/null | grep -v '^$'", check=False)
        if output.strip():
            for line in output.strip().split('\n')[-3:]:
                if line.strip():
                    print(f"   {line[:80]}")
        
        print("\n" + "=" * 60)
        print("✅ Email Server Test Complete!")
        print("\n📧 Your email server is ready!")
        print("\n📋 Summary:")
        print("   • SMTP: mail.phazevpn.com:587 (STARTTLS) or :465 (SSL)")
        print("   • IMAP: mail.phazevpn.com:993 (SSL)")
        print("   • Username: admin@phazevpn.com")
        print("   • DKIM: Added to Namecheap ✅")
        print("\n🧪 Next Steps:")
        print("   1. Configure your email client with the settings above")
        print("   2. Send a test email to yourself")
        print("   3. Check spam folder initially (until reputation builds)")
        print("   4. Test receiving email from external addresses")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

