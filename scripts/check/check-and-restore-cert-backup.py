#!/usr/bin/env python3
"""Check for certificate backups and restore if possible"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔍 Checking for Certificate Backups")
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
    return exit_code == 0, out, err

# Step 1: Check for existing certificates
print("1️⃣  Checking for existing certificates...")
success, out, err = run_cmd(ssh, 'find /etc/letsencrypt -name "*.pem" -type f 2>/dev/null | head -10')
print(out if out else "   No certificate files found")

# Step 2: Check archive
print("")
print("2️⃣  Checking certificate archive...")
success, archive, err = run_cmd(ssh, 'ls -la /etc/letsencrypt/archive/ 2>/dev/null')
print(archive if archive else "   No archive found")

# Step 3: Check live directory
print("")
print("3️⃣  Checking live certificate directory...")
success, live, err = run_cmd(ssh, 'ls -la /etc/letsencrypt/live/ 2>/dev/null')
print(live if live else "   No live certificates found")

# Step 4: Try to restore from archive if it exists
if 'phazevpn.duckdns.org' in archive or 'phazevpn.duckdns.org' in live:
    print("")
    print("4️⃣  Found certificate! Restoring...")
    run_cmd(ssh, 'certbot certificates 2>&1')
    
    # Try to create symlinks if archive exists
    run_cmd(ssh, 'mkdir -p /etc/letsencrypt/live/phazevpn.duckdns.org')
    run_cmd(ssh, 'ls -la /etc/letsencrypt/archive/phazevpn.duckdns.org/ 2>&1 | head -10')
    
    # Get latest version
    success, versions, err = run_cmd(ssh, 'ls -1t /etc/letsencrypt/archive/phazevpn.duckdns.org/ 2>&1 | head -1')
    if versions.strip():
        latest = versions.strip()
        print(f"   Latest version: {latest}")
        run_cmd(ssh, f'ln -sf /etc/letsencrypt/archive/phazevpn.duckdns.org/{latest}/cert.pem /etc/letsencrypt/live/phazevpn.duckdns.org/cert.pem')
        run_cmd(ssh, f'ln -sf /etc/letsencrypt/archive/phazevpn.duckdns.org/{latest}/chain.pem /etc/letsencrypt/live/phazevpn.duckdns.org/chain.pem')
        run_cmd(ssh, f'ln -sf /etc/letsencrypt/archive/phazevpn.duckdns.org/{latest}/fullchain.pem /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem')
        run_cmd(ssh, f'ln -sf /etc/letsencrypt/archive/phazevpn.duckdns.org/{latest}/privkey.pem /etc/letsencrypt/live/phazevpn.duckdns.org/privkey.pem')
        print("   ✅ Certificate symlinks created")
else:
    print("")
    print("4️⃣  No certificate found. Need to get new one.")
    print("   DNS timeout issue - will try with different DNS server")

# Step 5: Try getting certificate with Google DNS
print("")
print("5️⃣  Trying to get certificate with Google DNS...")
run_cmd(ssh, 'systemctl stop nginx')
time.sleep(2)

# Use Google DNS for resolution
cert_cmd = 'certbot certonly --standalone -d phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --preferred-challenges http --dns-cloudflare --dns-cloudflare-credentials /dev/null 2>&1 || certbot certonly --standalone -d phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --preferred-challenges http 2>&1'
success, output, err = run_cmd(ssh, cert_cmd)

if success or 'Congratulations' in output or 'Successfully' in output:
    print("   ✅ Certificate obtained!")
else:
    print("   ⚠️  Still having issues")
    print("   Last 200 chars:", output[-200:] if output else err[-200:])

# Step 6: Start nginx
print("")
print("6️⃣  Starting Nginx...")
run_cmd(ssh, 'systemctl start nginx')

# Verify
print("")
print("7️⃣  Verifying...")
success, status, err = run_cmd(ssh, 'systemctl status nginx --no-pager | head -5')
print(status)

ssh.close()

print("")
print("=" * 80)
print("✅ Certificate Check Complete")
print("=" * 80)
print("")
print("If certificate was restored, the site should work now.")
print("mail.phazevpn.duckdns.org will redirect to phazevpn.duckdns.org")
print("")

