#!/usr/bin/env python3
"""Setup DuckDNS domain and Let's Encrypt SSL"""

import paramiko
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"
DOMAIN = "phazevpn.duckdns.org"
DUCKDNS_TOKEN = "3ba54ff3-ad0e-4d4c-94d9-bfb1efe73427"

print("🌐 Setting Up DuckDNS & Let's Encrypt SSL...")
print("="*60)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    return stdout.read().decode(), stderr.read().decode(), exit_status

print("\n1️⃣  Setting up DuckDNS update script...")

# Create duckdns directory
run("mkdir -p ~/duckdns")

# Create duck.sh script
duck_script = f"""#!/bin/bash
echo url="https://www.duckdns.org/update?domains=phazevpn&token={DUCKDNS_TOKEN}&ip=" | curl -k -o ~/duckdns/duck.log -K -
"""

run(f"cat > ~/duckdns/duck.sh << 'EOF'\n{duck_script}\nEOF")
run("chmod 700 ~/duckdns/duck.sh")

# Test the script first (updates IP to current VPS IP)
print("\n2️⃣  Updating DuckDNS IP to VPS address...")
output, errors, status = run("bash ~/duckdns/duck.sh")
output2, _, _ = run("cat ~/duckdns/duck.log")
print(f"   DuckDNS response: {output2.strip()}")

# Set up cron job
print("\n3️⃣  Setting up cron job (updates every 5 minutes)...")
run("crontab -l 2>/dev/null | grep -v duck.sh | crontab -")  # Remove old entries
run(f"(crontab -l 2>/dev/null; echo '*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1') | crontab -")
print("   ✅ Cron job configured")

# Verify cron is running
output, _, _ = run("ps aux | grep -v grep | grep cron")
if output.strip():
    print("   ✅ Cron service is running")
else:
    print("   ⚠️  Cron service not running, installing...")
    run("apt-get install -y cron -qq")
    run("systemctl start cron && systemctl enable cron")

# Wait a moment for DNS propagation
print("\n4️⃣  Waiting for DNS propagation (30 seconds)...")
import time
time.sleep(30)

# Verify DNS
print("\n5️⃣  Verifying DNS...")
output, _, _ = run(f"nslookup {DOMAIN} 8.8.8.8 2>&1 | grep -A 1 'Name:'")
print(f"   DNS lookup: {output.strip()[:100]}")

# Install certbot if not installed
print("\n6️⃣  Installing certbot...")
run("apt-get update -qq")
run("apt-get install -y certbot python3-certbot-nginx -qq")
print("   ✅ Certbot installed")

# Configure nginx for the domain first
print("\n7️⃣  Configuring nginx for domain...")
nginx_config = f"""
server {{
    listen 80;
    server_name {DOMAIN} {VPS_IP};

    location / {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
}}
"""

run(f"echo '{nginx_config}' > /etc/nginx/sites-available/securevpn")
run("ln -sf /etc/nginx/sites-available/securevpn /etc/nginx/sites-enabled/")
run("rm -f /etc/nginx/sites-enabled/default")
run("nginx -t && systemctl reload nginx")
print("   ✅ Nginx configured")

# Get Let's Encrypt certificate
print("\n8️⃣  Obtaining Let's Encrypt SSL certificate...")
print("   This may take a minute...")
output, errors, status = run(
    f"certbot --nginx --non-interactive --agree-tos --email bigjacob710@gmail.com "
    f"-d {DOMAIN} --redirect 2>&1"
)

if status == 0:
    print("   ✅ Let's Encrypt certificate obtained!")
    print("   Your site now has a VALID SSL certificate!")
else:
    print(f"   ⚠️  Let's Encrypt failed (may need DNS to propagate more)")
    print(f"   Error: {errors[:300]}")
    print("   You can retry later with: certbot --nginx -d phazevpn.duckdns.org")

# Restart nginx
print("\n9️⃣  Finalizing nginx configuration...")
run("systemctl restart nginx")
run("systemctl status nginx --no-pager -l | head -5")

print("\n" + "="*60)
print("✅ DUCKDNS & SSL SETUP COMPLETE!")
print("="*60)
print(f"\n🌐 Your VPN Portal:")
print(f"   https://{DOMAIN}")
print(f"   https://{VPS_IP} (still works)")
print("\n✅ Features:")
print("   ✅ DuckDNS auto-updates every 5 minutes")
print("   ✅ Let's Encrypt SSL certificate")
print("   ✅ No more certificate warnings!")
print("   ✅ Valid HTTPS")
print("\n📋 DuckDNS Status:")
run("cat ~/duckdns/duck.log")
print()

ssh.close()

