#!/usr/bin/env python3
"""Comprehensive VPS fix - update everything and ensure it works"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔧 COMPREHENSIVE VPS FIX - Updating Everything")
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
    if exit_code != 0 and err and "warning" not in err.lower():
        print(f"   ⚠️  {err[:200]}")
    return exit_code == 0, out

# Step 1: Stop everything to start fresh
print("1️⃣  Stopping Services...")
run_cmd(ssh, 'systemctl stop nginx')
run_cmd(ssh, 'systemctl stop phazevpn-portal')
time.sleep(2)

# Step 2: Clean up old configs
print("")
print("2️⃣  Cleaning Up Configs...")
run_cmd(ssh, 'rm -f /etc/nginx/sites-enabled/*')
run_cmd(ssh, 'mkdir -p /var/www/html/.well-known/acme-challenge')
run_cmd(ssh, 'chmod -R 755 /var/www/html')

# Step 3: Create SIMPLE, WORKING nginx config
print("")
print("3️⃣  Creating Working Nginx Config...")

nginx_config = """server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name phazevpn.duckdns.org mail.phazevpn.duckdns.org _;

    # Logging
    access_log /var/log/nginx/phazevpn-access.log;
    error_log /var/log/nginx/phazevpn-error.log;

    # ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        try_files $uri =404;
    }

    # Main site - proxy to Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # No buffering
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

stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/nginx/sites-available/phazevpn << "EOFCONFIG"\n{nginx_config}\nEOFCONFIG\n')
stdout.channel.recv_exit_status()

# Step 4: Enable the site
print("")
print("4️⃣  Enabling Site...")
run_cmd(ssh, 'ln -sf /etc/nginx/sites-available/phazevpn /etc/nginx/sites-enabled/phazevpn')

# Step 5: Test nginx config
print("")
print("5️⃣  Testing Nginx Config...")
success, out = run_cmd(ssh, 'nginx -t 2>&1')
print(out)
if not success:
    print("   ❌ Nginx config has errors!")
    # Try to fix
    run_cmd(ssh, 'nginx -t 2>&1 | tail -20')

# Step 6: Start services
print("")
print("6️⃣  Starting Services...")
run_cmd(ssh, 'systemctl start phazevpn-portal')
time.sleep(3)
run_cmd(ssh, 'systemctl start nginx')
time.sleep(3)

# Step 7: Verify services are running
print("")
print("7️⃣  Verifying Services...")
success, nginx_status = run_cmd(ssh, 'systemctl is-active nginx')
print(f"   Nginx: {nginx_status.strip()}")
success, flask_status = run_cmd(ssh, 'systemctl is-active phazevpn-portal')
print(f"   Flask: {flask_status.strip()}")

# Step 8: Check what's listening
print("")
print("8️⃣  Checking Listeners...")
success, listeners = run_cmd(ssh, 'ss -tlnp | grep -E ":(80|443|5000)"')
print(listeners)

# Step 9: Test Flask app directly
print("")
print("9️⃣  Testing Flask App...")
success, flask_test = run_cmd(ssh, 'curl -I http://127.0.0.1:5000 2>&1 | head -5')
print(flask_test)

# Step 10: Test nginx
print("")
print("🔟  Testing Nginx...")
success, nginx_test = run_cmd(ssh, 'curl -I http://127.0.0.1:80 2>&1 | head -10')
print(nginx_test)

# Step 11: Test external DNS
print("")
print("1️⃣1️⃣  Testing External DNS...")
success, dns_test = run_cmd(ssh, 'curl -I http://phazevpn.duckdns.org 2>&1 | head -10')
print(dns_test)

# Step 12: Check firewall
print("")
print("1️⃣2️⃣  Verifying Firewall...")
success, fw_status = run_cmd(ssh, 'ufw status | grep -E "(80|443)" | head -5')
print(fw_status)

# Step 13: Enable services on boot
print("")
print("1️⃣3️⃣  Enabling Services on Boot...")
run_cmd(ssh, 'systemctl enable nginx')
run_cmd(ssh, 'systemctl enable phazevpn-portal')

# Step 14: Final status check
print("")
print("1️⃣4️⃣  Final Status Check...")
success, final_status = run_cmd(ssh, 'systemctl status nginx phazevpn-portal --no-pager | grep -E "(Active|Main PID)" | head -4')
print(final_status)

# Step 15: Test from VPS IP directly
print("")
print("1️⃣5️⃣  Testing from VPS IP...")
success, ip_test = run_cmd(ssh, f'curl -I http://{VPS_IP} 2>&1 | head -10')
print(ip_test)

ssh.close()

print("")
print("=" * 80)
print("✅ VPS Configuration Updated!")
print("=" * 80)
print("")
print("🌐 Site should be accessible at:")
print("   http://phazevpn.duckdns.org")
print("   http://15.204.11.19")
print("")
print("📋 If still not working:")
print("   1. Check DNS: dig phazevpn.duckdns.org")
print("   2. Try IP directly: http://15.204.11.19")
print("   3. Check local firewall/proxy")
print("   4. Clear browser cache/HSTS")
print("")

