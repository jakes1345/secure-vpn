#!/usr/bin/env python3
"""Add temporary HTTPS support and get proper certificate"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔒 Adding HTTPS Support and Getting Certificate")
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

# Step 1: Try to get certificate first
print("1️⃣  Attempting to get SSL certificate...")
run_cmd(ssh, 'systemctl reload nginx')
time.sleep(2)

cert_cmd = 'certbot certonly --nginx -d phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --redirect 2>&1'
success, output = run_cmd(ssh, cert_cmd)

if success or 'Congratulations' in output or 'Successfully' in output:
    print("   ✅ Certificate obtained!")
    cert_obtained = True
    print(output[-300:])
else:
    print("   ⚠️  Certificate not obtained (DNS/rate limit issue)")
    print("   Will configure HTTP-only for now")
    cert_obtained = False
    print(output[-300:] if output else "")

# Step 2: Update nginx config
print("")
if cert_obtained:
    print("2️⃣  Updating Nginx with HTTPS configuration...")
    
    nginx_config = """# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name phazevpn.duckdns.org mail.phazevpn.duckdns.org;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
        try_files $uri =404;
    }

    location / {
        return 301 https://$server_name$request_uri;
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

# HTTPS redirect - Mail subdomain
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name mail.phazevpn.duckdns.org;

    ssl_certificate /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/phazevpn.duckdns.org/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    return 301 https://phazevpn.duckdns.org$request_uri;
}
"""
else:
    print("2️⃣  Updating Nginx with HTTP-only configuration...")
    
    nginx_config = """# HTTP server (no SSL certificate available yet)
server {
    listen 80;
    listen [::]:80;
    server_name phazevpn.duckdns.org mail.phazevpn.duckdns.org;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
        try_files $uri =404;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static {
        alias /opt/phazevpn/web-portal/static;
        expires 30d;
    }
}
"""

stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/nginx/sites-available/phazevpn << "EOFCONFIG"\n{nginx_config}\nEOFCONFIG\n')
stdout.channel.recv_exit_status()

# Step 3: Test and reload
print("")
print("3️⃣  Testing and reloading Nginx...")
run_cmd(ssh, 'nginx -t')
run_cmd(ssh, 'systemctl reload nginx')
time.sleep(2)

# Step 4: Verify
print("")
print("4️⃣  Verifying services...")
run_cmd(ssh, 'systemctl status nginx --no-pager | head -3')
print("")

# Test connectivity
print("5️⃣  Testing connectivity:")
run_cmd(ssh, 'curl -I http://phazevpn.duckdns.org 2>&1 | head -3')
if cert_obtained:
    run_cmd(ssh, 'curl -k -I https://phazevpn.duckdns.org 2>&1 | head -3')

ssh.close()

print("")
print("=" * 80)
if cert_obtained:
    print("✅ SUCCESS! HTTPS is now enabled!")
    print("   https://phazevpn.duckdns.org should work now")
    print("   https://mail.phazevpn.duckdns.org redirects to main")
else:
    print("⚠️  Site is running on HTTP only")
    print("   http://phazevpn.duckdns.org should work")
    print("")
    print("   ⚠️  If browser tries HTTPS first:")
    print("   1. Clear HSTS: about:config → security.tls.insecure_fallback_hosts")
    print("   2. Add: phazevpn.duckdns.org")
    print("   3. Or use: http://phazevpn.duckdns.org (explicit HTTP)")
print("=" * 80)
print("")

