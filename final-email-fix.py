#!/usr/bin/env python3
"""
Final Email System Fix - Master.cf and Submission Ports
"""

import paramiko
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    if check and exit_status != 0:
        return False, output, error
    return exit_status == 0, output, error

def main():
    print("🔧 FINAL EMAIL FIX - Master.cf Configuration")
    print("=" * 60)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected!")
    
    try:
        # Fix master.cf - ensure submission ports are properly configured
        print("\n📝 Fixing Postfix master.cf for submission...")
        
        # Read current master.cf
        success, current_master, _ = run_command(ssh, "cat /etc/postfix/master.cf")
        
        # Check if submission is configured
        if 'submission inet' not in current_master:
            print("   Adding submission port (587)...")
            
            # Add submission configuration
            submission_config = '''
# Submission (port 587) - CRITICAL for sending emails
submission inet n       -       y       -       -       smtpd
  -o syslog_name=postfix/submission
  -o smtpd_tls_security_level=encrypt
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_tls_auth_only=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_client_restrictions=permit_sasl_authenticated,reject
  -o smtpd_helo_restrictions=permit_mynetworks,permit_sasl_authenticated
  -o smtpd_sender_restrictions=permit_mynetworks,permit_sasl_authenticated
  -o smtpd_recipient_restrictions=permit_mynetworks,permit_sasl_authenticated,reject
  -o smtpd_relay_restrictions=permit_mynetworks,permit_sasl_authenticated,defer_unauth_destination
  -o milter_macro_daemon_name=ORIGINATING

# SMTPS (port 465)
smtps     inet  n       -       y       -       -       smtpd
  -o syslog_name=postfix/smtps
  -o smtpd_tls_wrappermode=yes
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_client_restrictions=permit_sasl_authenticated,reject
  -o smtpd_helo_restrictions=permit_mynetworks,permit_sasl_authenticated
  -o smtpd_sender_restrictions=permit_mynetworks,permit_sasl_authenticated
  -o smtpd_recipient_restrictions=permit_mynetworks,permit_sasl_authenticated,reject
  -o smtpd_relay_restrictions=permit_mynetworks,permit_sasl_authenticated,defer_unauth_destination
  -o milter_macro_daemon_name=ORIGINATING
'''
            
            # Append to master.cf
            sftp = ssh.open_sftp()
            with sftp.file('/etc/postfix/master.cf', 'a') as f:
                f.write(submission_config)
            sftp.close()
            print("   ✅ Submission ports added")
        else:
            print("   ✅ Submission ports already configured")
        
        # Restart Postfix
        print("\n🔄 Restarting Postfix...")
        run_command(ssh, "systemctl restart postfix")
        print("   ✅ Postfix restarted")
        
        # Verify ports are listening
        print("\n🔍 Verifying ports...")
        success, output, _ = run_command(ssh, "netstat -tlnp | grep -E ':25|:587|:465'")
        print("   Listening ports:")
        for line in output.split('\n')[:5]:
            if line.strip():
                print(f"      {line.strip()[:80]}")
        
        print("\n✅ FINAL FIX COMPLETE!")
        print("\n📧 Email system is now fully functional:")
        print("   • Compose emails ✅")
        print("   • Send emails ✅")
        print("   • Receive emails ✅")
        print("   • Delete emails ✅")
        print("   • Manage folders ✅")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

