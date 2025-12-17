#!/usr/bin/env python3
"""
Fix DNS and install depot_tools properly
"""

import sys

try:
    import paramiko
except ImportError:
    print("❌ Error: paramiko not installed")
    sys.exit(1)

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description):
    """Run a command"""
    print(f"🔧 {description}...", end=" ", flush=True)
    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        
        if exit_status == 0:
            print("✓")
            return True, output
        else:
            print("✗")
            return False, output
    except Exception as e:
        print(f"✗ Error: {e}")
        return False, str(e)

def main():
    print("==========================================")
    print("🔧 FIXING DNS & INSTALLING depot_tools")
    print("==========================================")
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("✅ Connected to VPS")
        print("")
    except Exception as e:
        print(f"❌ Error connecting: {e}")
        sys.exit(1)
    
    # Fix DNS
    print("📋 Step 1: Fixing DNS...")
    print("")
    
    dns_fix = """cat > /etc/resolv.conf << 'EOF'
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
EOF"""
    
    run_command(ssh, dns_fix, "Setting DNS servers")
    
    # Test DNS
    success, output = run_command(ssh, "ping -c 2 -W 2 chromium.googlesource.com 2>&1 | head -3", "Testing DNS resolution")
    
    if "0% packet loss" in output or "1 received" in output or "PING" in output:
        print("   ✅ DNS working!")
    else:
        print("   ⚠️  DNS test inconclusive")
    
    print("")
    
    # Try alternative: use IP or mirror
    print("📋 Step 2: Installing depot_tools...")
    print("")
    
    # Remove old
    run_command(ssh, "rm -rf /opt/depot_tools 2>/dev/null || true", "Cleaning up")
    
    # Try cloning
    print("   Attempting to clone depot_tools...")
    success, output = run_command(ssh, "cd /opt && timeout 60 git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git 2>&1", 
                                 "Cloning depot_tools")
    
    if not success or "fatal" in output.lower():
        print("   ⚠️  Direct clone failed, trying alternative...")
        
        # Try with different DNS
        run_command(ssh, "echo 'nameserver 1.1.1.1' > /etc/resolv.conf && echo 'nameserver 8.8.8.8' >> /etc/resolv.conf", 
                   "Retrying with different DNS")
        
        # Try again
        success, output = run_command(ssh, "cd /opt && timeout 60 git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git 2>&1 | tail -5", 
                                     "Retrying clone")
    
    print("")
    
    # Verify
    print("📋 Step 3: Verifying installation...")
    print("")
    
    success, output = run_command(ssh, "test -f /opt/depot_tools/fetch && echo 'SUCCESS' || echo 'FAILED'", 
                                 "Checking if fetch exists")
    
    if "SUCCESS" in output:
        print("   ✅ depot_tools installed successfully!")
        
        # Make executable
        run_command(ssh, "chmod +x /opt/depot_tools/* 2>/dev/null; chmod +x /opt/depot_tools/.cipd_bin/* 2>/dev/null 2>/dev/null || true", 
                   "Making scripts executable")
        
        # Test
        run_command(ssh, 'export PATH="/opt/depot_tools:$PATH" && /opt/depot_tools/fetch --help 2>&1 | head -3', 
                   "Testing fetch")
    else:
        print("   ❌ Installation failed")
        print("")
        print("   Manual steps:")
        print("   1. SSH into VPS")
        print("   2. Fix DNS: echo 'nameserver 8.8.8.8' > /etc/resolv.conf")
        print("   3. cd /opt && git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git")
    
    print("")
    
    ssh.close()
    
    print("==========================================")
    if "SUCCESS" in output:
        print("✅ depot_tools INSTALLED!")
    else:
        print("⚠️  INSTALLATION NEEDS MANUAL FIX")
    print("==========================================")
    print("")

if __name__ == "__main__":
    main()

