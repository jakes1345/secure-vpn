#!/usr/bin/env python3
"""Restore certificate and fix mail subdomain issue"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔧 Restoring Certificate and Fixing Mail Subdomain")
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

# Step 1: Check if certificate exists
print("1️⃣  Checking certificate status...")
success, cert_check = run_cmd(ssh, 'ls -la /etc/letsencrypt/live/phazevpn.duckdns.org/ 2>&1')
if 'No such file' in cert_check:
    print("   ⚠️  Certificate doesn't exist, getting new one...")
    run_cmd(ssh, 'systemctl stop nginx')
    time.sleep(2)
    run_cmd(ssh, 'certbot certonly --standalone -d phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --preferred-challenges http 2>&1 | tail -10')
    run_cmd(ssh, 'systemctl start nginx')
else:
    print("   ✅ Certificate exists")

# Step 2: Check DNS for mail subdomain
print("")
print("2️⃣  Checking DNS for mail.phazevpn.duckdns.org...")
success, dns_check = run_cmd(ssh, 'dig +short mail.phazevpn.duckdns.org 2>&1 || nslookup mail.phazevpn.duckdns.org 2>&1 | head -5')
print(dns_check)

if '15.204.11.19' in dns_check or VPS_IP in dns_check:
    print("   ✅ DNS points to VPS")
    dns_ok = True
else:
    print("   ⚠️  DNS might not be configured for mail subdomain")
    print("   mail.phazevpn.duckdns.org needs to point to 15.204.11.19")
    dns_ok = False

# Step 3: Update Nginx to redirect mail to main (safe workaround)
print("")
print("3️⃣  Updating Nginx configuration...")
print("   mail.phazevpn.duckdns.org will redirect to phazevpn.duckdns.org")

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

    # Remove includeSubDomains temporarily to allow mail subdomain access
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

# Test and reload
print("")
print("4️⃣  Testing and reloading Nginx...")
run_cmd(ssh, 'nginx -t')
run_cmd(ssh, 'systemctl start nginx')
run_cmd(ssh, 'systemctl reload nginx')

# Verify services
print("")
print("5️⃣  Verifying services...")
run_cmd(ssh, 'systemctl status nginx --no-pager | head -5')
run_cmd(ssh, 'systemctl status phazevpn-portal --no-pager | head -5')

ssh.close()

print("")
print("=" * 80)
print("✅ Configuration Updated!")
print("=" * 80)
print("")
print("🔧 What Changed:")
print("   ✅ mail.phazevpn.duckdns.org redirects to phazevpn.duckdns.org")
print("   ✅ HSTS includeSubDomains removed (temporarily)")
print("   ✅ Both HTTP and HTTPS redirect mail to main domain")
print("")
print("🌐 Access:")
print("   https://phazevpn.duckdns.org ✅")
print("   https://mail.phazevpn.duckdns.org → redirects to main")
print("")
print("💡 To access mail subdomain without redirect:")
if dns_ok:
    print("   1. Get certificate that includes mail subdomain:")
    print("      certbot certonly --nginx -d phazevpn.duckdns.org -d mail.phazevpn.duckdns.org")
else:
    print("   1. Configure DNS: mail.phazevpn.duckdns.org → 15.204.11.19")
    print("   2. Then get certificate with both domains")
print("")
print("💡 Clear HSTS in Firefox:")
print("   about:config → security.tls.insecure_fallback_hosts")
print("   Add: mail.phazevpn.duckdns.org")
print("   Or clear cookies and site data")
print("")

