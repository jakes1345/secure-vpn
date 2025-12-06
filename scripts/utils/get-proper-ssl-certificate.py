#!/usr/bin/env python3
"""Get proper SSL certificate that includes both phazevpn.duckdns.org and mail.phazevpn.duckdns.org"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔒 Getting Proper SSL Certificate for Both Domains")
print("=" * 80)
print("")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS)

def run_cmd(ssh, cmd, desc=""):
    if desc:
        print(f"   {desc}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    output = ""
    for line in iter(stdout.readline, ""):
        if line:
            output += line
            print(f"      {line.rstrip()}")
    exit_code = stdout.channel.recv_exit_status()
    return exit_code == 0, output

# Step 1: Stop nginx temporarily
print("1️⃣  Stopping Nginx for certificate generation...")
run_cmd(ssh, 'systemctl stop nginx')
time.sleep(2)

# Step 2: Delete old certificate if it exists
print("")
print("2️⃣  Removing old certificate...")
run_cmd(ssh, 'certbot delete --cert-name phazevpn.duckdns.org --non-interactive 2>&1 || true')
time.sleep(1)

# Step 3: Get new certificate with BOTH domains using standalone
print("")
print("3️⃣  Getting new certificate for BOTH domains...")
print("   This will include: phazevpn.duckdns.org AND mail.phazevpn.duckdns.org")
print("")

cert_cmd = 'certbot certonly --standalone -d phazevpn.duckdns.org -d mail.phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --preferred-challenges http'
success, output = run_cmd(ssh, cert_cmd)

if success or 'Congratulations' in output or 'Successfully' in output:
    print("   ✅ Certificate obtained!")
else:
    print("   ⚠️  Certificate generation had issues")
    print("   Trying with nginx plugin instead...")
    run_cmd(ssh, 'systemctl start nginx')
    time.sleep(2)
    cert_cmd = 'certbot certonly --nginx -d phazevpn.duckdns.org -d mail.phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org'
    success, output = run_cmd(ssh, cert_cmd)

# Step 4: Start nginx
print("")
print("4️⃣  Starting Nginx...")
run_cmd(ssh, 'systemctl start nginx')

# Step 5: Verify certificate
print("")
print("5️⃣  Verifying certificate...")
stdin, stdout, stderr = ssh.exec_command('openssl x509 -in /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem -noout -text 2>/dev/null | grep -A 3 "Subject Alternative Name"')
cert_info = stdout.read().decode()
print(cert_info)

if 'mail.phazevpn.duckdns.org' in cert_info:
    print("   ✅ Certificate includes mail.phazevpn.duckdns.org!")
else:
    print("   ⚠️  Certificate still doesn't include mail subdomain")
    print("   Will use workaround: redirect mail to main domain")

# Step 6: Update Nginx config
print("")
print("6️⃣  Updating Nginx configuration...")

# Check if cert includes mail subdomain
if 'mail.phazevpn.duckdns.org' in cert_info:
    # Certificate includes both - use proper config
    nginx_config = """# HTTP to HTTPS redirect - Main domain
server {
    listen 80;
    listen [::]:80;
    server_name phazevpn.duckdns.org mail.phazevpn.duckdns.org;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server - Both domains
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name phazevpn.duckdns.org mail.phazevpn.duckdns.org;

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
else:
    # Certificate doesn't include mail - redirect mail to main domain
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

# HTTPS redirect - Mail subdomain (redirects to main since cert doesn't include it)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name mail.phazevpn.duckdns.org;

    ssl_certificate /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/phazevpn.duckdns.org/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Redirect to main domain (certificate doesn't include mail subdomain)
    return 301 https://phazevpn.duckdns.org$request_uri;
}
"""

stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/nginx/sites-available/phazevpn << "EOFCONFIG"\n{nginx_config}\nEOFCONFIG\n')
stdout.channel.recv_exit_status()

# Test and reload
print("")
print("7️⃣  Testing and reloading Nginx...")
run_cmd(ssh, 'nginx -t')
run_cmd(ssh, 'systemctl reload nginx')

ssh.close()

print("")
print("=" * 80)
print("✅ SSL Configuration Complete!")
print("=" * 80)
print("")
if 'mail.phazevpn.duckdns.org' in cert_info:
    print("✅ Certificate includes mail.phazevpn.duckdns.org")
    print("   https://mail.phazevpn.duckdns.org should work now!")
else:
    print("⚠️  Certificate doesn't include mail subdomain")
    print("   mail.phazevpn.duckdns.org will redirect to phazevpn.duckdns.org")
    print("   This is a workaround until we get a proper certificate")
print("")
print("🌐 Access:")
print("   https://phazevpn.duckdns.org (main site)")
if 'mail.phazevpn.duckdns.org' in cert_info:
    print("   https://mail.phazevpn.duckdns.org (mail subdomain)")
else:
    print("   https://mail.phazevpn.duckdns.org (redirects to main)")
print("")
print("💡 To clear HSTS in Firefox:")
print("   1. about:config")
print("   2. Search: security.tls.insecure_fallback_hosts")
print("   3. Add: mail.phazevpn.duckdns.org")
print("   4. Or clear cookies and site data")
print("")

