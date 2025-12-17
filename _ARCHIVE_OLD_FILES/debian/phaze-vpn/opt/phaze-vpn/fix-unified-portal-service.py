#!/usr/bin/env python3
"""
Fix Unified Portal Service - Get it running on port 8080
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
    print("🔧 Fixing Unified Portal Service...\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # 1. Check if unified portal files exist
        print("1️⃣ Checking unified portal files...")
        success, output, error = run_command(
            ssh,
            "test -f /opt/phazevpn-portal/app.py && echo 'EXISTS' || echo 'NOT FOUND'",
            check=False
        )
        print(f"   Portal files: {output.strip()}")
        
        if "NOT FOUND" in output:
            print("   ❌ Portal files not found! Need to deploy them first.")
            return
        
        # 2. Stop any existing service with same name (if it's the wrong one)
        print("\n2️⃣ Stopping conflicting services...")
        run_command(ssh, "systemctl stop phazevpn-unified-portal 2>/dev/null || true", check=False)
        
        # 3. Create proper systemd service for unified portal
        print("\n3️⃣ Creating unified portal service...")
        service_content = """[Unit]
Description=PhazeVPN Unified Web Portal (Email, Files, Productivity)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phazevpn-portal
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/usr/bin/gunicorn -w 4 -b 0.0.0.0:8080 --timeout 120 app:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"""
        
        sftp = ssh.open_sftp()
        f = sftp.file('/etc/systemd/system/phazevpn-unified-portal.service', 'w')
        f.write(service_content)
        f.close()
        sftp.close()
        
        # 4. Install dependencies if needed
        print("\n4️⃣ Installing dependencies...")
        run_command(
            ssh,
            "cd /opt/phazevpn-portal && pip3 install -q flask flask-cors requests gunicorn 2>&1 | tail -3",
            check=False
        )
        
        # 5. Reload systemd and enable service
        print("\n5️⃣ Enabling service...")
        run_command(ssh, "systemctl daemon-reload")
        run_command(ssh, "systemctl enable phazevpn-unified-portal")
        
        # 6. Start service
        print("\n6️⃣ Starting service...")
        success, output, error = run_command(
            ssh,
            "systemctl start phazevpn-unified-portal && sleep 3"
        )
        
        # 7. Check status
        print("\n7️⃣ Checking service status...")
        success, output, error = run_command(
            ssh,
            "systemctl status phazevpn-unified-portal --no-pager | head -15",
            check=False
        )
        print(output)
        
        # 8. Check if port 8080 is listening
        print("\n8️⃣ Checking port 8080...")
        success, output, error = run_command(
            ssh,
            "ss -tlnp | grep ':8080'",
            check=False
        )
        print(f"   Port 8080: {output if output else 'NOT LISTENING'}")
        
        # 9. Test direct connection
        print("\n9️⃣ Testing direct connection...")
        success, output, error = run_command(
            ssh,
            "curl -s http://127.0.0.1:8080/ | head -10",
            check=False
        )
        print(f"   Response: {output[:200]}")
        
        # 10. Update Nginx to route mail subdomain
        print("\n🔟 Updating Nginx routing...")
        nginx_config = """# Mail subdomain -> Unified Portal
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
        f = sftp.file('/etc/nginx/sites-available/mail-portal', 'w')
        f.write(nginx_config)
        f.close()
        sftp.close()
        
        run_command(ssh, "rm -f /etc/nginx/sites-enabled/00-mail-portal")
        run_command(ssh, "ln -sf /etc/nginx/sites-available/mail-portal /etc/nginx/sites-enabled/mail-portal")
        
        # Test Nginx config
        success, output, error = run_command(
            ssh,
            "nginx -t",
            check=False
        )
        print(f"   Nginx test: {output}")
        
        if "successful" in output.lower():
            run_command(ssh, "systemctl reload nginx")
            print("   ✅ Nginx reloaded")
        
        # Final test
        print("\n✅ Final test...")
        success, output, error = run_command(
            ssh,
            "curl -s -H 'Host: mail.phazevpn.duckdns.org' http://localhost/ | grep -o '<title>.*</title>'",
            check=False
        )
        print(f"   Mail subdomain: {output}")
        
        print("\n" + "="*50)
        print("✅ UNIFIED PORTAL FIXED!")
        print("="*50)
        print("\n🌐 Access URLs:")
        print("   - http://mail.phazevpn.duckdns.org")
        print("   - http://15.204.11.19:8080")
        print("\n📊 Service: phazevpn-unified-portal")
        print("   Check status: systemctl status phazevpn-unified-portal")
        print("   View logs: journalctl -u phazevpn-unified-portal -f")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

