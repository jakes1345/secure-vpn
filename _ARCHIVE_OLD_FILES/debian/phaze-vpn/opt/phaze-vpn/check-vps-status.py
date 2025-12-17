#!/usr/bin/env python3
"""Check VPS status and services"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔍 Checking VPS Status")
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

# Check services
print("1️⃣  Checking Services:")
print("")

# Nginx
success, out, err = run_cmd(ssh, 'systemctl status nginx --no-pager | head -10')
print("Nginx:")
print(out)
print("")

# Flask app
success, out, err = run_cmd(ssh, 'systemctl status phazevpn-portal --no-pager | head -10')
print("Flask Portal:")
print(out)
print("")

# Check ports
print("2️⃣  Checking Ports:")
success, out, err = run_cmd(ssh, 'netstat -tlnp | grep -E ":(80|443|5000)"')
print(out)
print("")

# Check nginx config
print("3️⃣  Checking Nginx Config:")
success, out, err = run_cmd(ssh, 'nginx -t 2>&1')
print(out)
print("")

# Check if nginx is listening
print("4️⃣  Checking Nginx Listen Status:")
success, out, err = run_cmd(ssh, 'ss -tlnp | grep -E ":(80|443)"')
print(out if out else "   No listeners found")
print("")

# Check firewall
print("5️⃣  Checking Firewall:")
success, out, err = run_cmd(ssh, 'ufw status 2>&1 || iptables -L -n | head -10')
print(out)
print("")

# Test local connectivity
print("6️⃣  Testing Local Connectivity:")
success, out, err = run_cmd(ssh, 'curl -I http://127.0.0.1:5000 2>&1 | head -5')
print(out)
print("")

success, out, err = run_cmd(ssh, 'curl -I http://127.0.0.1:80 2>&1 | head -5')
print("Nginx HTTP:")
print(out)
print("")

# Check certificate
print("7️⃣  Checking SSL Certificate:")
success, out, err = run_cmd(ssh, 'ls -la /etc/letsencrypt/live/phazevpn.duckdns.org/ 2>&1')
print(out)
print("")

ssh.close()

print("=" * 80)
print("✅ Status Check Complete")
print("=" * 80)
