#!/usr/bin/env python3
"""Verify VPS deployment - Check all services"""

import paramiko
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔍 Verifying VPS Deployment")
print("=" * 80)
print("")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS)

def check_service(ssh, service_name):
    """Check if service is running"""
    stdin, stdout, stderr = ssh.exec_command(f'systemctl is-active {service_name}')
    status = stdout.read().decode().strip()
    return status == 'active'

def get_service_status(ssh, service_name):
    """Get detailed service status"""
    stdin, stdout, stderr = ssh.exec_command(f'systemctl status {service_name} --no-pager -l | head -15')
    return stdout.read().decode()

# Check services
print("1️⃣  Checking Services:")
print("")

services = {
    'phazevpn-portal': 'Web Portal',
    'phazevpn-protocol': 'PhazeVPN Protocol',
    'nginx': 'Nginx',
}

all_running = True
for service, name in services.items():
    running = check_service(ssh, service)
    status = "✅ RUNNING" if running else "❌ NOT RUNNING"
    print(f"   {name}: {status}")
    if not running:
        all_running = False
        print(f"   Details:")
        print(get_service_status(ssh, service))
        print("")

# Check ports
print("")
print("2️⃣  Checking Listening Ports:")
print("")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp 2>/dev/null | grep -E "5000|51821|1194|443|80" || netstat -tlnp 2>/dev/null | grep -E "5000|51821|1194|443|80"')
ports = stdout.read().decode()
if ports:
    print(ports)
else:
    print("   ⚠️  No expected ports found")

# Check website
print("")
print("3️⃣  Testing Website:")
print("")
stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 || echo "FAILED"')
http_code = stdout.read().decode().strip()
if http_code == '200':
    print("   ✅ Portal responding (HTTP 200)")
else:
    print(f"   ⚠️  Portal returned: {http_code}")

# Check PhazeVPN Protocol
print("")
print("4️⃣  Testing PhazeVPN Protocol:")
print("")
stdin, stdout, stderr = ssh.exec_command('ss -uln 2>/dev/null | grep 51821 || netstat -uln 2>/dev/null | grep 51821')
protocol_listening = stdout.read().decode().strip()
if protocol_listening:
    print("   ✅ PhazeVPN Protocol listening on port 51821")
else:
    print("   ⚠️  PhazeVPN Protocol not listening")

# Check logs for errors
print("")
print("5️⃣  Recent Errors (last 5 lines):")
print("")
stdin, stdout, stderr = ssh.exec_command('journalctl -u phazevpn-portal -u phazevpn-protocol --no-pager -n 5 | grep -i error || echo "No recent errors"')
errors = stdout.read().decode()
if errors and 'No recent errors' not in errors:
    print(f"   ⚠️  {errors}")
else:
    print("   ✅ No recent errors")

ssh.close()

print("")
print("=" * 80)
if all_running:
    print("✅ ALL SERVICES RUNNING!")
else:
    print("⚠️  SOME SERVICES NOT RUNNING - CHECK ABOVE")
print("=" * 80)
