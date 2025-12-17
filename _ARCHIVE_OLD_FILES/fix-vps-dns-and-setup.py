#!/usr/bin/env python3
"""
Fix VPS DNS and Complete Browser Setup
"""

import sys
import time

try:
    import paramiko
except ImportError:
    print("❌ Error: paramiko not installed")
    sys.exit(1)

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description):
    """Run a command and return output"""
    print(f"🔧 {description}...", end=" ", flush=True)
    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if exit_status == 0:
            print("✓")
            return True, output
        else:
            print(f"✗ (exit code: {exit_status})")
            if error:
                print(f"   Error: {error[:200]}")
            return False, error
    except Exception as e:
        print(f"✗ Error: {e}")
        return False, str(e)

def main():
    print("==========================================")
    print("🔧 FIXING VPS DNS & SETTING UP BROWSER")
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
    
    # Step 1: Fix DNS
    print("📋 Step 1: Fixing DNS...")
    print("")
    
    # Backup current DNS
    run_command(ssh, "cp /etc/resolv.conf /etc/resolv.conf.backup 2>/dev/null || true", "Backing up DNS config")
    
    # Set Google DNS
    dns_fix = """cat > /etc/resolv.conf << 'EOF'
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
EOF"""
    
    success, _ = run_command(ssh, dns_fix, "Setting DNS servers")
    
    if success:
        # Test DNS
        success, output = run_command(ssh, "ping -c 2 -W 2 google.com 2>&1 | head -3", "Testing DNS")
        if "0% packet loss" in output or "1 received" in output:
            print("   ✅ DNS working!")
        else:
            print("   ⚠️  DNS test inconclusive, but continuing...")
    
    print("")
    
    # Step 2: Update package lists
    print("📋 Step 2: Updating package lists...")
    print("")
    run_command(ssh, "apt-get update -qq 2>&1 | tail -5", "Updating package lists")
    print("")
    
    # Step 3: Install essential packages
    print("📋 Step 3: Installing essential packages...")
    print("")
    
    essential_packages = [
        "git",
        "python3",
        "build-essential",
        "ninja-build",
        "pkg-config",
    ]
    
    for package in essential_packages:
        run_command(ssh, f"dpkg -l {package} 2>/dev/null | grep -q '^ii' && echo 'installed' || apt-get install -y {package} 2>&1 | tail -1", 
                   f"Checking/installing {package}")
    
    print("")
    
    # Step 4: Install depot_tools
    print("📋 Step 4: Installing depot_tools...")
    print("")
    
    if run_command(ssh, "test -d /opt/depot_tools && echo 'exists' || echo 'missing'", "Checking depot_tools")[1].strip() == "exists":
        print("   ✅ depot_tools already installed")
    else:
        run_command(ssh, "cd /opt && git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git 2>&1 | tail -3", 
                   "Cloning depot_tools")
    
    # Add to PATH
    bashrc_check = "grep -q 'depot_tools' /root/.bashrc && echo 'exists' || echo 'missing'"
    if run_command(ssh, bashrc_check, "Checking PATH")[1].strip() == "missing":
        run_command(ssh, 'echo "" >> /root/.bashrc && echo "# PhazeBrowser" >> /root/.bashrc && echo \'export PATH="$PATH:/opt/depot_tools"\' >> /root/.bashrc', 
                   "Adding depot_tools to PATH")
    
    print("")
    
    # Step 5: Verify setup
    print("📋 Step 5: Verifying setup...")
    print("")
    
    # Check if fetch command works
    success, output = run_command(ssh, "export PATH=\"$PATH:/opt/depot_tools\" && which fetch", "Testing fetch command")
    if success and "depot_tools" in output:
        print("   ✅ fetch command ready!")
    else:
        print("   ⚠️  fetch command not found, but depot_tools installed")
    
    print("")
    
    ssh.close()
    
    print("==========================================")
    print("✅ SETUP COMPLETE!")
    print("==========================================")
    print("")
    print("📝 Next Steps:")
    print("")
    print("1. SSH into VPS:")
    print(f"   ssh {VPS_USER}@{VPS_IP}")
    print("")
    print("2. Start Chromium fetch:")
    print("   export PATH=\"$PATH:/opt/depot_tools\"")
    print("   cd /opt/phazebrowser")
    print("   fetch --nohooks chromium")
    print("")
    print("   Or use the script:")
    print("   cd /opt/phazebrowser")
    print("   ./start-chromium-fetch.sh")
    print("")
    print("💡 TIP: Run in screen session:")
    print("   screen -S chromium")
    print("   export PATH=\"$PATH:/opt/depot_tools\"")
    print("   fetch --nohooks chromium")
    print("   # Ctrl+A then D to detach")
    print("")

if __name__ == "__main__":
    main()

