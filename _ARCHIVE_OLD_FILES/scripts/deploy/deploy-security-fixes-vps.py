#!/usr/bin/env python3
"""
Deploy Security Fixes to VPS using Paramiko
Installs Flask-WTF and applies all security fixes
"""

import paramiko
import os
from pathlib import Path
import time

# VPS Connection Details
VPS_HOST = os.environ.get('VPS_HOST') or os.environ.get('VPS_IP', '15.204.11.19')
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PASSWORD = 'Jakes1328!@'

def connect_vps():
    """Connect to VPS"""
    print(f"🔌 Connecting to {VPS_HOST} as {VPS_USER}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=15)
        print("✅ Connected successfully!\n")
        return ssh
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        raise

def run_command(ssh, command, description, show_output=True):
    """Run command and show output"""
    print(f"  ⚙️  {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if exit_status == 0:
        print(f"  ✅ Success")
        if show_output and output.strip():
            print(f"     {output.strip()[:300]}")
        return True, output
    else:
        print(f"  ❌ Failed: {error[:200]}")
        return False, error

def upload_file(ssh, local_path, remote_path):
    """Upload file to VPS"""
    print(f"  📤 Uploading {local_path.name}...")
    sftp = ssh.open_sftp()
    try:
        sftp.put(str(local_path), remote_path)
        print(f"  ✅ Uploaded to {remote_path}")
        return True
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return False
    finally:
        sftp.close()

def main():
    print("=" * 70)
    print("🔒 Deploying Security Fixes to VPS")
    print("=" * 70)
    print(f"📍 VPS: {VPS_HOST}")
    print(f"👤 User: {VPS_USER}")
    print("=" * 70)
    print()
    
    ssh = connect_vps()
    
    try:
        # Step 1: Install Flask-WTF
        print("📋 Step 1: Installing Flask-WTF...")
        run_command(ssh,
            "cd /opt/phaze-vpn/web-portal && pip3 install Flask-WTF WTForms --quiet",
            "Install Flask-WTF"
        )
        print()
        
        # Step 2: Verify installation
        print("📋 Step 2: Verifying Flask-WTF installation...")
        run_command(ssh,
            "python3 -c 'import flask_wtf; print(flask_wtf.__version__)'",
            "Check Flask-WTF version"
        )
        print()
        
        # Step 3: Upload security fix files
        print("📋 Step 3: Uploading security fix files...")
        base_dir = Path(__file__).parent
        web_portal_dir = "/opt/phaze-vpn/web-portal"
        
        files_to_upload = [
            ('web-portal/rate_limiting.py', f'{web_portal_dir}/rate_limiting.py'),
            ('web-portal/file_locking.py', f'{web_portal_dir}/file_locking.py'),
            ('web-portal/payment_integrations.py', f'{web_portal_dir}/payment_integrations.py'),
            ('web-portal/requirements.txt', f'{web_portal_dir}/requirements.txt'),
        ]
        
        for local_file, remote_file in files_to_upload:
            local_path = base_dir / local_file
            if local_path.exists():
                upload_file(ssh, local_path, remote_file)
            else:
                print(f"  ⚠️  File not found: {local_file}")
        print()
        
        # Step 4: Upload updated app.py (if needed - check first)
        print("📋 Step 4: Checking app.py...")
        run_command(ssh,
            "cd /opt/phaze-vpn/web-portal && grep -q 'CSRFProtect' app.py && echo 'CSRF already in app.py' || echo 'CSRF not found'",
            "Check if CSRF is already in app.py"
        )
        print()
        
        # Step 5: Upload templates with CSRF tokens
        print("📋 Step 5: Uploading updated templates...")
        templates_dir = f"{web_portal_dir}/templates"
        template_files = [
            'base.html',
            'login.html',
            'signup.html',
            'contact.html',
            'forgot-password.html',
            'reset-password.html',
        ]
        
        for template_file in template_files:
            local_path = base_dir / 'web-portal' / 'templates' / template_file
            if local_path.exists():
                upload_file(ssh, local_path, f"{templates_dir}/{template_file}")
            else:
                print(f"  ⚠️  Template not found: {template_file}")
        print()
        
        # Step 6: Create data directory for rate limiting
        print("📋 Step 6: Creating data directory...")
        run_command(ssh,
            "mkdir -p /opt/phaze-vpn/web-portal/data && chmod 755 /opt/phaze-vpn/web-portal/data",
            "Create data directory"
        )
        print()
        
        # Step 7: Set proper permissions
        print("📋 Step 7: Setting file permissions...")
        run_command(ssh,
            f"chmod 644 {web_portal_dir}/*.py {web_portal_dir}/templates/*.html 2>/dev/null; chmod 755 {web_portal_dir}/*.py 2>/dev/null; echo 'Permissions set'",
            "Set file permissions"
        )
        print()
        
        # Step 8: Check if service needs restart
        print("📋 Step 8: Checking service status...")
        run_command(ssh,
            "systemctl is-active phazevpn-portal.service && echo 'Service is running' || echo 'Service not running'",
            "Check portal service"
        )
        print()
        
        # Step 9: Test Python imports
        print("📋 Step 9: Testing Python imports...")
        test_imports = """
python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/opt/phaze-vpn/web-portal')
try:
    from flask_wtf.csrf import CSRFProtect
    print('✅ Flask-WTF imported successfully')
except ImportError as e:
    print(f'❌ Flask-WTF import failed: {e}')

try:
    from rate_limiting import check_rate_limit
    print('✅ rate_limiting imported successfully')
except ImportError as e:
    print(f'❌ rate_limiting import failed: {e}')

try:
    from file_locking import safe_json_read
    print('✅ file_locking imported successfully')
except ImportError as e:
    print(f'❌ file_locking import failed: {e}')
PYTHON_EOF
"""
        run_command(ssh, test_imports, "Test imports")
        print()
        
        # Step 10: Summary
        print("=" * 70)
        print("✅ Security Fixes Deployment Complete!")
        print("=" * 70)
        print()
        print("📝 Next Steps:")
        print("  1. Review the changes")
        print("  2. Set environment variables (FLASK_SECRET_KEY, STRIPE keys)")
        print("  3. Restart the service: systemctl restart phazevpn-portal.service")
        print("  4. Check logs: journalctl -u phazevpn-portal.service -f")
        print()
        print("📄 Files updated:")
        print("  • rate_limiting.py - File-based rate limiting")
        print("  • file_locking.py - Race condition prevention")
        print("  • payment_integrations.py - Secure payment handler")
        print("  • requirements.txt - Dependencies")
        print("  • Templates - CSRF tokens added")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()
        print("✅ Connection closed")

if __name__ == "__main__":
    main()

