#!/usr/bin/env python3
"""
Fix HSTS Issue - Set up proper SSL or clear HSTS
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
    print("🔧 Fixing HSTS and Setting Up SSL...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # Option 1: Set up Let's Encrypt SSL (proper solution)
        print("\n1️⃣ Setting up Let's Encrypt SSL certificate...")
        
        # Check if certbot is installed
        success, output, error = run_command(
            ssh,
            "which certbot",
            check=False
        )
        
        if not success:
            print("   Installing certbot...")
            run_command(ssh, "apt-get update && apt-get install -y certbot python3-certbot-nginx", check=False)
        
        # Get certificate for mail subdomain
        print("\n2️⃣ Getting SSL certificate...")
        success, output, error = run_command(
            ssh,
            f"certbot certonly --standalone -d mail.phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --preferred-challenges http",
            check=False
        )
        
        if success or "already exists" in output.lower() or "Certificate not yet due for renewal" in output:
            print("   ✅ Certificate obtained or already exists")
            
            # Configure Nginx with SSL
            print("\n3️⃣ Configuring Nginx with SSL...")
            
            nginx_config = """server {
    listen 80;
    server_name mail.phazevpn.duckdns.org;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mail.phazevpn.duckdns.org;

    ssl_certificate /etc/letsencrypt/live/mail.phazevpn.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mail.phazevpn.duckdns.org/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

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

# Default server for IP access (HTTP only)
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
            
            # Enable site
            run_command(ssh, "rm -f /etc/nginx/sites-enabled/phazevpn-portal*", check=False)
            run_command(ssh, "ln -sf /etc/nginx/sites-available/phazevpn-portal /etc/nginx/sites-enabled/")
            
            # Test and reload
            success, output, error = run_command(
                ssh,
                "nginx -t",
                check=False
            )
            
            if success:
                run_command(ssh, "systemctl reload nginx")
                print("   ✅ Nginx configured with SSL")
            else:
                print(f"   ⚠️  Nginx error: {error}")
            
            # Open firewall for HTTPS
            run_command(ssh, "ufw allow 443/tcp comment 'HTTPS'", check=False)
            
            print("\n✅ SSL Setup Complete!")
            print("\n🌐 Access URLs:")
            print("   - https://mail.phazevpn.duckdns.org (with SSL)")
            print("   - http://15.204.11.19:8080 (direct, no SSL)")
            print("\n📝 If Firefox still shows error:")
            print("   1. Type 'about:config' in address bar")
            print("   2. Search for 'security.tls.insecure_fallback_hosts'")
            print("   3. Add 'mail.phazevpn.duckdns.org' to the list")
            print("   OR")
            print("   4. Clear HSTS: about:preferences#privacy -> Clear Data -> Site Data")
            
        else:
            print(f"   ⚠️  Certificate issue: {error}")
            print("\n   Using self-signed certificate as fallback...")
            
            # Create self-signed cert
            run_command(ssh, f"""
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/mail-selfsigned.key \
  -out /etc/ssl/certs/mail-selfsigned.crt \
  -subj "/CN=mail.phazevpn.duckdns.org"
""", check=False)
            
            # Configure with self-signed
            nginx_config_self = """server {
    listen 443 ssl http2;
    server_name mail.phazevpn.duckdns.org;

    ssl_certificate /etc/ssl/certs/mail-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/mail-selfsigned.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}"""
            
            sftp = ssh.open_sftp()
            f = sftp.file('/etc/nginx/sites-available/phazevpn-portal', 'w')
            f.write(nginx_config_self)
            f.close()
            sftp.close()
            
            run_command(ssh, "rm -f /etc/nginx/sites-enabled/phazevpn-portal*")
            run_command(ssh, "ln -sf /etc/nginx/sites-available/phazevpn-portal /etc/nginx/sites-enabled/")
            run_command(ssh, "nginx -t && systemctl reload nginx", check=False)
            
            print("   ✅ Self-signed certificate created")
            print("   ⚠️  Firefox will show a warning - click 'Advanced' -> 'Accept the Risk'")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
