#!/bin/bash
# Complete website fix - everything at once

set -e

echo "🔧 COMPLETE WEBSITE FIX"
echo "======================"

python3 << 'PYEOF'
import paramiko
import base64
from pathlib import Path

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    exit_status = stdout.channel.recv_exit_status()
    return stdout.read().decode().strip(), stderr.read().decode().strip()

print("1. Stopping Flask...")
run("pkill -9 -f 'python.*app.py'; sleep 1")

print("2. Reading local base.html...")
with open('web-portal/templates/base.html', 'r') as f:
    base_content = f.read()

print(f"   Local file: {len(base_content)} bytes")

print("3. Uploading base.html to VPS...")
sftp = ssh.open_sftp()
remote_path = "/opt/secure-vpn/web-portal/templates/base.html"
with sftp.file(remote_path, 'w') as f:
    f.write(base_content)
sftp.close()

print("4. Verifying upload...")
output, _ = run(f"wc -c {remote_path}")
print(f"   {output}")

print("5. Starting Flask...")
run("cd /opt/secure-vpn/web-portal && nohup python3 app.py > /tmp/flask.log 2>&1 &")
import time
time.sleep(3)

print("6. Testing Flask...")
output, _ = run("curl -s http://127.0.0.1:5000/ | head -20")
if len(output) > 100:
    print(f"   ✅ Flask working! ({len(output)} bytes)")
else:
    print(f"   ⚠️  Flask: {output[:100]}")

print("7. Restarting Nginx...")
run("systemctl restart nginx")

print("8. Final test...")
output, _ = run("curl -s -H 'Host: phazevpn.duckdns.org' http://127.0.0.1/ | head -20")
if len(output) > 100:
    print(f"   ✅ Website working! ({len(output)} bytes)")
else:
    print(f"   ⚠️  Website: {output[:100]}")

ssh.close()
print("\n✅ DONE!")
PYEOF

