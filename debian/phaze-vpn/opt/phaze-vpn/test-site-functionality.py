#!/usr/bin/env python3
"""Test site functionality to find what's broken"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS)

# Test various endpoints
endpoints = ['/', '/login', '/signup', '/pricing', '/download']
print('Testing Site Endpoints:')
print('=' * 60)

for endpoint in endpoints:
    stdin, stdout, stderr = ssh.exec_command(f'curl -s -o /dev/null -w "{endpoint}: %{{http_code}}" http://127.0.0.1:5000{endpoint}')
    result = stdout.read().decode().strip()
    print(result)
    
    # Check for errors in response
    stdin, stdout, stderr = ssh.exec_command(f'curl -s http://127.0.0.1:5000{endpoint} | grep -i "error\\|exception\\|traceback" | head -3')
    errors = stdout.read().decode().strip()
    if errors:
        print(f'  ⚠️  Errors found: {errors[:100]}')

# Check Flask app for Python errors
print('\nChecking Flask App for Import Errors:')
stdin, stdout, stderr = ssh.exec_command('cd /opt/phazevpn/web-portal && python3 -c "import app" 2>&1')
import_test = stdout.read().decode()
if 'Error' in import_test or 'Traceback' in import_test:
    print('❌ Import errors found:')
    print(import_test[:500])
else:
    print('✅ No import errors')

# Check recent Flask errors
print('\nRecent Flask Errors:')
stdin, stdout, stderr = ssh.exec_command('journalctl -u phazevpn-portal --no-pager -n 100 | grep -i "error\\|exception\\|traceback" | tail -10')
errors = stdout.read().decode()
if errors:
    print(errors)
else:
    print('✅ No recent errors in logs')

ssh.close()

print('\n✅ Site functionality test complete!')

