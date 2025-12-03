#!/usr/bin/env python3
"""Get fresh SSL certificate that includes both domains"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔒 Getting Fresh SSL Certificate for Both Domains")
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

# Step 1: Delete old certificate
print("1️⃣  Removing old certificate...")
run_cmd(ssh, 'certbot delete --cert-name phazevpn.duckdns.org --non-interactive 2>&1')
time.sleep(2)

# Step 2: Stop nginx
print("")
print("2️⃣  Stopping Nginx...")
run_cmd(ssh, 'systemctl stop nginx')
time.sleep(2)

# Step 3: Get fresh certificate with BOTH domains
print("")
print("3️⃣  Getting fresh certificate for BOTH domains...")
print("   phazevpn.duckdns.org AND mail.phazevpn.duckdns.org")
print("")

cert_cmd = 'certbot certonly --standalone -d phazevpn.duckdns.org -d mail.phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --preferred-challenges http 2>&1'
success, output = run_cmd(ssh, cert_cmd)

if success or 'Congratulations' in output or 'Successfully' in output:
    print("   ✅ Certificate obtained!")
    print(output[-200:])
else:
    print("   ⚠️  Certificate request had issues")
    print(output[-300:])

# Step 4: Start nginx
print("")
print("4️⃣  Starting Nginx...")
run_cmd(ssh, 'systemctl start nginx')

# Step 5: Verify certificate
print("")
print("5️⃣  Verifying certificate includes both domains...")
success, cert_check = run_cmd(ssh, 'openssl x509 -in /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem -noout -text 2>/dev/null | grep -A 3 "Subject Alternative Name"')
print(cert_check)

if 'mail.phazevpn.duckdns.org' in cert_check:
    print("   ✅ SUCCESS! Certificate includes mail.phazevpn.duckdns.org!")
    cert_has_mail = True
else:
    print("   ⚠️  Certificate doesn't include mail subdomain")
    cert_has_mail = False

# Step 6: Update Nginx config
print("")
print("6️⃣  Updating Nginx configuration...")

if cert_has_mail:
    # Perfect! Certificate includes both domains
    nginx_config = """# HTTP to HTTPS redirect - Both domains
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
    # Fallback: redirect mail to main
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

# HTTP redirect - Mail subdomain
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
if cert_has_mail:
    print("✅ SUCCESS! Certificate includes both domains!")
    print("   https://mail.phazevpn.duckdns.org should work now!")
    print("")
    print("   ⚠️  IMPORTANT: Clear browser HSTS cache:")
    print("      Firefox: about:config → security.tls.insecure_fallback_hosts")
    print("      Add: mail.phazevpn.duckdns.org")
    print("      Or clear cookies and site data")
else:
    print("⚠️  Certificate doesn't include mail subdomain")
    print("   mail.phazevpn.duckdns.org redirects to main domain")
print("=" * 80)
print("")
print("🌐 Access:")
print("   https://phazevpn.duckdns.org")
if cert_has_mail:
    print("   https://mail.phazevpn.duckdns.org ✅")
else:
    print("   https://mail.phazevpn.duckdns.org (redirects)")
print("")

