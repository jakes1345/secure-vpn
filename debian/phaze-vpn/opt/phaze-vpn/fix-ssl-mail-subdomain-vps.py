#!/usr/bin/env python3
"""Fix SSL for mail.phazevpn.duckdns.org - Get certificate with both domains"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔒 Fixing SSL Certificate - mail.phazevpn.duckdns.org")
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
    if exit_code != 0:
        print(f"   ⚠️  {err[:150]}")
    return exit_code == 0, out

# Check current certificate
print("1️⃣  Checking current certificate...")
success, cert_info = run_cmd(ssh, 'openssl x509 -in /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem -noout -text 2>/dev/null | grep -A 5 "Subject Alternative Name" || echo "NO_CERT"')
print(cert_info)

# Step 1: Make sure nginx is running for certbot
print("")
print("2️⃣  Ensuring Nginx is running...")
run_cmd(ssh, 'systemctl start nginx')
time.sleep(2)

# Step 2: Get new certificate with both domains using nginx plugin
print("")
print("3️⃣  Getting SSL certificate for both domains...")
print("   Domains: phazevpn.duckdns.org, mail.phazevpn.duckdns.org")

# First, try to expand existing certificate
cert_cmd = 'certbot certonly --nginx -d phazevpn.duckdns.org -d mail.phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --expand 2>&1'
success, output = run_cmd(ssh, cert_cmd)

if not success:
    print("   ⚠️  Expand failed, trying to get new certificate...")
    # Delete old cert and get new one
    run_cmd(ssh, 'certbot delete --cert-name phazevpn.duckdns.org --non-interactive 2>&1 || true')
    time.sleep(1)
    # Get new cert with both domains
    cert_cmd = 'certbot certonly --nginx -d phazevpn.duckdns.org -d mail.phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org 2>&1'
    success, output = run_cmd(ssh, cert_cmd)

if success:
    print("   ✅ Certificate obtained/updated")
else:
    print("   ⚠️  Certificate update had issues")
    print("   Output:", output[:300])

# Step 3: Verify certificate includes both domains
print("")
print("4️⃣  Verifying certificate...")
success, cert_check = run_cmd(ssh, 'openssl x509 -in /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem -noout -text 2>/dev/null | grep -E "DNS:.*phazevpn.duckdns.org"')
print(cert_check)

if 'mail.phazevpn.duckdns.org' in cert_check:
    print("   ✅ Certificate includes mail.phazevpn.duckdns.org")
else:
    print("   ⚠️  Certificate might not include mail subdomain")
    print("   You may need to clear browser HSTS cache")

# Step 4: Update Nginx to handle both domains properly
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

# HTTPS server - Mail subdomain
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name mail.phazevpn.duckdns.org;

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
"""

stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/nginx/sites-available/phazevpn << "EOFCONFIG"\n{nginx_config}\nEOFCONFIG\n')
stdout.channel.recv_exit_status()

# Test and reload
print("")
print("6️⃣  Testing and reloading Nginx...")
run_cmd(ssh, 'nginx -t')
run_cmd(ssh, 'systemctl reload nginx')

# Final check
print("")
print("7️⃣  Final verification...")
success, final_check = run_cmd(ssh, 'curl -k -I https://mail.phazevpn.duckdns.org 2>&1 | head -5')
print(final_check)

ssh.close()

print("")
print("=" * 80)
print("✅ SSL Fix Applied!")
print("=" * 80)
print("")
print("🌐 Try accessing:")
print("   https://mail.phazevpn.duckdns.org")
print("")
print("⚠️  IMPORTANT - Clear Browser HSTS Cache:")
print("   Firefox: about:preferences#privacy → Clear Data → Cookies and Site Data")
print("   Or: about:config → search 'security.tls.insecure_fallback_hosts'")
print("   Add: mail.phazevpn.duckdns.org")
print("")
print("   Chrome: chrome://net-internals/#hsts")
print("   Delete domain security policies for: mail.phazevpn.duckdns.org")
print("")

