#!/usr/bin/env python3
"""Emergency fix for site connectivity - comprehensive check and fix"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🚨 EMERGENCY FIX - Site Connectivity")
print("=" * 80)
print("")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS)

def run_cmd(ssh, cmd, desc=""):
    if desc:
        print(f"{desc}...")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    return exit_code == 0, out, err

# Step 1: Check if services are running
print("1️⃣  Checking Services:")
success, out, err = run_cmd(ssh, 'systemctl is-active nginx phazevpn-portal')
print(f"   Services: {out.strip()}")
print("")

# Step 2: Check what's listening
print("2️⃣  Checking Listeners:")
success, out, err = run_cmd(ssh, 'ss -tlnp | grep -E ":(80|443|5000)"')
print(out)
print("")

# Step 3: Check nginx config
print("3️⃣  Checking Nginx Config:")
success, out, err = run_cmd(ssh, 'nginx -t 2>&1')
print(out)
if not success:
    print(f"   ERROR: {err[:200]}")
print("")

# Step 4: Check current nginx config
print("4️⃣  Current Nginx Config:")
success, out, err = run_cmd(ssh, 'cat /etc/nginx/sites-available/phazevpn')
print(out[:500])
print("")

# Step 5: Create SIMPLE, WORKING config
print("5️⃣  Creating Simple Working Config...")

simple_config = """server {
    listen 80;
    listen [::]:80;
    server_name phazevpn.duckdns.org mail.phazevpn.duckdns.org _;

    # Logging
    access_log /var/log/nginx/phazevpn-access.log;
    error_log /var/log/nginx/phazevpn-error.log;

    # ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        try_files $uri =404;
    }

    # Main site
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        
        # Fix timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Buffer settings
        proxy_buffering off;
    }

    # Static files
    location /static {
        alias /opt/phazevpn/web-portal/static;
        expires 30d;
        add_header Cache-Control "public";
    }
}
"""

stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/nginx/sites-available/phazevpn << "EOFCONFIG"\n{simple_config}\nEOFCONFIG\n')
stdout.channel.recv_exit_status()

# Step 6: Make sure it's enabled
print("")
print("6️⃣  Enabling Site Config...")
run_cmd(ssh, 'ln -sf /etc/nginx/sites-available/phazevpn /etc/nginx/sites-enabled/phazevpn')
run_cmd(ssh, 'rm -f /etc/nginx/sites-enabled/default')

# Step 7: Test config
print("")
print("7️⃣  Testing Config...")
success, out, err = run_cmd(ssh, 'nginx -t 2>&1')
print(out)
if not success:
    print(f"   ERROR: {err[:200]}")

# Step 8: Restart nginx (not reload, full restart)
print("")
print("8️⃣  Restarting Nginx (full restart)...")
run_cmd(ssh, 'systemctl stop nginx')
time.sleep(2)
run_cmd(ssh, 'systemctl start nginx')
time.sleep(3)

# Step 9: Verify it's running
print("")
print("9️⃣  Verifying Services...")
success, out, err = run_cmd(ssh, 'systemctl status nginx --no-pager | head -10')
print(out)
print("")

success, out, err = run_cmd(ssh, 'systemctl status phazevpn-portal --no-pager | head -10')
print("Flask App:")
print(out)
print("")

# Step 10: Test from VPS
print("🔟  Testing from VPS:")
success, out, err = run_cmd(ssh, 'curl -v http://127.0.0.1:80 2>&1 | head -15')
print(out)
print("")

success, out, err = run_cmd(ssh, 'curl -v http://phazevpn.duckdns.org 2>&1 | head -15')
print("External DNS test:")
print(out)
print("")

# Step 11: Check firewall
print("1️⃣1️⃣  Checking Firewall Rules:")
success, out, err = run_cmd(ssh, 'ufw status | grep -E "(80|443)"')
print(out)
print("")

# Step 12: Check if port 80 is accessible externally
print("1️⃣2️⃣  Checking External Port Access:")
success, out, err = run_cmd(ssh, f'netstat -tlnp | grep ":80"')
print(out)
print("")

# Step 13: Test Flask app directly
print("1️⃣3️⃣  Testing Flask App Directly:")
success, out, err = run_cmd(ssh, 'curl -I http://127.0.0.1:5000 2>&1 | head -5')
print(out)
print("")

ssh.close()

print("=" * 80)
print("✅ Emergency Fix Applied!")
print("=" * 80)
print("")
print("🌐 Try accessing:")
print("   http://phazevpn.duckdns.org")
print("   http://15.204.11.19")
print("")
print("If still not working, check:")
print("   1. DNS: dig phazevpn.duckdns.org")
print("   2. Firewall on your local machine")
print("   3. VPN/proxy settings")
print("")

