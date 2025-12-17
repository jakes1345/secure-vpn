#!/usr/bin/env python3
"""Comprehensive website audit and fix"""

import paramiko
import time

VPS_IP = '15.204.11.19'
VPS_USER = 'root'
VPS_PASS = 'Jakes1328!@'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)

print('='*70)
print('🔍 DEEP DIVE WEBSITE AUDIT')
print('='*70)

# 1. Test app import
print('\n1️⃣ TESTING APP IMPORT')
print('-'*70)
test_import = '''#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/phaze-vpn/web-portal")
try:
    from app import app
    print("✅ App imported successfully")
except Exception as e:
    print(f"❌ Import failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
'''

stdin, stdout, stderr = ssh.exec_command("cat > /tmp/test_import.py << 'EOF'\n" + test_import + "\nEOF")
stdout.channel.recv_exit_status()

stdin, stdout, stderr = ssh.exec_command("cd /opt/phaze-vpn/web-portal && python3 /tmp/test_import.py 2>&1")
import_result = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
print(import_result[:3000])

# 2. Test homepage route
print('\n2️⃣ TESTING HOMEPAGE ROUTE')
print('-'*70)
test_homepage = '''#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/phaze-vpn/web-portal")
from app import app

with app.test_client() as client:
    try:
        response = client.get("/")
        print(f"Status: {response.status_code}")
        if response.status_code == 500:
            print("500 Error detected")
            # Try to get exception info
            print(f"Response length: {len(response.data)}")
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
'''

stdin, stdout, stderr = ssh.exec_command("cat > /tmp/test_homepage.py << 'EOF'\n" + test_homepage + "\nEOF")
stdout.channel.recv_exit_status()

stdin, stdout, stderr = ssh.exec_command("cd /opt/phaze-vpn/web-portal && python3 /tmp/test_homepage.py 2>&1")
homepage_result = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
print(homepage_result[:3000])

# 3. Check for actual runtime errors
print('\n3️⃣ CHECKING RUNTIME ERRORS')
print('-'*70)
# Make a request to trigger error
ssh.exec_command('curl -s http://localhost:5000/ > /dev/null 2>&1')
time.sleep(2)

# Check journalctl
stdin, stdout, stderr = ssh.exec_command('journalctl -u phazevpn-portal --since "5 seconds ago" --no-pager | tail -50')
journal_output = stdout.read().decode('utf-8')
if 'Exception' in journal_output or 'Traceback' in journal_output or 'Error' in journal_output:
    print('Errors found:')
    # Extract the error
    lines = journal_output.split('\n')
    error_start = None
    for i, line in enumerate(lines):
        if 'Exception' in line or 'Traceback' in line:
            error_start = i
            break
    if error_start:
        print('\n'.join(lines[error_start:error_start+30]))
else:
    print('No runtime errors in journal')

# 4. Check homepage route code
print('\n4️⃣ CHECKING HOMEPAGE ROUTE CODE')
print('-'*70)
stdin, stdout, stderr = ssh.exec_command('sed -n "684,720p" /opt/phaze-vpn/web-portal/app.py')
homepage_code = stdout.read().decode('utf-8')
print(homepage_code[:1000])

# 5. Check if template exists
print('\n5️⃣ CHECKING TEMPLATES')
print('-'*70)
stdin, stdout, stderr = ssh.exec_command('ls -la /opt/phaze-vpn/web-portal/templates/index.html /opt/phaze-vpn/web-portal/templates/home.html 2>&1')
template_check = stdout.read().decode('utf-8')
print(template_check[:500])

# 6. Check gunicorn workers
print('\n6️⃣ CHECKING GUNICORN WORKERS')
print('-'*70)
stdin, stdout, stderr = ssh.exec_command('ps aux | grep gunicorn | grep worker | wc -l')
worker_count = stdout.read().decode('utf-8').strip()
print(f'Active workers: {worker_count}')

# 7. Enable Flask debug mode temporarily to see errors
print('\n7️⃣ ENABLING DEBUG MODE TO SEE ERRORS')
print('-'*70)
# Check if we can enable debug
stdin, stdout, stderr = ssh.exec_command('grep -n "app.run\|debug" /opt/phaze-vpn/web-portal/app.py | head -5')
print(stdout.read().decode('utf-8')[:500])

ssh.close()

