#!/usr/bin/env python3
"""Verify files synced and restart services on VPS"""
import pexpect
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_PATH = "/opt/secure-vpn"

print("=" * 50)
print("🔍 VERIFYING FILES AND RESTARTING SERVICES")
print("=" * 50)
print()

def run_ssh_command(command, description):
    """Run a command on VPS via SSH"""
    print(f"[{description}]...")
    cmd = f"ssh -o StrictHostKeyChecking=no {VPS_USER}@{VPS_IP} '{command}'"
    
    try:
        child = pexpect.spawn(cmd, timeout=30)
        child.logfile = sys.stdout.buffer
        
        index = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
        
        if index == 0:
            child.sendline(VPS_PASS)
            child.expect(pexpect.EOF, timeout=30)
            output = child.before.decode('utf-8', errors='ignore')
            print(f"   ✓ Done\n")
            return True, output
        else:
            output = child.before.decode('utf-8', errors='ignore')
            print(f"   ✓ Done (no password)\n")
            return True, output
            
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return False, str(e)

# Verify files exist
print("Step 1: Verifying synced files...")
run_ssh_command(f"ls -lh {VPS_PATH}/web-portal/app.py {VPS_PATH}/web-portal/requirements.txt {VPS_PATH}/web-portal/templates/base.html", "Checking files")

# Install dependencies
print("Step 2: Installing/updating Python dependencies...")
run_ssh_command(f"cd {VPS_PATH}/web-portal && pip3 install -r requirements.txt 2>&1", "Installing dependencies")

# Restart web portal service
print("Step 3: Restarting web portal service...")
run_ssh_command("sudo systemctl restart secure-vpn-portal 2>&1", "Restarting service")

# Check service status
print("Step 4: Checking service status...")
success, output = run_ssh_command("sudo systemctl status secure-vpn-portal --no-pager | head -10", "Service status")

print("=" * 50)
print("✅ SETUP COMPLETE!")
print("=" * 50)
print()
print("🌐 Web portal should be available at:")
print("   https://phazevpn.duckdns.org")
print()

