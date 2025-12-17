#!/usr/bin/env python3
"""
Directly fix the request.endpoint None check issue in base.html
"""

import paramiko
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
    print("🔧 DIRECTLY FIXING request.endpoint NONE CHECK")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Read base.html
        print("1️⃣  Reading base.html...")
        success, base_html, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/templates/base.html", check=False)
        
        if not success:
            print("   ❌ Failed to read base.html")
            return
        
        print("   ✅ Read base.html")
        print("")
        
        # Fix the specific problematic patterns
        print("2️⃣  Fixing request.endpoint checks...")
        
        fixed_html = base_html
        
        # Fix: {% if 'admin' in request.endpoint %} -> {% if request.endpoint and 'admin' in request.endpoint %}
        if "'admin' in request.endpoint" in fixed_html and "request.endpoint and 'admin' in request.endpoint" not in fixed_html:
            fixed_html = fixed_html.replace(
                "{% if 'admin' in request.endpoint %}",
                "{% if request.endpoint and 'admin' in request.endpoint %}"
            )
            print("   ✅ Fixed 'admin' in request.endpoint")
        
        if "'moderator' in request.endpoint" in fixed_html and "request.endpoint and 'moderator' in request.endpoint" not in fixed_html:
            fixed_html = fixed_html.replace(
                "{% if 'moderator' in request.endpoint %}",
                "{% if request.endpoint and 'moderator' in request.endpoint %}"
            )
            print("   ✅ Fixed 'moderator' in request.endpoint")
        
        # Also check for request.endpoint == patterns and make them safe
        # Actually, == is fine with None, so we don't need to change those
        
        if fixed_html != base_html:
            # Write back
            print("")
            print("3️⃣  Writing fixed base.html to VPS...")
            stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/templates/base.html << 'BASE_EOF'\n{fixed_html}\nBASE_EOF")
            stdout.channel.recv_exit_status()
            print("   ✅ Written to VPS")
        else:
            print("   ⚠️  No changes detected - checking current content...")
            # Show the problematic lines
            success, check, _ = run_command(ssh, f"grep -n \"'admin' in request.endpoint\" {VPN_DIR}/web-portal/templates/base.html", check=False)
            if check:
                print(f"   Found line: {check}")
        
        print("")
        
        # Restart service
        print("4️⃣  Restarting service...")
        run_command(ssh, "systemctl restart secure-vpn-download", check=False)
        
        import time
        time.sleep(3)
        
        success, status, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -3", check=False)
        if 'active (running)' in status:
            print("   ✅ Service restarted and running")
        else:
            print(f"   ⚠️  Service status: {status[:100]}")
        
        print("")
        print("=" * 70)
        print("✅ FIX COMPLETE")
        print("=" * 70)
        print("")
        print("🌐 Try accessing: https://phazevpn.com/admin")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

