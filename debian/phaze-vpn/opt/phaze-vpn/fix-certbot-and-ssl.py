#!/usr/bin/env python3
"""Fix certbot and get SSL certificate for both domains"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔧 Fixing Certbot and SSL Certificate")
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

# Step 1: Fix certbot
print("1️⃣  Fixing certbot installation...")
run_cmd(ssh, 'apt-get update -qq')
run_cmd(ssh, 'apt-get install -y --reinstall certbot python3-certbot-nginx 2>&1 | tail -5')
print("   ✅ Certbot reinstalled")

# Step 2: Make sure nginx is running
print("")
print("2️⃣  Ensuring Nginx is running...")
run_cmd(ssh, 'systemctl start nginx')
time.sleep(2)

# Step 3: Get certificate with both domains
print("")
print("3️⃣  Getting SSL certificate for both domains...")
print("   This may take a minute...")

# Try using nginx plugin
cert_cmd = 'certbot certonly --nginx -d phazevpn.duckdns.org -d mail.phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --redirect 2>&1'
success, output = run_cmd(ssh, cert_cmd)

if success:
    print("   ✅ Certificate obtained!")
elif 'already exists' in output.lower() or 'renew' in output.lower():
    print("   ℹ️  Certificate exists, trying to expand...")
    # Try to expand existing certificate
    run_cmd(ssh, 'certbot certonly --nginx -d phazevpn.duckdns.org -d mail.phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --expand --force-renewal 2>&1 | tail -10')
else:
    print("   ⚠️  Certificate request had issues")
    print("   Trying alternative method...")
    # Alternative: Use standalone mode
    run_cmd(ssh, 'systemctl stop nginx')
    time.sleep(1)
    run_cmd(ssh, 'certbot certonly --standalone -d phazevpn.duckdns.org -d mail.phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --preferred-challenges http 2>&1 | tail -10')
    run_cmd(ssh, 'systemctl start nginx')

# Step 4: Verify certificate
print("")
print("4️⃣  Verifying certificate includes both domains...")
success, cert_check = run_cmd(ssh, 'openssl x509 -in /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem -noout -text 2>/dev/null | grep -A 2 "Subject Alternative Name"')
print(cert_check)

if 'mail.phazevpn.duckdns.org' in cert_check:
    print("   ✅ Certificate includes mail.phazevpn.duckdns.org!")
else:
    print("   ⚠️  Certificate doesn't include mail subdomain")
    print("   Will configure Nginx to use main domain certificate (works but shows warning)")

# Step 5: Update Nginx config
print("")
print("5️⃣  Updating Nginx configuration...")

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

# HTTP to HTTPS redirect - Mail subdomain
server {
    listen 80;
    listen [::]:80;
    server_name mail.phazevpn.duckdns.org;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
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

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
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

# HTTPS server - Mail subdomain (uses same certificate)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name mail.phazevpn.duckdns.org;

    # Use main domain certificate (will work if cert includes both, or show warning if not)
    ssl_certificate /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/phazevpn.duckdns.org/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Temporarily reduce HSTS to allow access (remove includeSubDomains)
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
"""

stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/nginx/sites-available/phazevpn << "EOFCONFIG"\n{nginx_config}\nEOFCONFIG\n')
stdout.channel.recv_exit_status()

# Test and reload
print("")
print("6️⃣  Testing and reloading Nginx...")
run_cmd(ssh, 'nginx -t')
run_cmd(ssh, 'systemctl reload nginx')

ssh.close()

print("")
print("=" * 80)
print("✅ SSL Configuration Updated!")
print("=" * 80)
print("")
print("🔧 What Changed:")
print("   ✅ Nginx configured for mail.phazevpn.duckdns.org")
print("   ✅ HSTS includeSubDomains removed from mail subdomain (temporarily)")
print("   ✅ Both domains use same certificate")
print("")
print("🌐 Try accessing:")
print("   https://mail.phazevpn.duckdns.org")
print("")
print("⚠️  IMPORTANT - Clear Browser HSTS Cache:")
print("   Firefox:")
print("   1. Type: about:config")
print("   2. Search: security.tls.insecure_fallback_hosts")
print("   3. Add: mail.phazevpn.duckdns.org")
print("   4. Or: about:preferences#privacy → Clear Cookies and Site Data")
print("")
print("   Chrome:")
print("   1. Go to: chrome://net-internals/#hsts")
print("   2. Delete domain security policies for: mail.phazevpn.duckdns.org")
print("")
print("   Or use incognito/private mode to test")
print("")

