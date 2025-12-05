#!/usr/bin/env python3
"""
Verify everything is on VPS and working
"""
import paramiko

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)

print("=" * 70)
print("📋 VERIFYING EVERYTHING IS ON VPS")
print("=" * 70)

# Services
print("\n✅ SERVICES:")
stdin, stdout, stderr = ssh.exec_command('systemctl is-active phazevpn-portal.service')
flask_status = stdout.read().decode().strip()
print(f"   Flask Portal: {flask_status}")

stdin, stdout, stderr = ssh.exec_command('systemctl is-active nginx')
nginx_status = stdout.read().decode().strip()
print(f"   Nginx: {nginx_status}")

# Ports
print("\n✅ LISTENING PORTS:")
stdin, stdout, stderr = ssh.exec_command('netstat -tlnp 2>/dev/null | grep -E ":5000|:80" | grep LISTEN')
ports = stdout.read().decode().strip()
print(f"   {ports if ports else 'No ports found'}")

# Files on VPS
print("\n✅ TEMPLATE FILES ON VPS:")
stdin, stdout, stderr = ssh.exec_command('ls /opt/secure-vpn/web-portal/templates/*.html 2>/dev/null | wc -l')
count = stdout.read().decode().strip()
print(f"   Total HTML templates: {count}")

stdin, stdout, stderr = ssh.exec_command('ls -lh /opt/secure-vpn/web-portal/app.py')
app_info = stdout.read().decode().strip()
print(f"   {app_info}")

# base.html verification
print("\n✅ BASE.HTML VERIFICATION:")
stdin, stdout, stderr = ssh.exec_command("grep -c \"url_for('index')\" /opt/secure-vpn/web-portal/templates/base.html")
index_count = stdout.read().decode().strip()
stdin, stdout, stderr = ssh.exec_command("grep -c \"url_for('home')\" /opt/secure-vpn/web-portal/templates/base.html")
home_count = stdout.read().decode().strip()
print(f"   url_for('index'): {index_count} instances ✓")
print(f"   url_for('home'): {home_count} instances (should be 0)")

# Website responses
print("\n✅ WEBSITE RESPONSES:")
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:5000/ 2>&1 | head -1')
first_line = stdout.read().decode().strip()
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:5000/ 2>&1 | wc -c')
size = stdout.read().decode().strip()
if '<!DOCTYPE html>' in first_line:
    print(f"   ✅ Flask responding ({size} bytes)")
else:
    print(f"   ⚠️  Flask: {first_line[:60]}")

stdin, stdout, stderr = ssh.exec_command('curl -s -H "Host: phazevpn.duckdns.org" http://127.0.0.1/ 2>&1 | head -1')
nginx_first = stdout.read().decode().strip()
stdin, stdout, stderr = ssh.exec_command('curl -s -H "Host: phazevpn.duckdns.org" http://127.0.0.1/ 2>&1 | wc -c')
nginx_size = stdout.read().decode().strip()
if '<!DOCTYPE html>' in nginx_first:
    print(f"   ✅ Nginx proxying correctly ({nginx_size} bytes)")
else:
    print(f"   ⚠️  Nginx: {nginx_first[:60]}")

# Systemd service file
print("\n✅ SYSTEMD SERVICE:")
stdin, stdout, stderr = ssh.exec_command('test -f /etc/systemd/system/phazevpn-portal.service && echo "EXISTS" || echo "MISSING"')
service_exists = stdout.read().decode().strip()
print(f"   Service file: {service_exists}")

# Nginx config
print("\n✅ NGINX CONFIG:")
stdin, stdout, stderr = ssh.exec_command('ls -la /etc/nginx/sites-enabled/')
print(stdout.read().decode().strip())

ssh.close()
print("\n" + "=" * 70)
print("✅ VERIFICATION COMPLETE!")
print("=" * 70)
print("\n🌐 Website should be accessible at:")
print("   - http://phazevpn.duckdns.org")
print("   - http://15.204.11.19")

