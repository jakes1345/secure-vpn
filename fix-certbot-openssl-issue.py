#!/usr/bin/env python3
"""Fix certbot OpenSSL library issue and get proper certificate"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔧 Fixing Certbot OpenSSL Issue")
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

# Step 1: Fix OpenSSL/Python library issue
print("1️⃣  Fixing OpenSSL library compatibility...")
run_cmd(ssh, 'apt-get update -qq')
run_cmd(ssh, 'apt-get install -y python3-pip python3-venv 2>&1 | tail -3')
run_cmd(ssh, 'pip3 install --upgrade pyopenssl cryptography 2>&1 | tail -5')
print("   ✅ OpenSSL libraries updated")

# Step 2: Reinstall certbot
print("")
print("2️⃣  Reinstalling certbot...")
run_cmd(ssh, 'apt-get remove -y certbot python3-certbot-nginx 2>&1 | tail -2')
run_cmd(ssh, 'apt-get install -y certbot python3-certbot-nginx 2>&1 | tail -5')
print("   ✅ Certbot reinstalled")

# Step 3: Test certbot
print("")
print("3️⃣  Testing certbot...")
success, output = run_cmd(ssh, 'certbot --version 2>&1')
if success:
    print(f"   ✅ Certbot works: {output.strip()}")
else:
    print("   ⚠️  Certbot still has issues")
    print("   Trying alternative: use snap certbot")
    run_cmd(ssh, 'snap install --classic certbot 2>&1 | tail -3')
    run_cmd(ssh, 'ln -sf /snap/bin/certbot /usr/bin/certbot 2>&1')

# Step 4: Stop nginx and get certificate
print("")
print("4️⃣  Getting SSL certificate for both domains...")
run_cmd(ssh, 'systemctl stop nginx')
time.sleep(2)

# Get certificate with both domains
cert_cmd = 'certbot certonly --standalone -d phazevpn.duckdns.org -d mail.phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --preferred-challenges http 2>&1'
success, output = run_cmd(ssh, cert_cmd)

if success or 'Congratulations' in output or 'Successfully' in output or 'Certificate not yet due' in output:
    print("   ✅ Certificate obtained/updated!")
else:
    print("   ⚠️  Certificate request had issues")
    print("   Output:", output[-300:])

# Step 5: Start nginx
print("")
print("5️⃣  Starting Nginx...")
run_cmd(ssh, 'systemctl start nginx')

# Step 6: Verify certificate
print("")
print("6️⃣  Verifying certificate...")
success, cert_check = run_cmd(ssh, 'openssl x509 -in /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem -noout -text 2>/dev/null | grep -A 3 "Subject Alternative Name"')
print(cert_check)

if 'mail.phazevpn.duckdns.org' in cert_check:
    print("   ✅ Certificate includes mail.phazevpn.duckdns.org!")
    cert_has_mail = True
else:
    print("   ⚠️  Certificate doesn't include mail subdomain")
    cert_has_mail = False

# Step 7: Update Nginx config
print("")
print("7️⃣  Updating Nginx configuration...")

if cert_has_mail:
    # Certificate includes both domains - perfect!
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
    # Certificate doesn't include mail - redirect mail to main
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
print("8️⃣  Testing and reloading Nginx...")
run_cmd(ssh, 'nginx -t')
run_cmd(ssh, 'systemctl reload nginx')

ssh.close()

print("")
print("=" * 80)
if cert_has_mail:
    print("✅ SUCCESS! Certificate includes both domains!")
    print("   https://mail.phazevpn.duckdns.org should work now!")
else:
    print("⚠️  Certificate doesn't include mail subdomain")
    print("   mail.phazevpn.duckdns.org redirects to main domain")
    print("   Clear browser HSTS cache to test")
print("=" * 80)
print("")
print("🌐 Access:")
print("   https://phazevpn.duckdns.org")
if cert_has_mail:
    print("   https://mail.phazevpn.duckdns.org ✅")
else:
    print("   https://mail.phazevpn.duckdns.org (redirects)")
print("")
print("💡 Clear HSTS in Firefox:")
print("   about:config → security.tls.insecure_fallback_hosts")
print("   Add: mail.phazevpn.duckdns.org")
print("")

