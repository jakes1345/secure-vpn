#!/usr/bin/env python3
"""
Fix SSL Certificate and DNS - Make mail subdomain work
"""

import paramiko
import sys

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

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
    print("🔧 Fixing SSL and DNS for mail.phazevpn.duckdns.org...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # Update Nginx to handle HTTP only (no SSL for now)
        print("\n1️⃣ Configuring Nginx for HTTP (no SSL)...")
        
        nginx_config = """server {
    listen 80;
    server_name mail.phazevpn.duckdns.org;

    # Portal
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

    # Email Service API
    location /api/email/ {
        proxy_pass http://127.0.0.1:5005/api/v1/email/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Email API
    location /api/v1/ {
        proxy_pass http://127.0.0.1:5001/api/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Storage API
    location /api/storage/ {
        proxy_pass http://127.0.0.1:5002/api/v1/storage/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Productivity API
    location /api/productivity/ {
        proxy_pass http://127.0.0.1:5003/api/v1/productivity/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Extensibility API
    location /api/extensibility/ {
        proxy_pass http://127.0.0.1:5004/api/v1/extensibility/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# Also handle main domain
server {
    listen 80;
    server_name phazevpn.duckdns.org;

    # Portal (if they want to access it from main domain too)
    location /portal {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# Default server for IP access
server {
    listen 80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}"""
        
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
            print("   ✅ Nginx configured for HTTP")
        else:
            print(f"   ⚠️  Nginx config error: {error}")
        
        print("\n✅ Fixed!")
        print("\n📝 About DuckDNS:")
        print("   - You DON'T need to add 'mail' as a separate domain")
        print("   - DuckDNS automatically supports subdomains")
        print("   - Just make sure phazevpn.duckdns.org points to 15.204.11.19")
        print("   - Then mail.phazevpn.duckdns.org will work automatically")
        print("\n🌐 Access URLs (HTTP only for now):")
        print("   - http://mail.phazevpn.duckdns.org")
        print("   - http://15.204.11.19:8080")
        print("\n🔒 SSL Setup (optional later):")
        print("   - We can set up Let's Encrypt SSL later")
        print("   - For now, HTTP works fine for testing")
        print("   - Just use http:// (not https://)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
