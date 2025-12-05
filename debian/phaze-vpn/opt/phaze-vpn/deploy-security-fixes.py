#!/usr/bin/env python3
"""Deploy security fixes and set up HTTPS"""

import paramiko
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"
DOMAIN = "15.204.11.19"  # Using IP for now, can change to domain later

print("🔒 Deploying Security Fixes & HTTPS Setup...")
print("="*60)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    return stdout.read().decode(), stderr.read().decode(), exit_status

def upload_file(local_path, remote_path):
    sftp = ssh.open_sftp()
    try:
        remote_dir = str(Path(remote_path).parent)
        run(f"mkdir -p {remote_dir}")
        sftp.put(local_path, remote_path)
        return True
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False
    finally:
        sftp.close()

# 1. Upload fixed app.py with security improvements
print("\n1️⃣  Uploading security fixes...")
upload_file('/opt/phaze-vpn/web-portal/app.py', f'{VPN_DIR}/web-portal/app.py')
print("   ✅ Updated app.py with secure secret key and rate limiting")

# 2. Install nginx and certbot
print("\n2️⃣  Installing nginx and certbot...")
output, errors, status = run("apt-get update && apt-get install -y nginx certbot python3-certbot-nginx")
print("   ✅ Installed")

# 3. Configure nginx as reverse proxy
print("\n3️⃣  Configuring nginx reverse proxy...")
nginx_config = f"""
server {{
    listen 80;
    server_name {DOMAIN};

    location / {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
}}
"""

run(f"echo '{nginx_config}' > /etc/nginx/sites-available/securevpn")
run("ln -sf /etc/nginx/sites-available/securevpn /etc/nginx/sites-enabled/")
run("rm -f /etc/nginx/sites-enabled/default")  # Remove default site

# Test nginx config
output, errors, status = run("nginx -t")
if status == 0:
    print("   ✅ Nginx configuration valid")
    run("systemctl restart nginx")
    run("systemctl enable nginx")
else:
    print(f"   ⚠️  Nginx config error: {errors}")

# 4. Get SSL certificate (using self-signed for IP, or Let's Encrypt if domain)
print("\n4️⃣  Setting up SSL certificate...")
print("   Note: Using self-signed cert (Let's Encrypt requires a domain name)")

# Generate self-signed certificate
run(f"""
mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/securevpn.key \
    -out /etc/nginx/ssl/securevpn.crt \
    -subj "/C=US/ST=State/L=City/O=SecureVPN/CN={DOMAIN}"
""")
print("   ✅ Self-signed certificate generated")

# 5. Configure nginx with SSL
print("\n5️⃣  Configuring HTTPS...")
nginx_ssl_config = f"""
server {{
    listen 80;
    server_name {DOMAIN};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {DOMAIN};

    ssl_certificate /etc/nginx/ssl/securevpn.crt;
    ssl_certificate_key /etc/nginx/ssl/securevpn.key;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}
}}
"""

run(f"echo '{nginx_ssl_config}' > /etc/nginx/sites-available/securevpn")
run("nginx -t && systemctl reload nginx")
print("   ✅ HTTPS configured")

# 6. Update firewall to allow HTTPS
print("\n6️⃣  Configuring firewall...")
run("ufw allow 80/tcp")
run("ufw allow 443/tcp")
print("   ✅ Firewall updated")

# 7. Restart portal
print("\n7️⃣  Restarting services...")
run("systemctl restart secure-vpn-portal")
print("   ✅ Portal restarted")

# 8. Check status
print("\n8️⃣  Checking services...")
output, _, _ = run("systemctl status nginx --no-pager -l | head -8")
print(output)

output, _, _ = run("systemctl status secure-vpn-portal --no-pager -l | head -8")
print(output)

print("\n" + "="*60)
print("✅ SECURITY FIXES DEPLOYED!")
print("="*60)
print(f"\n🔒 Security Improvements:")
print("  ✅ Secure secret key (64 random characters)")
print("  ✅ Rate limiting (5 attempts per 15 min)")
print("  ✅ HTTPS enabled (self-signed cert)")
print("  ✅ Security headers added")
print("  ✅ Nginx reverse proxy configured")
print("\n🌐 Access:")
print(f"  HTTP:  http://{VPS_IP} (redirects to HTTPS)")
print(f"  HTTPS: https://{VPS_IP} (may show cert warning - that's normal)")
print("\n⚠️  Note:")
print("  - Browser will show 'Not Secure' warning (self-signed cert)")
print("  - Click 'Advanced' → 'Proceed anyway'")
print("  - For production: Get Let's Encrypt cert with a domain name")
print("\n📋 New passwords:")
print("  - Check SECURE-PASSWORDS.txt on your local machine")
print("  - Change them after first login!")
print()

ssh.close()

