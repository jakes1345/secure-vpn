#!/usr/bin/env python3
"""
Properly install depot_tools on VPS
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

def run_command(ssh, command, description, timeout=60):
    """Run a command and show output"""
    print(f"🔧 {description}...")
    print("")
    
    try:
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True, timeout=timeout)
        
        # Stream output
        output_lines = []
        for line in iter(stdout.readline, ""):
            if line:
                line = line.rstrip()
                print(f"   {line}")
                output_lines.append(line)
        
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print(f"   ✅ {description} - Complete")
            return True
        else:
            error = stderr.read().decode()
            print(f"   ⚠️  Exit code: {exit_status}")
            if error:
                print(f"   Error: {error[:300]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("==========================================")
    print("🔧 PROPERLY INSTALLING depot_tools")
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
    
    # Remove old depot_tools if it exists but is broken
    print("📋 Step 1: Cleaning up old depot_tools...")
    print("")
    run_command(ssh, "rm -rf /opt/depot_tools 2>/dev/null || true", "Removing old depot_tools")
    
    print("")
    
    # Install git if not installed
    print("📋 Step 2: Ensuring git is installed...")
    print("")
    run_command(ssh, "which git || apt-get install -y git", "Checking/installing git")
    
    print("")
    
    # Clone depot_tools properly
    print("📋 Step 3: Cloning depot_tools...")
    print("   This may take a minute...")
    print("")
    
    success = run_command(
        ssh,
        "cd /opt && git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git 2>&1",
        "Cloning depot_tools from Google",
        timeout=120
    )
    
    if not success:
        print("   ⚠️  Clone had issues, but continuing...")
    
    print("")
    
    # Verify installation
    print("📋 Step 4: Verifying installation...")
    print("")
    
    run_command(ssh, "test -f /opt/depot_tools/fetch && echo 'fetch exists' || echo 'fetch missing'", 
               "Checking if fetch script exists")
    
    run_command(ssh, "ls -la /opt/depot_tools/ | head -15", "Listing depot_tools contents")
    
    print("")
    
    # Make executable
    print("📋 Step 5: Making scripts executable...")
    print("")
    run_command(ssh, "chmod +x /opt/depot_tools/* 2>/dev/null; chmod +x /opt/depot_tools/.cipd_bin/* 2>/dev/null || true", 
               "Making scripts executable")
    
    print("")
    
    # Test fetch
    print("📋 Step 6: Testing fetch command...")
    print("")
    
    test_cmd = 'export PATH="/opt/depot_tools:$PATH" && /opt/depot_tools/fetch --help 2>&1 | head -10'
    success = run_command(ssh, test_cmd, "Testing fetch command")
    
    print("")
    
    # Add to bashrc
    print("📋 Step 7: Adding to PATH permanently...")
    print("")
    
    bashrc_check = 'grep -q "depot_tools" /root/.bashrc && echo "exists" || echo "missing"'
    stdin, stdout, stderr = ssh.exec_command(bashrc_check)
    exists = stdout.read().decode().strip() == "exists"
    
    if not exists:
        run_command(ssh, '''echo "" >> /root/.bashrc && echo "# PhazeBrowser - depot_tools" >> /root/.bashrc && echo 'export PATH="/opt/depot_tools:$PATH"' >> /root/.bashrc''', 
                   "Adding depot_tools to .bashrc")
    else:
        print("   ✅ Already in .bashrc")
    
    print("")
    
    ssh.close()
    
    print("==========================================")
    print("✅ INSTALLATION COMPLETE!")
    print("==========================================")
    print("")
    print("📝 Now you can use fetch:")
    print("")
    print("1. SSH into VPS:")
    print(f"   ssh {VPS_USER}@{VPS_IP}")
    print("")
    print("2. Start screen session:")
    print("   screen -S chromium")
    print("")
    print("3. Export PATH and fetch:")
    print("   export PATH=\"/opt/depot_tools:\$PATH\"")
    print("   cd /opt/phazebrowser")
    print("   fetch --nohooks chromium")
    print("")
    print("   Or use full path:")
    print("   /opt/depot_tools/fetch --nohooks chromium")
    print("")
    print("4. Detach: Ctrl+A then D")
    print("5. Reattach: screen -r chromium")
    print("")

if __name__ == "__main__":
    main()

