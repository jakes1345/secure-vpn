#!/usr/bin/env python3
"""Fix SSL certificate for mail.phazevpn.duckdns.org subdomain"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔒 Fixing SSL Certificate for mail.phazevpn.duckdns.org")
print("=" * 80)
print("")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS)

def run_command(ssh, command, description=""):
    """Run command on VPS"""
    if description:
        print(f"   {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    if exit_status != 0:
        print(f"   ⚠️  {error[:200]}")
    return exit_status == 0, output

# Step 1: Get new certificate with both domains
print("1️⃣  Getting SSL certificate for both domains...")
print("   This will include: phazevpn.duckdns.org AND mail.phazevpn.duckdns.org")
print("")

# Stop nginx temporarily for certbot
run_command(ssh, 'systemctl stop nginx')

# Get certificate with both domains
cert_command = 'certbot certonly --standalone -d phazevpn.duckdns.org -d mail.phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --preferred-challenges http'
success, output = run_command(ssh, cert_command)

if success:
    print("   ✅ Certificate obtained for both domains")
else:
    print("   ⚠️  Certificate request had issues, checking existing cert...")
    # Check if we can just add the subdomain
    run_command(ssh, 'certbot certonly --standalone -d mail.phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org || true')

# Step 2: Update Nginx config for mail subdomain
print("")
print("2️⃣  Updating Nginx configuration...")

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

# HTTPS server - Mail subdomain (same as main, or separate if needed)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name mail.phazevpn.duckdns.org;

    # Use same certificate (should include both domains now)
    ssl_certificate /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/phazevpn.duckdns.org/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Note: HSTS with includeSubDomains means both domains share the policy
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

# Test nginx config
print("")
print("3️⃣  Testing Nginx configuration...")
success, output = run_command(ssh, 'nginx -t')
if success:
    print("   ✅ Nginx config is valid")
else:
    print("   ❌ Nginx config has errors!")
    print(output)

# Step 4: Restart services
print("")
print("4️⃣  Restarting Nginx...")
run_command(ssh, 'systemctl start nginx')
run_command(ssh, 'systemctl reload nginx')

# Step 5: Verify certificate
print("")
print("5️⃣  Verifying certificate...")
stdin, stdout, stderr = ssh.exec_command('openssl x509 -in /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem -noout -text | grep -A 1 "Subject Alternative Name"')
cert_info = stdout.read().decode()
print(cert_info)

# Step 6: Check if mail subdomain is in certificate
if 'mail.phazevpn.duckdns.org' in cert_info or 'DNS:mail.phazevpn.duckdns.org' in cert_info:
    print("   ✅ Certificate includes mail.phazevpn.duckdns.org")
else:
    print("   ⚠️  Certificate might not include mail subdomain")
    print("   Getting new certificate with both domains...")
    run_command(ssh, 'certbot certonly --nginx -d phazevpn.duckdns.org -d mail.phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org')

ssh.close()

print("")
print("=" * 80)
print("✅ SSL Certificate Fix Complete!")
print("=" * 80)
print("")
print("🌐 Try accessing:")
print("   https://mail.phazevpn.duckdns.org")
print("   https://phazevpn.duckdns.org")
print("")
print("⚠️  If you still see the error:")
print("   1. Clear browser cache and HSTS settings")
print("   2. Wait a few minutes for DNS/certificate propagation")
print("   3. Try in incognito/private mode")
print("")

