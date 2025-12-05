#!/usr/bin/env python3
"""
Directly fix the indentation error - line 714 needs 8 spaces
"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

# Read the file
stdin, stdout, stderr = ssh.exec_command(f"cat {VPN_DIR}/web-portal/app.py")
full_file = stdout.read().decode()

# Fix line 714 specifically - it should have 8 spaces (inside if request.method == 'POST':)
lines = full_file.split('\n')

# Line 714 is index 713 (0-indexed)
if len(lines) > 713:
    line_714 = lines[713]
    # If it doesn't start with 8 spaces, fix it
    if not line_714.startswith('        '):  # 8 spaces
        lines[713] = '        ' + line_714.lstrip()
        print(f"Fixed line 714: {repr(lines[713])}")
    else:
        print(f"Line 714 already correct: {repr(lines[713])}")

# Also ensure line 715+ are properly indented
for i in range(714, min(765, len(lines))):
    line = lines[i]
    if line.strip() and not line.strip().startswith('@') and not line.strip().startswith('def '):
        # Should be indented at least 8 spaces (inside the if POST block)
        # or 12 spaces (inside nested if blocks)
        if not line.startswith(' ') and line.strip():
            # Not indented at all - this is wrong
            if not line.strip().startswith('@') and not line.strip().startswith('def '):
                # Indent it
                lines[i] = '        ' + line.lstrip()
                print(f"Fixed line {i+1}: {repr(lines[i][:50])}")

# Write back
new_file = '\n'.join(lines)
stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/app.py << 'EOF'\n{new_file}\nEOF")
stdout.channel.recv_exit_status()

# Verify syntax
stdin, stdout, stderr = ssh.exec_command(f"python3 -m py_compile {VPN_DIR}/web-portal/app.py 2>&1")
result = stdout.read().decode()
if not result:
    print("✅ Syntax is valid!")
else:
    print(f"❌ Syntax error: {result}")

# Restart service
ssh.exec_command("systemctl restart secure-vpn-download")
import time
time.sleep(3)

stdin, stdout, stderr = ssh.exec_command("systemctl status secure-vpn-download --no-pager | head -3")
status = stdout.read().decode()
if 'active (running)' in status:
    print("✅ Service is running!")
else:
    print(f"⚠️ Status: {status}")

ssh.close()

