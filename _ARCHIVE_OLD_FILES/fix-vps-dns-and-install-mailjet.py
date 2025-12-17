#!/usr/bin/env python3
"""
Fix VPS DNS and install Mailjet
"""

from paramiko import SSHClient, AutoAddPolicy
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("==========================================")
print("🔧 FIXING VPS DNS & INSTALLING MAILJET")
print("==========================================")
print("")

ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())

try:
    print("📡 Connecting to VPS...")
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("   ✅ Connected!")
    print("")
    
    # Fix DNS
    print("🔧 Fixing DNS...")
    commands = [
        "echo 'nameserver 8.8.8.8' > /etc/resolv.conf",
        "echo 'nameserver 1.1.1.1' >> /etc/resolv.conf",
        "echo 'nameserver 8.8.4.4' >> /etc/resolv.conf",
        "chattr +i /etc/resolv.conf 2>/dev/null || true"  # Prevent overwrite
    ]
    
    for cmd in commands:
        ssh.exec_command(cmd)
    
    # Verify DNS
    stdin, stdout, stderr = ssh.exec_command("cat /etc/resolv.conf")
    dns_config = stdout.read().decode()
    print("   DNS configured:")
    print(f"   {dns_config.strip().replace(chr(10), ' | ')}")
    print("")
    
    # Test connectivity
    print("🧪 Testing connectivity...")
    stdin, stdout, stderr = ssh.exec_command("ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1 && echo 'OK' || echo 'FAIL'")
    network_ok = stdout.read().decode().strip()
    print(f"   Network: {network_ok}")
    print("")
    
    if network_ok == "FAIL":
        print("   ⚠️  Network issue - may need to check VPS network settings")
        print("")
    
    # Install mailjet-rest
    print("📦 Installing mailjet-rest...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /opt/secure-vpn/web-portal && pip3 install mailjet-rest 2>&1",
        timeout=60
    )
    
    # Wait for command to complete
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error_output = stderr.read().decode()
    
    if exit_status == 0 or "Successfully installed" in output:
        print("   ✅ Mailjet installed successfully!")
        if "Successfully installed" in output:
            print(f"   {[line for line in output.split(chr(10)) if 'Successfully' in line][0]}")
    else:
        print(f"   ❌ Installation failed")
        print(f"   Error: {error_output[-300:] if error_output else output[-300:]}")
        print("")
        print("   💡 Trying alternative method...")
        
        # Try with --break-system-packages
        stdin, stdout, stderr = ssh.exec_command(
            "pip3 install --break-system-packages mailjet-rest 2>&1",
            timeout=60
        )
        exit_status2 = stdout.channel.recv_exit_status()
        output2 = stdout.read().decode()
        
        if exit_status2 == 0 or "Successfully installed" in output2:
            print("   ✅ Mailjet installed with --break-system-packages!")
        else:
            print(f"   ❌ Still failed: {output2[-200:]}")
    
    print("")
    print("==========================================")
    print("✅ COMPLETE")
    print("==========================================")
    print("")
    print("📝 Next: Restart web portal on VPS")
    print("")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    ssh.close()

