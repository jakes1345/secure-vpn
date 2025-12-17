#!/usr/bin/env python3
"""Fix nginx config and restore site accessibility"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔧 Fixing Nginx and Restoring Site")
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

# Step 1: Check current nginx config
print("1️⃣  Checking current Nginx config...")
success, current_config = run_cmd(ssh, 'cat /etc/nginx/sites-available/phazevpn 2>&1')
print(current_config[:500])
print("")

# Step 2: Create proper HTTP-only config (no SSL for now)
print("2️⃣  Creating HTTP-only Nginx config...")

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
        proxy_http_version 1.1;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static {
        alias /opt/phazevpn/web-portal/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
"""

stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/nginx/sites-available/phazevpn << "EOFCONFIG"\n{nginx_config}\nEOFCONFIG\n')
stdout.channel.recv_exit_status()

# Step 3: Test and reload
print("")
print("3️⃣  Testing and reloading Nginx...")
run_cmd(ssh, 'nginx -t')
run_cmd(ssh, 'systemctl reload nginx')
time.sleep(2)

# Step 4: Verify it's working
print("")
print("4️⃣  Verifying services...")
run_cmd(ssh, 'systemctl status nginx --no-pager | head -5')
print("")

# Test from VPS
print("5️⃣  Testing from VPS:")
success, test_output = run_cmd(ssh, 'curl -I http://phazevpn.duckdns.org 2>&1 | head -10')
print(test_output)
print("")

# Check what's listening
print("6️⃣  Checking what's listening:")
success, listeners = run_cmd(ssh, 'ss -tlnp | grep -E ":(80|443)"')
print(listeners)
print("")

# Test external connectivity
print("7️⃣  Testing external connectivity:")
success, external_test = run_cmd(ssh, f'curl -I http://{VPS_IP} 2>&1 | head -5')
print(external_test)
print("")

ssh.close()

print("=" * 80)
print("✅ Nginx Configuration Updated!")
print("=" * 80)
print("")
print("🌐 Site should now be accessible at:")
print("   http://phazevpn.duckdns.org")
print("   http://mail.phazevpn.duckdns.org")
print("")
print("⚠️  Note: Currently HTTP only (no SSL certificate)")
print("   Once certificate is obtained, HTTPS will be enabled")
print("")

