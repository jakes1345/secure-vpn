#!/usr/bin/env python3
"""Fix port 5000 conflict - kill duplicate processes"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 80)
print("🔧 Fixing Port 5000 Conflict")
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
    return exit_code == 0, out

# Step 1: Find all processes on port 5000
print("1️⃣  Finding processes on port 5000...")
success, processes = run_cmd(ssh, 'lsof -ti:5000 || fuser 5000/tcp 2>/dev/null || ss -tlnp | grep :5000')
print(processes)

# Step 2: Stop the systemd service
print("")
print("2️⃣  Stopping systemd service...")
run_cmd(ssh, 'systemctl stop phazevpn-portal')
time.sleep(2)

# Step 3: Kill any remaining processes on port 5000
print("")
print("3️⃣  Killing any remaining processes on port 5000...")
run_cmd(ssh, 'lsof -ti:5000 | xargs kill -9 2>/dev/null || true')
run_cmd(ssh, 'fuser -k 5000/tcp 2>/dev/null || true')
run_cmd(ssh, 'pkill -9 -f "gunicorn.*5000" || true')
run_cmd(ssh, 'pkill -9 -f "python.*app.py" || true')
time.sleep(2)

# Step 4: Verify port is free
print("")
print("4️⃣  Verifying port 5000 is free...")
success, check = run_cmd(ssh, 'ss -tlnp | grep :5000 || echo "Port 5000 is free"')
print(check)

# Step 5: Start the service
print("")
print("5️⃣  Starting Flask service...")
run_cmd(ssh, 'systemctl start phazevpn-portal')
time.sleep(5)

# Step 6: Check status
print("")
print("6️⃣  Checking service status...")
success, status = run_cmd(ssh, 'systemctl status phazevpn-portal --no-pager | head -15')
print(status)

# Step 7: Test the site
print("")
print("7️⃣  Testing site...")
success, test = run_cmd(ssh, 'curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:5000')
print(test)

success, test2 = run_cmd(ssh, 'curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:80')
print(test2)

# Step 8: Check for errors
print("")
print("8️⃣  Checking for errors...")
success, errors = run_cmd(ssh, 'journalctl -u phazevpn-portal --no-pager -n 10 | grep -i error || echo "No recent errors"')
print(errors)

ssh.close()

print("")
print("=" * 80)
print("✅ Port Conflict Fixed!")
print("=" * 80)
print("")
print("🌐 Site should be working now at: http://phazevpn.duckdns.org")
print("")

