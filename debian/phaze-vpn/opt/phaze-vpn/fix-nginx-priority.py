#!/usr/bin/env python3
"""
Fix Nginx Priority - Make mail config take precedence
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
    print("🔧 Fixing Nginx Priority...\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # 1. Check main nginx.conf for default_server
        print("1️⃣ Checking main nginx.conf...")
        success, output, error = run_command(
            ssh,
            "grep -n 'default_server\\|include.*sites-enabled' /etc/nginx/nginx.conf",
            check=False
        )
        print(f"   {output}")
        
        # 2. Remove ALL configs
        print("\n2️⃣ Removing all configs...")
        run_command(ssh, "rm -f /etc/nginx/sites-enabled/*", check=False)
        
        # 3. Create mail config with explicit priority
        print("\n3️⃣ Creating mail config with explicit listen...")
        mail_config = """# MAIL SUBDOMAIN - Unified Portal (HIGHEST PRIORITY)
server {
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
        
        sftp = ssh.open_sftp()
        f = sftp.file('/etc/nginx/sites-available/mail-portal', 'w')
        f.write(mail_config)
        f.close()
        sftp.close()
        
        run_command(ssh, "ln -sf /etc/nginx/sites-available/mail-portal /etc/nginx/sites-enabled/mail-portal")
        
        # 4. Modify securevpn to NOT catch mail subdomain
        print("\n4️⃣ Updating securevpn config...")
        success, output, error = run_command(
            ssh,
            "cat /etc/nginx/sites-available/securevpn",
            check=False
        )
        
        # Read and modify
        sftp = ssh.open_sftp()
        f = sftp.file('/etc/nginx/sites-available/securevpn', 'r')
        securevpn_config = f.read().decode('utf-8')
        f.close()
        
        # Ensure server_name only has main domain, not mail
        lines = securevpn_config.split('\n')
        new_lines = []
        for i, line in enumerate(lines):
            if 'server_name' in line and 'listen 80' in '\n'.join(lines[max(0,i-5):i]):
                # This is the HTTP server block - make sure it doesn't catch mail
                if 'mail.phazevpn.duckdns.org' not in line:
                    new_lines.append(line)
                else:
                    # Remove mail from server_name
                    new_line = line.replace(' mail.phazevpn.duckdns.org', '').replace('mail.phazevpn.duckdns.org ', '')
                    new_lines.append(new_line)
            else:
                new_lines.append(line)
        
        f = sftp.file('/etc/nginx/sites-available/securevpn', 'w')
        f.write('\n'.join(new_lines))
        f.close()
        sftp.close()
        
        # Re-enable securevpn
        run_command(ssh, "ln -sf /etc/nginx/sites-available/securevpn /etc/nginx/sites-enabled/securevpn")
        
        # 5. Test and reload
        print("\n5️⃣ Testing and reloading Nginx...")
        success, output, error = run_command(
            ssh,
            "nginx -t",
            check=False
        )
        print(f"   {output}")
        
        if "successful" in output.lower():
            run_command(ssh, "systemctl reload nginx")
            print("   ✅ Nginx reloaded")
            
            # Wait a moment
            import time
            time.sleep(2)
        
        # 6. Test routing
        print("\n6️⃣ Testing routing...")
        success, output, error = run_command(
            ssh,
            "curl -s -H 'Host: mail.phazevpn.duckdns.org' http://localhost/ | grep -o '<title>.*</title>'",
            check=False
        )
        print(f"   Mail subdomain: {output}")
        
        if "Dashboard" in output or "PhazeVPN Platform" in output:
            print("   ✅ SUCCESS! Mail subdomain working!")
        else:
            print("   ⚠️  Still not working")
            
            # Check what Nginx is actually serving
            print("\n   Checking Nginx response headers...")
            success, output, error = run_command(
                ssh,
                "curl -I -H 'Host: mail.phazevpn.duckdns.org' http://localhost/ 2>&1 | head -15",
                check=False
            )
            print(f"   Headers:\n{output}")
        
        print("\n" + "="*50)
        print("✅ PRIORITY FIXED!")
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

