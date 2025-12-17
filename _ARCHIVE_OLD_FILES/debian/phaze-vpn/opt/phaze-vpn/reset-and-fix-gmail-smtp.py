#!/usr/bin/env python3
"""
Delete all clients and accounts, reset to Gmail SMTP, and diagnose email issues
"""

import paramiko
import json
import time
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

def run_command(ssh, command, check=True):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("🧹 RESET: Delete All Clients & Accounts, Fix Gmail SMTP")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # ============================================================
        # STEP 1: DELETE ALL CLIENTS
        # ============================================================
        print("1️⃣  Deleting all VPN clients...")
        print("")
        
        # List all client certificates
        print("   📋 Finding all client certificates...")
        success, output, _ = run_command(ssh, f"ls -1 {VPN_DIR}/certs/*.crt 2>/dev/null | grep -v 'ca.crt\|server.crt' | xargs -r -n1 basename | sed 's/.crt$//' || true", check=False)
        clients = [c.strip() for c in output.split('\n') if c.strip()] if success and output else []
        
        if clients:
            print(f"   Found {len(clients)} clients: {', '.join(clients)}")
            for client in clients:
                print(f"   🗑️  Deleting client: {client}")
                # Delete certificate files
                run_command(ssh, f"rm -f {VPN_DIR}/certs/{client}.crt {VPN_DIR}/certs/{client}.key {VPN_DIR}/certs/{client}.csr 2>/dev/null || true", check=False)
                # Delete config files
                run_command(ssh, f"rm -f {VPN_DIR}/client-configs/{client}.ovpn 2>/dev/null || true", check=False)
            print(f"   ✅ Deleted {len(clients)} clients")
        else:
            print("   ℹ️  No clients found to delete")
        print("")
        
        # ============================================================
        # STEP 2: RESET USER ACCOUNTS (Keep only admin)
        # ============================================================
        print("2️⃣  Resetting user accounts (keeping only admin)...")
        print("")
        
        default_users = {
            "users": {
                "admin": {
                    "password": "admin123",
                    "role": "admin",
                    "created": "2025-11-19"
                }
            },
            "roles": {
                "admin": {
                    "can_start_stop_vpn": True,
                    "can_edit_server_config": True,
                    "can_manage_clients": True,
                    "can_view_logs": True,
                    "can_view_statistics": True,
                    "can_export_configs": True,
                    "can_backup": True,
                    "can_disconnect_clients": True,
                    "can_revoke_clients": True,
                    "can_add_clients": True,
                    "can_edit_clients": True,
                    "can_start_download_server": True,
                    "can_manage_users": True,
                    "can_manage_tickets": True
                },
                "moderator": {
                    "can_start_stop_vpn": False,
                    "can_edit_server_config": False,
                    "can_manage_clients": True,
                    "can_view_logs": True,
                    "can_view_statistics": True,
                    "can_export_configs": True,
                    "can_backup": False,
                    "can_disconnect_clients": True,
                    "can_revoke_clients": False,
                    "can_add_clients": True,
                    "can_edit_clients": True,
                    "can_start_download_server": True,
                    "can_manage_users": False,
                    "can_manage_tickets": True
                },
                "user": {
                    "can_start_stop_vpn": False,
                    "can_edit_server_config": False,
                    "can_manage_clients": False,
                    "can_view_logs": False,
                    "can_view_statistics": True,
                    "can_export_configs": False,
                    "can_backup": False,
                    "can_disconnect_clients": False,
                    "can_revoke_clients": False,
                    "can_add_clients": False,
                    "can_edit_clients": False,
                    "can_start_download_server": False,
                    "can_manage_users": False
                },
                "premium": {
                    "can_start_stop_vpn": False,
                    "can_edit_server_config": False,
                    "can_manage_clients": False,
                    "can_view_logs": True,
                    "can_view_statistics": True,
                    "can_export_configs": True,
                    "can_backup": False,
                    "can_disconnect_clients": False,
                    "can_revoke_clients": False,
                    "can_add_clients": False,
                    "can_edit_clients": False,
                    "can_start_download_server": False,
                    "can_manage_users": False
                }
            }
        }
        
        # Backup existing users.json
        print("   💾 Backing up existing users.json...")
        run_command(ssh, f"cp {VPN_DIR}/users.json {VPN_DIR}/users.json.backup 2>/dev/null || true", check=False)
        
        # Write new users.json
        users_json = json.dumps(default_users, indent=2)
        stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/users.json << 'EOF'\n{users_json}\nEOF")
        stdout.channel.recv_exit_status()
        print("   ✅ User accounts reset (only admin remains)")
        print(f"   📝 Admin login: admin / admin123")
        print("")
        
        # ============================================================
        # STEP 3: CHECK GMAIL SMTP CONFIGURATION
        # ============================================================
        print("3️⃣  Checking Gmail SMTP configuration...")
        print("")
        
        email_smtp_file = f"{VPN_DIR}/web-portal/email_smtp.py"
        
        # Check if email_smtp.py exists
        success, _, _ = run_command(ssh, f"test -f {email_smtp_file}", check=False)
        if not success:
            print(f"   ❌ {email_smtp_file} not found!")
        else:
            print(f"   ✅ {email_smtp_file} exists")
        
        # Check for smtp_config.py
        print("   📋 Checking for smtp_config.py...")
        success, output, _ = run_command(ssh, f"test -f {VPN_DIR}/web-portal/smtp_config.py && echo 'EXISTS' || echo 'NOT_FOUND'", check=False)
        if 'EXISTS' in output:
            print("   ⚠️  smtp_config.py found - checking contents...")
            success, output, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/smtp_config.py", check=False)
            print("   Current config:")
            for line in output.split('\n')[:15]:
                if line.strip() and not line.strip().startswith('#'):
                    print(f"      {line}")
        else:
            print("   ℹ️  smtp_config.py not found (will use environment variables)")
        
        # Check environment variables
        print("   📋 Checking environment variables...")
        success, output, _ = run_command(ssh, "env | grep -E '^SMTP_' || echo 'No SMTP env vars found'", check=False)
        if output and 'No SMTP' not in output:
            print("   Found SMTP environment variables:")
            for line in output.split('\n'):
                if line.strip() and 'PASSWORD' in line:
                    # Hide password
                    parts = line.split('=')
                    if len(parts) == 2:
                        print(f"      {parts[0]}=***")
                elif line.strip():
                    print(f"      {line}")
        else:
            print("   ⚠️  No SMTP environment variables found")
        print("")
        
        # ============================================================
        # STEP 4: CREATE/RESET GMAIL SMTP CONFIG
        # ============================================================
        print("4️⃣  Setting up Gmail SMTP configuration...")
        print("")
        
        print("   📝 Creating smtp_config.py with Gmail defaults...")
        smtp_config = """# Gmail SMTP Configuration
# Set these to your Gmail App Password credentials

SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = ''  # Your Gmail address (e.g., 'your-email@gmail.com')
SMTP_PASSWORD = ''  # Your Gmail App Password (16 characters)
FROM_EMAIL = ''  # Your Gmail address (usually same as SMTP_USER)
FROM_NAME = 'PhazeVPN'

# To get a Gmail App Password:
# 1. Go to: https://myaccount.google.com/apppasswords
# 2. Select "Mail" and generate password
# 3. Copy the 16-character password and paste it above
"""
        
        stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/smtp_config.py << 'SMTPEOF'\n{smtp_config}\nSMTPEOF")
        stdout.channel.recv_exit_status()
        print("   ✅ Created smtp_config.py template")
        print("")
        print("   ⚠️  IMPORTANT: You need to edit smtp_config.py and add:")
        print("      - SMTP_USER: Your Gmail address")
        print("      - SMTP_PASSWORD: Your Gmail App Password")
        print("      - FROM_EMAIL: Your Gmail address")
        print("")
        
        # ============================================================
        # STEP 5: DIAGNOSE EMAIL ISSUES
        # ============================================================
        print("5️⃣  Diagnosing email configuration...")
        print("")
        
        # Check if Python can import email_smtp
        print("   🔍 Testing email_smtp.py import...")
        success, output, error = run_command(ssh, f"cd {VPN_DIR}/web-portal && python3 -c 'import email_smtp; print(\"OK\")' 2>&1", check=False)
        if success and 'OK' in output:
            print("   ✅ email_smtp.py imports successfully")
        else:
            print(f"   ❌ Import failed: {error or output}")
        
        # Check SMTP configuration loading
        print("   🔍 Testing SMTP config loading...")
        success, output, error = run_command(ssh, f"cd {VPN_DIR}/web-portal && python3 -c 'from email_smtp import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD; print(f\"HOST: {{SMTP_HOST}}, PORT: {{SMTP_PORT}}, USER: {{SMTP_USER[:10] if SMTP_USER else \"NOT_SET\"}}...\")' 2>&1", check=False)
        if success:
            print(f"   ✅ Config loaded: {output}")
        else:
            print(f"   ⚠️  Config check: {error or output}")
        
        # Test SMTP connection (without sending)
        print("   🔍 Testing SMTP server connection...")
        test_smtp_code = """
import smtplib
import socket
try:
    host = 'smtp.gmail.com'
    port = 587
    socket.create_connection((host, port), timeout=5)
    print(f'OK: Can connect to {host}:{port}')
except Exception as e:
    print(f'FAIL: {e}')
"""
        success, output, error = run_command(ssh, f"cd {VPN_DIR}/web-portal && python3 << 'PYEOF'\n{test_smtp_code}\nPYEOF", check=False)
        if success:
            print(f"   {output}")
        else:
            print(f"   ⚠️  Connection test: {error or output}")
        
        # Check if credentials are set
        print("   🔍 Checking if credentials are configured...")
        success, output, _ = run_command(ssh, f"cd {VPN_DIR}/web-portal && python3 -c 'from email_smtp import SMTP_USER, SMTP_PASSWORD; print(\"CONFIGURED\" if SMTP_USER and SMTP_PASSWORD else \"NOT_CONFIGURED\")' 2>&1", check=False)
        if 'CONFIGURED' in output:
            print("   ✅ SMTP credentials are configured")
        else:
            print("   ❌ SMTP credentials NOT configured")
            print("      Please edit smtp_config.py and add your Gmail App Password")
        print("")
        
        # ============================================================
        # STEP 6: RESTART WEB PORTAL
        # ============================================================
        print("6️⃣  Restarting web portal to apply changes...")
        print("")
        
        run_command(ssh, "systemctl restart secure-vpn-download", check=False)
        time.sleep(2)
        
        success, output, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -5", check=False)
        print(output)
        print("")
        
        # ============================================================
        # SUMMARY
        # ============================================================
        print("=" * 70)
        print("✅ RESET COMPLETE")
        print("=" * 70)
        print("")
        print("📋 What was done:")
        print("   1. ✅ Deleted all VPN clients")
        print("   2. ✅ Reset user accounts (only admin remains)")
        print("   3. ✅ Created Gmail SMTP configuration template")
        print("   4. ✅ Diagnosed email configuration")
        print("")
        print("📝 Next steps:")
        print("   1. Edit smtp_config.py on the VPS:")
        print(f"      nano {VPN_DIR}/web-portal/smtp_config.py")
        print("")
        print("   2. Add your Gmail credentials:")
        print("      - Get App Password: https://myaccount.google.com/apppasswords")
        print("      - Set SMTP_USER = 'your-email@gmail.com'")
        print("      - Set SMTP_PASSWORD = 'your-16-char-app-password'")
        print("      - Set FROM_EMAIL = 'your-email@gmail.com'")
        print("")
        print("   3. Test email sending:")
        print(f"      cd {VPN_DIR}/web-portal")
        print("      python3 email_smtp.py your-email@gmail.com")
        print("")
        print("🔐 Admin login:")
        print("   Username: admin")
        print("   Password: admin123")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

