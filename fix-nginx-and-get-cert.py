#!/usr/bin/env python3
"""Fix nginx config and get certificate properly"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔧 Fixing Nginx and Getting Certificate")
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

# Step 1: Disable all site configs
print("1️⃣  Disabling all site configs...")
run_cmd(ssh, 'rm -f /etc/nginx/sites-enabled/*')
run_cmd(ssh, 'systemctl stop nginx')

# Step 2: Create clean HTTP-only config
print("")
print("2️⃣  Creating clean HTTP-only config...")

clean_nginx = """server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""

stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/nginx/sites-available/phazevpn << "EOFCONFIG"\n{clean_nginx}\nEOFCONFIG\n')
stdout.channel.recv_exit_status()
run_cmd(ssh, 'ln -sf /etc/nginx/sites-available/phazevpn /etc/nginx/sites-enabled/phazevpn')

# Step 3: Start nginx
print("")
print("3️⃣  Starting Nginx...")
run_cmd(ssh, 'nginx -t')
run_cmd(ssh, 'systemctl start nginx')
time.sleep(3)

# Step 4: Get certificate
print("")
print("4️⃣  Getting SSL certificate...")
cert_cmd = 'certbot certonly --nginx -d phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --redirect 2>&1'
success, output = run_cmd(ssh, cert_cmd)

if success or 'Congratulations' in output or 'Successfully' in output:
    print("   ✅ Certificate obtained!")
    print(output[-400:])
else:
    print("   ⚠️  Certificate request had issues")
    print(output[-400:])

# Step 5: Verify certificate
print("")
print("5️⃣  Verifying certificate...")
success, cert_check = run_cmd(ssh, 'ls -la /etc/letsencrypt/live/phazevpn.duckdns.org/ 2>&1')
if 'fullchain.pem' in cert_check:
    print("   ✅ Certificate exists!")
    cert_exists = True
else:
    print("   ❌ Certificate missing")
    cert_exists = False

# Step 6: Update to final HTTPS config
if cert_exists:
    print("")
    print("6️⃣  Updating to HTTPS configuration...")

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

    stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/nginx/sites-available/phazevpn << "EOFCONFIG"\n{nginx_config}\nEOFCONFIG\n')
    stdout.channel.recv_exit_status()

    # Test and reload
    print("")
    print("7️⃣  Testing and reloading Nginx...")
    run_cmd(ssh, 'nginx -t')
    run_cmd(ssh, 'systemctl reload nginx')
    time.sleep(2)

    # Verify
    print("")
    print("8️⃣  Verifying services...")
    run_cmd(ssh, 'systemctl status nginx --no-pager | head -3')
    run_cmd(ssh, 'curl -k -I https://phazevpn.duckdns.org 2>&1 | head -3')

ssh.close()

print("")
print("=" * 80)
if cert_exists:
    print("✅ SSL Certificate Restored!")
    print("   https://phazevpn.duckdns.org should work now")
    print("   https://mail.phazevpn.duckdns.org redirects to main")
else:
    print("⚠️  Certificate not obtained - DNS/network issue")
    print("   Site is running on HTTP only")
print("=" * 80)
print("")
print("💡 To clear HSTS in Firefox:")
print("   about:config → security.tls.insecure_fallback_hosts")
print("   Add: mail.phazevpn.duckdns.org")
print("")

