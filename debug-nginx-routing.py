#!/usr/bin/env python3
"""
Debug Nginx Routing - Find out what's actually happening
"""

import paramiko

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status == 0, output, error

def main():
    print("🔍 Debugging Nginx Routing...\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # 1. List all configs with full paths
        print("1️⃣ All Nginx configs...")
        success, output, error = run_command(
            ssh,
            "find /etc/nginx/sites-enabled -type l -exec ls -la {} \\;",
            check=False
        )
        print(output)
        
        # 2. Show full content of each enabled config
        print("\n2️⃣ Content of enabled configs...")
        success, output, error = run_command(
            ssh,
            "for f in /etc/nginx/sites-enabled/*; do echo '=== ' $(basename $f) ' ==='; cat $f; echo; done",
            check=False
        )
        print(output[:2000])
        
        # 3. Test with verbose curl to see redirects
        print("\n3️⃣ Testing with verbose curl...")
        success, output, error = run_command(
            ssh,
            "curl -v -H 'Host: mail.phazevpn.duckdns.org' http://localhost/ 2>&1 | head -30",
            check=False
        )
        print(output)
        
        # 4. Check Nginx access logs
        print("\n4️⃣ Recent Nginx access logs...")
        success, output, error = run_command(
            ssh,
            "tail -5 /var/log/nginx/access.log 2>/dev/null || echo 'No access log'",
            check=False
        )
        print(output)
        
        # 5. Check what Nginx thinks it's serving
        print("\n5️⃣ Nginx config test with details...")
        success, output, error = run_command(
            ssh,
            "nginx -T 2>&1 | grep -A 10 'mail.phazevpn.duckdns.org' | head -20",
            check=False
        )
        print(f"Mail subdomain config:\n{output}")
        
        # 6. Direct test bypassing Nginx
        print("\n6️⃣ Direct test to port 8080...")
        success, output, error = run_command(
            ssh,
            "curl -s http://127.0.0.1:8080/ | grep -o '<title>.*</title>'",
            check=False
        )
        print(f"   Direct 8080: {output}")
        
        # 7. Test through Nginx with IP
        print("\n7️⃣ Test through Nginx with IP...")
        success, output, error = run_command(
            ssh,
            "curl -s http://127.0.0.1/ -H 'Host: mail.phazevpn.duckdns.org' | grep -o '<title>.*</title>'",
            check=False
        )
        print(f"   Through Nginx: {output}")
        
        print("\n" + "="*50)
        print("DEBUG COMPLETE")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

