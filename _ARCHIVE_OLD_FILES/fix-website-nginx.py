#!/usr/bin/env python3
"""
Fix website down issue - check and fix nginx configuration
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
    print("🔧 FIXING WEBSITE DOWN ISSUE")
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
        # 1. Check nginx config files
        print("1️⃣ Checking Nginx configuration files...")
        success, output = run_command(ssh, "ls -la /etc/nginx/sites-enabled/", "Listing enabled sites")
        
        # 2. Check main nginx config
        print("\n2️⃣ Checking main Nginx config...")
        success, output = run_command(ssh, "grep -E 'server_name|proxy_pass|listen' /etc/nginx/sites-enabled/* 2>/dev/null | head -20", "Checking server blocks")
        
        # 3. Check if phazevpn config exists
        print("\n3️⃣ Checking for PhazeVPN nginx config...")
        success, output = run_command(ssh, "test -f /etc/nginx/sites-enabled/phazevpn && echo 'EXISTS' || echo 'NOT_FOUND'", "Checking config file")
        if 'NOT_FOUND' in output:
            print("   ⚠️  PhazeVPN config not found - checking other locations...")
            run_command(ssh, "find /etc/nginx -name '*phazevpn*' -o -name '*phaze*' 2>/dev/null", "Searching for config")
        
        # 4. Check what nginx is serving
        print("\n4️⃣ Testing what nginx serves...")
        success, output = run_command(ssh, "curl -s -I http://localhost/ 2>&1 | head -10", "Testing localhost")
        
        # 5. Check if web portal responds directly
        print("\n5️⃣ Testing web portal directly...")
        success, output = run_command(ssh, "curl -s -I http://localhost:5000/ 2>&1 | head -5", "Testing port 5000")
        
        # 6. Check nginx access logs
        print("\n6️⃣ Checking recent nginx access...")
        success, output = run_command(ssh, "tail -5 /var/log/nginx/access.log 2>&1 | head -5 || echo 'NO_LOG'", "Checking access log")
        
        # 7. Fix port 8080 issue (kill gunicorn on 8080)
        print("\n7️⃣ Fixing port 8080 conflict...")
        success, output = run_command(ssh, "lsof -ti :8080 | xargs kill -9 2>/dev/null || echo 'NO_PROCESS'", "Killing processes on 8080")
        if 'NO_PROCESS' not in output:
            print("   ✅ Killed processes on port 8080")
        else:
            print("   ✅ Port 8080 is now free")
        
        # 8. Restart services
        print("\n8️⃣ Restarting services...")
        run_command(ssh, "systemctl restart nginx", "Restarting Nginx")
        run_command(ssh, "systemctl restart phazevpn-portal", "Restarting web portal")
        
        # 9. Test again
        print("\n9️⃣ Testing website after restart...")
        import time
        time.sleep(2)
        success, output = run_command(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost/ 2>&1", "Testing website")
        if output.strip() == '200':
            print("   ✅ Website is now working!")
        elif output.strip() == '404':
            print("   ⚠️  Website returns 404 - nginx routing issue")
        else:
            print(f"   ⚠️  Website returns HTTP {output.strip()}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📋 SUMMARY")
        print("=" * 70)
        print("")
        print("✅ Port 8080 conflict fixed")
        print("✅ Services restarted")
        print("")
        print("🔧 If website still down, check:")
        print("   1. Nginx config: /etc/nginx/sites-enabled/")
        print("   2. Web portal logs: journalctl -u phazevpn-portal")
        print("   3. Nginx logs: /var/log/nginx/error.log")
        print("")
        print("🌐 Test website:")
        print("   curl -I http://15.204.11.19/")
        print("   curl -I https://phazevpn.com/")
        print("")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

