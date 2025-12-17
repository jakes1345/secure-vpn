#!/usr/bin/env python3
"""
Diagnose why website is down on VPS
Check nginx, web portal, services, ports
"""

import paramiko
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description=""):
    """Run command on VPS"""
    if description:
        print(f"🔧 {description}...")
    
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    
    output_lines = []
    for line in iter(stdout.readline, ""):
        if line:
            line = line.rstrip()
            print(f"   {line}")
            output_lines.append(line)
    
    exit_status = stdout.channel.recv_exit_status()
    return exit_status == 0, "\n".join(output_lines)

def main():
    print("=" * 70)
    print("🔍 DIAGNOSING WEBSITE DOWN ISSUE")
    print("=" * 70)
    print("")
    
    # Connect to VPS
    print("🔌 Connecting to VPS...", end=" ", flush=True)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected!")
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)
    
    print("")
    
    try:
        # 1. Check what's using port 8080
        print("1️⃣ Checking what's using port 8080...")
        success, output = run_command(ssh, "lsof -i :8080 || netstat -tulpn | grep :8080 || ss -tulpn | grep :8080", "Checking port 8080")
        if output.strip():
            print("   ⚠️  Port 8080 is in use!")
        else:
            print("   ✅ Port 8080 is free")
        
        # 2. Check nginx status
        print("\n2️⃣ Checking Nginx status...")
        success, output = run_command(ssh, "systemctl status nginx --no-pager | head -10", "Checking Nginx")
        if 'active (running)' in output.lower():
            print("   ✅ Nginx is running")
        else:
            print("   ❌ Nginx is NOT running!")
        
        # 3. Check web portal service
        print("\n3️⃣ Checking web portal service...")
        success, output = run_command(ssh, "systemctl status phazevpn-portal --no-pager 2>&1 | head -10 || echo 'SERVICE_NOT_FOUND'", "Checking web portal")
        if 'SERVICE_NOT_FOUND' in output:
            print("   ⚠️  phazevpn-portal service not found")
        elif 'active (running)' in output.lower():
            print("   ✅ Web portal service is running")
        else:
            print("   ❌ Web portal service is NOT running!")
        
        # 4. Check if web portal process is running
        print("\n4️⃣ Checking web portal process...")
        success, output = run_command(ssh, "ps aux | grep -E 'gunicorn|app.py|web-portal' | grep -v grep | head -5", "Checking processes")
        if output.strip():
            print("   ✅ Web portal process found")
        else:
            print("   ❌ No web portal process running!")
        
        # 5. Check port 5000 (web portal)
        print("\n5️⃣ Checking port 5000 (web portal)...")
        success, output = run_command(ssh, "lsof -i :5000 || netstat -tulpn | grep :5000 || ss -tulpn | grep :5000", "Checking port 5000")
        if output.strip():
            print("   ✅ Port 5000 is in use (web portal)")
        else:
            print("   ❌ Port 5000 is NOT in use (web portal not running)")
        
        # 6. Check nginx config
        print("\n6️⃣ Checking Nginx configuration...")
        success, output = run_command(ssh, "nginx -t 2>&1", "Testing Nginx config")
        if success:
            print("   ✅ Nginx config is valid")
        else:
            print("   ❌ Nginx config has errors!")
        
        # 7. Check if website responds
        print("\n7️⃣ Testing website response...")
        success, output = run_command(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost/ 2>&1 || echo 'FAILED'", "Testing localhost")
        if output.strip() and output.strip() != 'FAILED':
            print(f"   ✅ Website responds with HTTP {output.strip()}")
        else:
            print("   ❌ Website does NOT respond!")
        
        # 8. Check nginx error logs
        print("\n8️⃣ Checking Nginx error logs (last 10 lines)...")
        success, output = run_command(ssh, "tail -10 /var/log/nginx/error.log 2>&1 || echo 'NO_LOG'", "Checking error log")
        if 'NO_LOG' not in output and output.strip():
            print("   Recent errors:")
            for line in output.strip().split('\n')[-5:]:
                if line.strip():
                    print(f"      {line[:80]}")
        
        # 9. Check all listening ports
        print("\n9️⃣ Checking all listening ports...")
        success, output = run_command(ssh, "ss -tulpn | grep LISTEN | head -10", "Checking listening ports")
        if output.strip():
            print("   Listening ports:")
            for line in output.strip().split('\n')[:10]:
                if line.strip():
                    print(f"      {line[:80]}")
        
        # 10. Summary and fixes
        print("\n" + "=" * 70)
        print("📋 DIAGNOSIS SUMMARY")
        print("=" * 70)
        print("")
        print("🔧 Common Fixes:")
        print("")
        print("1. If Nginx is down:")
        print("   systemctl start nginx")
        print("   systemctl enable nginx")
        print("")
        print("2. If web portal is down:")
        print("   systemctl start phazevpn-portal")
        print("   systemctl enable phazevpn-portal")
        print("")
        print("3. If port 8080 is in use (for SearXNG):")
        print("   # Find what's using it:")
        print("   lsof -i :8080")
        print("   # Kill it or use different port")
        print("")
        print("4. If Nginx config has errors:")
        print("   nginx -t")
        print("   # Fix errors in /etc/nginx/sites-available/")
        print("")
        print("5. Restart everything:")
        print("   systemctl restart nginx")
        print("   systemctl restart phazevpn-portal")
        print("")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

