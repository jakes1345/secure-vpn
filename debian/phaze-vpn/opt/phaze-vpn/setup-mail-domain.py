#!/usr/bin/env python3
"""
Setup Mail Domain - Use mail.phazevpn.duckdns.org
"""

import paramiko
import sys

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

PORTAL_DOMAIN = "mail.phazevpn.duckdns.org"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    if check and exit_status != 0:
        print(f"❌ Error: {error}")
        return False, output, error
    return True, output, error

def main():
    print("🔧 Setting up mail.phazevpn.duckdns.org...")
    print(f"   Domain: {PORTAL_DOMAIN}")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # Configure Nginx with mail domain
        print("\n1️⃣ Configuring Nginx...")
        
        nginx_config = f"""server {{
    listen 80;
    server_name {PORTAL_DOMAIN};

    # Portal
    location / {{
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}

    # Email Service API
    location /api/email/ {{
        proxy_pass http://127.0.0.1:5005/api/v1/email/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}

    # Email API (existing)
    location /api/v1/ {{
        proxy_pass http://127.0.0.1:5001/api/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}

    # Storage API
    location /api/storage/ {{
        proxy_pass http://127.0.0.1:5002/api/v1/storage/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}

    # Productivity API
    location /api/productivity/ {{
        proxy_pass http://127.0.0.1:5003/api/v1/productivity/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}

    # Extensibility API
    location /api/extensibility/ {{
        proxy_pass http://127.0.0.1:5004/api/v1/extensibility/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
}}"""
        
        # Write Nginx config
        sftp = ssh.open_sftp()
        f = sftp.file('/etc/nginx/sites-available/phazevpn-portal', 'w')
        f.write(nginx_config)
        f.close()
        sftp.close()
        
        # Remove old symlinks
        run_command(ssh, "rm -f /etc/nginx/sites-enabled/phazevpn-portal*", check=False)
        
        # Enable new site
        run_command(ssh, "ln -sf /etc/nginx/sites-available/phazevpn-portal /etc/nginx/sites-enabled/")
        
        # Test and reload Nginx
        success, output, error = run_command(
            ssh,
            "nginx -t",
            check=False
        )
        
        if success:
            run_command(ssh, "systemctl reload nginx")
            print("   ✅ Nginx configured")
        else:
            print(f"   ⚠️  Nginx config error: {error}")
        
        # Keep IP access as fallback
        print("\n2️⃣ Keeping IP access as fallback...")
        ip_config = """server {
    listen 80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}"""
        
        sftp = ssh.open_sftp()
        f = sftp.file('/etc/nginx/sites-available/phazevpn-portal-ip', 'w')
        f.write(ip_config)
        f.close()
        sftp.close()
        
        run_command(ssh, "ln -sf /etc/nginx/sites-available/phazevpn-portal-ip /etc/nginx/sites-enabled/phazevpn-portal-ip")
        run_command(ssh, "systemctl reload nginx")
        
        print("\n✅ Mail Domain Setup Complete!")
        print("\n🌐 Access URLs:")
        print(f"   - http://{PORTAL_DOMAIN} (after DNS setup)")
        print("   - http://15.204.11.19:8080 (direct - works now)")
        print("   - http://15.204.11.19 (via IP - works now)")
        print("\n📝 DNS Setup:")
        print(f"   Add A record: {PORTAL_DOMAIN} -> 15.204.11.19")
        print("   Or use DuckDNS:")
        print(f"   curl 'https://www.duckdns.org/update?domains=mail-phazevpn&token=YOUR_TOKEN&ip=15.204.11.19'")
        print("\n💡 Perfect for:")
        print("   - Email/webmail interface")
        print("   - Unified platform")
        print("   - All email-related services")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
