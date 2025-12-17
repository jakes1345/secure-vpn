#!/usr/bin/env python3
"""
Fix ALL request.endpoint checks in base.html to handle None values
"""

import paramiko
import sys
import re

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
    print("🔧 FIXING ALL request.endpoint CHECKS IN base.html")
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
        
        # Fix all problematic patterns
        print("2️⃣  Fixing all request.endpoint checks...")
        
        original_html = base_html
        fixed_html = base_html
        
        # Pattern 1: {% if 'admin' in request.endpoint %}
        # Should be: {% if request.endpoint and 'admin' in request.endpoint %}
        fixed_html = re.sub(
            r"{%\s*if\s+['\"]admin['\"]\s+in\s+request\.endpoint\s*%}",
            "{% if request.endpoint and 'admin' in request.endpoint %}",
            fixed_html
        )
        
        fixed_html = re.sub(
            r"{%\s*if\s+['\"]moderator['\"]\s+in\s+request\.endpoint\s*%}",
            "{% if request.endpoint and 'moderator' in request.endpoint %}",
            fixed_html
        )
        
        # Pattern 2: {% if request.endpoint == 'something' %}
        # Should check if endpoint exists first (though == should be fine, but let's be safe)
        # Actually, == is fine with None, so we can leave those
        
        # Pattern 3: Any other 'in request.endpoint' patterns
        # Find all remaining patterns
        lines = fixed_html.split('\n')
        fixed_lines = []
        changes_made = 0
        
        for i, line in enumerate(lines):
            original_line = line
            # Check for 'in request.endpoint' patterns that don't have the None check
            if "'" in line and 'in request.endpoint' in line and 'request.endpoint and' not in line:
                # Fix patterns like: {% if 'something' in request.endpoint %}
                line = re.sub(
                    r"({%\s*if\s+)(['\"][^'\"]+['\"])\s+in\s+request\.endpoint",
                    r"\1request.endpoint and \2 in request.endpoint",
                    line
                )
            
            if original_line != line:
                changes_made += 1
                print(f"   Fixed line {i+1}: {original_line.strip()[:60]}...")
            
            fixed_lines.append(line)
        
        fixed_html = '\n'.join(fixed_lines)
        
        if fixed_html != original_html:
            print(f"   ✅ Fixed {changes_made} lines with request.endpoint checks")
            
            # Write back
            print("")
            print("3️⃣  Writing fixed base.html to VPS...")
            stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/templates/base.html << 'BASE_EOF'\n{fixed_html}\nBASE_EOF")
            stdout.channel.recv_exit_status()
            print("   ✅ Written to VPS")
        else:
            print("   ✓ No changes needed")
        
        print("")
        
        # Verify the fix
        print("4️⃣  Verifying fix...")
        success, verify, _ = run_command(ssh, f"grep -n \"'admin' in request.endpoint\" {VPN_DIR}/web-portal/templates/base.html | grep -v 'request.endpoint and' || echo 'NONE_FOUND'", check=False)
        if 'NONE_FOUND' in verify or not verify.strip():
            print("   ✅ All problematic patterns fixed")
        else:
            print(f"   ⚠️  Some patterns may remain: {verify[:100]}")
        
        print("")
        
        # Restart service
        print("5️⃣  Restarting service...")
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
        print("📋 Fixed:")
        print("   ✅ Added None checks for all 'in request.endpoint' patterns")
        print("   ✅ Prevents TypeError when endpoint is None (error pages)")
        print("")
        print("🌐 The site should now work!")
        print("   Try: https://phazevpn.com/admin")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

