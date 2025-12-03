#!/usr/bin/env python3
"""
Fix the TypeError in base.html where request.endpoint can be None
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
    print("🔧 FIXING base.html TypeError - request.endpoint can be None")
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
        
        # Fix all instances where we check 'in request.endpoint' without checking if it's None
        print("2️⃣  Fixing request.endpoint checks...")
        
        # Pattern 1: {% if 'admin' in request.endpoint %}
        # Should be: {% if request.endpoint and 'admin' in request.endpoint %}
        fixed_html = base_html
        
        # Fix all instances
        patterns = [
            (r"{%\s*if\s+['\"](admin|moderator|dashboard|profile|contact|pricing|guide|download|login|signup|tickets|home|index)['\"]\s+in\s+request\.endpoint\s*%}", 
             lambda m: f"{{% if request.endpoint and '{m.group(1)}' in request.endpoint %}}"),
        ]
        
        for pattern, replacement in patterns:
            if callable(replacement):
                fixed_html = re.sub(pattern, replacement, fixed_html)
            else:
                fixed_html = re.sub(pattern, replacement, fixed_html)
        
        # Also fix the specific problematic line
        if "'admin' in request.endpoint" in fixed_html and "request.endpoint and" not in fixed_html.split("'admin' in request.endpoint")[0][-20:]:
            fixed_html = re.sub(
                r"{%\s*if\s+['\"]admin['\"]\s+in\s+request\.endpoint\s*%}",
                "{% if request.endpoint and 'admin' in request.endpoint %}",
                fixed_html
            )
        
        if "'moderator' in request.endpoint" in fixed_html:
            fixed_html = re.sub(
                r"{%\s*if\s+['\"]moderator['\"]\s+in\s+request\.endpoint\s*%}",
                "{% if request.endpoint and 'moderator' in request.endpoint %}",
                fixed_html
            )
        
        if "'dashboard' in request.endpoint" in fixed_html:
            fixed_html = re.sub(
                r"{%\s*if\s+['\"]dashboard['\"]\s+in\s+request\.endpoint\s*%}",
                "{% if request.endpoint and 'dashboard' in request.endpoint %}",
                fixed_html
            )
        
        # Fix any remaining patterns manually
        lines = fixed_html.split('\n')
        fixed_lines = []
        for i, line in enumerate(lines):
            # Check if line has the problematic pattern
            if 'request.endpoint' in line and "'" in line and 'in' in line:
                # Check if it already has the None check
                if 'request.endpoint and' not in line:
                    # Fix it
                    line = re.sub(
                        r"(['\"][^'\"]+['\"])\s+in\s+request\.endpoint",
                        r"request.endpoint and \1 in request.endpoint",
                        line
                    )
            fixed_lines.append(line)
        
        fixed_html = '\n'.join(fixed_lines)
        
        # Count fixes
        original_count = base_html.count("'admin' in request.endpoint") + base_html.count('"admin" in request.endpoint')
        fixed_count = fixed_html.count("request.endpoint and 'admin' in request.endpoint") + fixed_html.count('request.endpoint and "admin" in request.endpoint')
        
        if fixed_count > original_count or fixed_html != base_html:
            print(f"   ✅ Fixed {fixed_count} request.endpoint checks")
            
            # Write back
            print("")
            print("3️⃣  Writing fixed base.html to VPS...")
            stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/templates/base.html << 'BASE_EOF'\n{fixed_html}\nBASE_EOF")
            stdout.channel.recv_exit_status()
            print("   ✅ Written to VPS")
        else:
            print("   ⚠️  No changes needed (already fixed or pattern not found)")
        
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
        print("📋 Fixed:")
        print("   ✅ Added None checks for request.endpoint in base.html")
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

