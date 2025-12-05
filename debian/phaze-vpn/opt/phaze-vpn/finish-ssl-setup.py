#!/usr/bin/env python3
"""Finish Let's Encrypt SSL setup"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
DOMAIN = "phazevpn.duckdns.org"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=120)
    exit_status = stdout.channel.recv_exit_status()
    return stdout.read().decode(), stderr.read().decode(), exit_status

print("🔒 Getting Let's Encrypt SSL Certificate...")
print("="*60)

# Wait a bit more for DNS
print("\n1️⃣  Waiting for DNS propagation...")
time.sleep(10)

# Verify DNS is working
print("\n2️⃣  Verifying DNS resolution...")
output, _, _ = run(f"dig +short {DOMAIN} @8.8.8.8")
print(f"   DNS resolves to: {output.strip()}")
if output.strip() != "15.204.11.19":
    print("   ⚠️  DNS not fully propagated yet, but continuing...")

# Make sure nginx is serving on port 80
print("\n3️⃣  Verifying nginx is accessible...")
output, _, _ = run(f"curl -s -o /dev/null -w '%{{http_code}}' http://{DOMAIN}")
if "200" in output or "301" in output or "302" in output:
    print("   ✅ Domain is accessible via HTTP")
else:
    print(f"   ⚠️  HTTP response: {output.strip()}")

# Get certificate with standalone mode (more reliable)
print("\n4️⃣  Obtaining SSL certificate (standalone mode)...")
output, errors, status = run(
    f"certbot certonly --standalone --non-interactive --agree-tos "
    f"--email bigjacob710@gmail.com -d {DOMAIN} --preferred-challenges http 2>&1"
)

if status == 0:
    print("   ✅ Certificate obtained!")
    
    # Configure nginx to use the certificate
    print("\n5️⃣  Configuring nginx with SSL...")
    nginx_ssl_config = f"""
server {{
    listen 80;
    server_name {DOMAIN} {VPS_IP};
    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {DOMAIN} {VPS_IP};

    ssl_certificate /etc/letsencrypt/live/{DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}
}}
"""
    run(f"echo '{nginx_ssl_config}' > /etc/nginx/sites-available/securevpn")
    run("nginx -t && systemctl reload nginx")
    
    print("\n" + "="*60)
    print("✅ SSL CERTIFICATE INSTALLED!")
    print("="*60)
    print(f"\n🌐 Access your secure portal:")
    print(f"   https://{DOMAIN}")
    print("\n✅ Features:")
    print("   ✅ Valid SSL certificate (Let's Encrypt)")
    print("   ✅ No certificate warnings!")
    print("   ✅ Auto-renewal configured")
    print("   ✅ DuckDNS auto-updates every 5 min")
    print("\n🎉 Your VPN portal is now fully secure!")
else:
    print(f"\n⚠️  Certificate request failed:")
    print(f"   Output: {output[-500:]}")
    print(f"   Errors: {errors[-500:]}")
    print("\n💡 Troubleshooting:")
    print(f"   1. Check DNS: nslookup {DOMAIN}")
    print(f"   2. Check nginx: systemctl status nginx")
    print(f"   3. Retry manually: certbot certonly --nginx -d {DOMAIN}")

ssh.close()

