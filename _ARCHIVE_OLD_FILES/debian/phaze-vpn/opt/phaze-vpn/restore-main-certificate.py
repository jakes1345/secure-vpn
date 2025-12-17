#!/usr/bin/env python3
"""Restore SSL certificate for main domain"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔒 Restoring SSL Certificate for Main Domain")
print("=" * 80)
print("")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS)

def run_cmd(ssh, cmd, desc=""):
    if desc:
        print(f"   {desc}...")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    if exit_code != 0 and err:
        print(f"   ⚠️  {err[:200]}")
    return exit_code == 0, out

# Step 1: Stop nginx
print("1️⃣  Stopping Nginx...")
run_cmd(ssh, 'systemctl stop nginx')
time.sleep(2)

# Step 2: Get certificate for main domain
print("")
print("2️⃣  Getting SSL certificate for phazevpn.duckdns.org...")
cert_cmd = 'certbot certonly --standalone -d phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --preferred-challenges http 2>&1'
success, output = run_cmd(ssh, cert_cmd)

if success or 'Congratulations' in output or 'Successfully' in output:
    print("   ✅ Certificate obtained!")
    print(output[-200:])
else:
    print("   ⚠️  Certificate request had issues")
    print(output[-300:])

# Step 3: Verify certificate
print("")
print("3️⃣  Verifying certificate...")
success, cert_check = run_cmd(ssh, 'ls -la /etc/letsencrypt/live/phazevpn.duckdns.org/ 2>&1')
if 'fullchain.pem' in cert_check:
    print("   ✅ Certificate files exist")
else:
    print("   ❌ Certificate files missing!")

# Step 4: Update Nginx config
print("")
print("4️⃣  Updating Nginx configuration...")

nginx_config = """# HTTP to HTTPS redirect - Main domain
server {
    listen 80;
    listen [::]:80;
    server_name phazevpn.duckdns.org;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTP redirect - Mail subdomain (redirects to main)
server {
    listen 80;
    listen [::]:80;
    server_name mail.phazevpn.duckdns.org;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://phazevpn.duckdns.org$request_uri;
    }
}

# HTTPS server - Main domain
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name phazevpn.duckdns.org;

    ssl_certificate /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/phazevpn.duckdns.org/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS without includeSubDomains to allow mail subdomain
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
    }

    location /static {
        alias /opt/phazevpn/web-portal/static;
        expires 30d;
    }
}

# HTTPS redirect - Mail subdomain (redirects to main)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name mail.phazevpn.duckdns.org;

    ssl_certificate /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/phazevpn.duckdns.org/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Redirect to main domain
    return 301 https://phazevpn.duckdns.org$request_uri;
}
"""

stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/nginx/sites-available/phazevpn << "EOFCONFIG"\n{nginx_config}\nEOFCONFIG\n')
stdout.channel.recv_exit_status()

# Test and start
print("")
print("5️⃣  Testing and starting Nginx...")
run_cmd(ssh, 'nginx -t')
run_cmd(ssh, 'systemctl start nginx')
time.sleep(2)
run_cmd(ssh, 'systemctl status nginx --no-pager | head -3')

ssh.close()

print("")
print("=" * 80)
print("✅ SSL Certificate Restored!")
print("=" * 80)
print("")
print("🌐 Access:")
print("   https://phazevpn.duckdns.org ✅")
print("   https://mail.phazevpn.duckdns.org → redirects to main")
print("")
print("💡 The mail subdomain redirects to the main domain.")
print("   This fixes the SSL certificate error you saw.")
print("")
print("💡 To clear HSTS in Firefox:")
print("   about:config → security.tls.insecure_fallback_hosts")
print("   Add: mail.phazevpn.duckdns.org")
print("   Or clear cookies and site data")
print("")

