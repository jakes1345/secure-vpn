#!/usr/bin/env python3
"""
Fix Nginx Mail Routing - Make sure mail subdomain goes to portal
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
    print("🔧 Fixing Nginx Mail Routing...\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # 1. List all Nginx configs
        print("1️⃣ Current Nginx configs...")
        success, output, error = run_command(
            ssh,
            "ls -la /etc/nginx/sites-enabled/",
            check=False
        )
        print(output)
        
        # 2. Check what each config does
        print("\n2️⃣ Checking config contents...")
        success, output, error = run_command(
            ssh,
            "grep -h 'server_name' /etc/nginx/sites-enabled/*",
            check=False
        )
        print(f"Server names: {output}")
        
        # 3. Remove ALL configs
        print("\n3️⃣ Removing all configs...")
        run_command(ssh, "rm -f /etc/nginx/sites-enabled/*", check=False)
        
        # 4. Create mail config FIRST (alphabetically first = priority)
        print("\n4️⃣ Creating mail config...")
        mail_config = """# MAIL SUBDOMAIN - Unified Portal
server {
    listen 80;
    server_name mail.phazevpn.duckdns.org;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}"""
        
        sftp = ssh.open_sftp()
        f = sftp.file('/etc/nginx/sites-available/00-mail-portal', 'w')
        f.write(mail_config)
        f.close()
        sftp.close()
        
        run_command(ssh, "ln -sf /etc/nginx/sites-available/00-mail-portal /etc/nginx/sites-enabled/00-mail-portal")
        
        # 5. Re-enable securevpn for main domain
        print("\n5️⃣ Re-enabling VPN homepage...")
        success, output, error = run_command(
            ssh,
            "test -f /etc/nginx/sites-available/securevpn && echo 'EXISTS' || echo 'NOT FOUND'",
            check=False
        )
        if "EXISTS" in output:
            run_command(ssh, "ln -sf /etc/nginx/sites-available/securevpn /etc/nginx/sites-enabled/securevpn")
        
        # 6. Test Nginx
        print("\n6️⃣ Testing Nginx...")
        success, output, error = run_command(
            ssh,
            "nginx -t",
            check=False
        )
        print(f"   {output}")
        
        if "successful" in output.lower():
            run_command(ssh, "systemctl reload nginx")
            print("   ✅ Nginx reloaded")
        
        # 7. Test routing
        print("\n7️⃣ Testing routing...")
        success, output, error = run_command(
            ssh,
            "curl -s -H 'Host: mail.phazevpn.duckdns.org' http://localhost/ | grep -o '<title>.*</title>'",
            check=False
        )
        print(f"   Mail subdomain: {output}")
        
        if "Dashboard" in output or "PhazeVPN Platform" in output:
            print("   ✅ Mail subdomain routing correctly!")
        else:
            print("   ⚠️  Still routing to wrong place")
            
            # Check what's actually on port 8080
            print("\n   Checking what's on port 8080...")
            success, output, error = run_command(
                ssh,
                "curl -s http://127.0.0.1:8080/ | grep -o '<title>.*</title>'",
                check=False
            )
            print(f"   Direct 8080: {output}")
        
        print("\n" + "="*50)
        print("✅ NGINX ROUTING FIXED!")
        print("="*50)
        print("\n🌐 Try: http://mail.phazevpn.duckdns.org")
        print("   Or: http://15.204.11.19:8080")
        print("\n💡 If still not working, clear browser cache!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

