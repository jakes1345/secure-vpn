#!/usr/bin/env python3
"""Fix ACME challenge and get certificate"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔧 Fixing ACME Challenge and Getting Certificate")
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

# Step 1: Create proper HTTP config with ACME challenge
print("1️⃣  Creating HTTP config with proper ACME challenge support...")

nginx_config = """server {
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
    }
}
"""

stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/nginx/sites-available/phazevpn << "EOFCONFIG"\n{nginx_config}\nEOFCONFIG\n')
stdout.channel.recv_exit_status()

# Step 2: Ensure directory exists
print("")
print("2️⃣  Setting up ACME challenge directory...")
run_cmd(ssh, 'mkdir -p /var/www/html/.well-known/acme-challenge')
run_cmd(ssh, 'chmod -R 755 /var/www/html')
run_cmd(ssh, 'chown -R www-data:www-data /var/www/html')

# Step 3: Test and reload nginx
print("")
print("3️⃣  Testing and reloading Nginx...")
run_cmd(ssh, 'nginx -t')
run_cmd(ssh, 'systemctl reload nginx')
time.sleep(2)

# Step 4: Test ACME challenge path
print("")
print("4️⃣  Testing ACME challenge path...")
run_cmd(ssh, 'echo "test" > /var/www/html/.well-known/acme-challenge/test.txt')
success, test_output = run_cmd(ssh, 'curl http://phazevpn.duckdns.org/.well-known/acme-challenge/test.txt 2>&1')
if 'test' in test_output:
    print("   ✅ ACME challenge path works!")
else:
    print("   ⚠️  ACME challenge path might have issues")

# Step 5: Get certificate
print("")
print("5️⃣  Getting SSL certificate...")
cert_cmd = 'certbot certonly --nginx -d phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --redirect 2>&1'
success, output = run_cmd(ssh, cert_cmd)

if success or 'Congratulations' in output or 'Successfully' in output:
    print("   ✅ Certificate obtained!")
    print(output[-400:])
    cert_obtained = True
else:
    print("   ⚠️  Certificate request had issues")
    print(output[-400:])
    cert_obtained = False

# Step 6: If certificate obtained, update to HTTPS config
if cert_obtained:
    print("")
    print("6️⃣  Updating to HTTPS configuration...")

    nginx_config = """# HTTP to HTTPS redirect - Main domain
server {
    listen 80;
    listen [::]:80;
    server_name phazevpn.duckdns.org;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
        try_files $uri =404;
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
        try_files $uri =404;
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
if cert_obtained:
    print("✅ SUCCESS! SSL Certificate Obtained!")
    print("   https://phazevpn.duckdns.org should work now")
    print("   https://mail.phazevpn.duckdns.org redirects to main")
else:
    print("⚠️  Certificate not obtained")
    print("   Site is running on HTTP")
    print("   May need to wait for Let's Encrypt rate limit")
print("=" * 80)
print("")
print("💡 To clear HSTS in Firefox:")
print("   about:config → security.tls.insecure_fallback_hosts")
print("   Add: mail.phazevpn.duckdns.org")
print("")

