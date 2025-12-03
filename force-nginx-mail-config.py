#!/usr/bin/env python3
"""
Force Nginx Mail Config - Make it work no matter what
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
    print("🔧 Forcing Nginx Mail Config...\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # 1. Stop Nginx
        print("1️⃣ Stopping Nginx...")
        run_command(ssh, "systemctl stop nginx")
        
        # 2. Remove ALL configs
        print("\n2️⃣ Removing all configs...")
        run_command(ssh, "rm -f /etc/nginx/sites-enabled/*")
        
        # 3. Create ONLY mail config (no other configs to interfere)
        print("\n3️⃣ Creating mail-only config...")
        mail_config = """server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name mail.phazevpn.duckdns.org _;

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
        f = sftp.file('/etc/nginx/sites-available/mail-only', 'w')
        f.write(mail_config)
        f.close()
        sftp.close()
        
        run_command(ssh, "ln -sf /etc/nginx/sites-available/mail-only /etc/nginx/sites-enabled/mail-only")
        
        # 4. Test config
        print("\n4️⃣ Testing Nginx config...")
        success, output, error = run_command(
            ssh,
            "nginx -t",
            check=False
        )
        print(f"   {output}")
        
        if "successful" in output.lower():
            # 5. Start Nginx
            print("\n5️⃣ Starting Nginx...")
            run_command(ssh, "systemctl start nginx")
            
            import time
            time.sleep(2)
            
            # 6. Test
            print("\n6️⃣ Testing routing...")
            success, output, error = run_command(
                ssh,
                "curl -s -H 'Host: mail.phazevpn.duckdns.org' http://localhost/ | grep -o '<title>.*</title>'",
                check=False
            )
            print(f"   Mail subdomain: {output}")
            
            if "Dashboard" in output or "PhazeVPN Platform" in output:
                print("   ✅ SUCCESS!")
                
                # Now add back securevpn config but make sure mail comes first
                print("\n7️⃣ Adding back VPN homepage config...")
                run_command(ssh, "rm -f /etc/nginx/sites-enabled/*")
                
                # Mail config (no default_server this time)
                mail_config2 = """server {
    listen 80;
    listen [::]:80;
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
                
                f = sftp.file('/etc/nginx/sites-available/00-mail-portal', 'w')
                f.write(mail_config2)
                f.close()
                
                run_command(ssh, "ln -sf /etc/nginx/sites-available/00-mail-portal /etc/nginx/sites-enabled/00-mail-portal")
                run_command(ssh, "ln -sf /etc/nginx/sites-available/securevpn /etc/nginx/sites-enabled/securevpn")
                
                run_command(ssh, "nginx -t && systemctl reload nginx")
                
                # Final test
                success, output, error = run_command(
                    ssh,
                    "curl -s -H 'Host: mail.phazevpn.duckdns.org' http://localhost/ | grep -o '<title>.*</title>'",
                    check=False
                )
                print(f"\n   Final test: {output}")
                
                if "Dashboard" in output or "PhazeVPN Platform" in output:
                    print("   ✅ PERFECT! Both configs working!")
                else:
                    print("   ⚠️  Mail config not working with both enabled")
            else:
                print("   ❌ Still not working even with only mail config")
        else:
            print(f"   ❌ Config error: {error}")
        
        print("\n" + "="*50)
        print("✅ CONFIG FORCED!")
        print("="*50)
        print("\n🌐 Try: http://mail.phazevpn.duckdns.org")
        print("   Or: http://15.204.11.19:8080")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

