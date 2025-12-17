#!/usr/bin/env python3
"""
Check Email Server Setup Status on VPS
"""

import paramiko
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = os.environ.get("VPS_PASSWORD", "Jakes1328!@")

def run_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    return exit_status == 0, output

def main():
    print("🔍 Checking Email Server Setup Status")
    print("=" * 50)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        
        # Check if setup script is running
        print("\n1️⃣ Checking if setup script is running...")
        success, output = run_command(ssh, "ps aux | grep setup-complete-email-server.sh | grep -v grep")
        if output.strip():
            print("   ⏳ Setup script is RUNNING")
            print(f"   {output.strip()}")
        else:
            print("   ✅ Setup script is NOT running (either finished or not started)")
        
        # Check installed packages
        print("\n2️⃣ Checking installed email packages...")
        packages = ['postfix', 'dovecot-core', 'opendkim', 'spamassassin']
        for pkg in packages:
            success, output = run_command(ssh, f"dpkg -l | grep {pkg} | head -1")
            if output.strip():
                print(f"   ✅ {pkg} installed")
            else:
                print(f"   ❌ {pkg} NOT installed")
        
        # Check services
        print("\n3️⃣ Checking email services status...")
        services = ['postfix', 'dovecot', 'opendkim']
        for svc in services:
            success, output = run_command(ssh, f"systemctl is-active {svc} 2>&1")
            status = output.strip()
            if status == 'active':
                print(f"   ✅ {svc} is running")
            elif status == 'inactive':
                print(f"   ⏸️  {svc} is stopped")
            else:
                print(f"   ❓ {svc} status: {status}")
        
        # Check if Postfix is configured
        print("\n4️⃣ Checking Postfix configuration...")
        success, output = run_command(ssh, "grep 'myhostname = mail.phazevpn.com' /etc/postfix/main.cf 2>&1")
        if 'mail.phazevpn.com' in output:
            print("   ✅ Postfix configured for mail.phazevpn.com")
        else:
            print("   ❌ Postfix not configured yet")
        
        # Check DKIM keys
        print("\n5️⃣ Checking DKIM keys...")
        success, output = run_command(ssh, "test -f /etc/opendkim/mail.private && echo 'EXISTS' || echo 'NOT_FOUND'")
        if 'EXISTS' in output:
            print("   ✅ DKIM keys generated")
        else:
            print("   ❌ DKIM keys not generated yet")
        
        # Check firewall ports
        print("\n6️⃣ Checking firewall ports...")
        ports = ['25', '587', '465', '143', '993']
        success, output = run_command(ssh, "ufw status | grep -E '25|587|465|143|993'")
        if output.strip():
            print("   ✅ Email ports are open:")
            for line in output.strip().split('\n'):
                if line.strip():
                    print(f"      {line.strip()}")
        else:
            print("   ⚠️  Email ports may not be open yet")
        
        print("\n" + "=" * 50)
        print("✅ Status check complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

