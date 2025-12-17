#!/usr/bin/env python3
"""
Install depot_tools on VPS for PhazeBrowser development
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

def run_command(ssh, command, description="", timeout=300):
    """Run a command and show output"""
    if description:
        print(f"🔧 {description}...")
        print("")
    
    try:
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True, timeout=timeout)
        
        output_lines = []
        for line in iter(stdout.readline, ""):
            if line:
                line = line.rstrip()
                print(f"   {line}")
                output_lines.append(line)
        
        exit_status = stdout.channel.recv_exit_status()
        return exit_status == 0, "\n".join(output_lines)
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, str(e)

def main():
    print("=" * 60)
    print("🔧 INSTALLING depot_tools ON VPS")
    print("=" * 60)
    print("")
    
    # Connect
    print("🔌 Connecting to VPS...", end=" ", flush=True)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("✅ Connected!")
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)
    
    print("")
    
    # Check if already installed
    success, output = run_command(ssh, "test -d /opt/depot_tools && echo 'exists' || echo 'missing'", "Checking if depot_tools already installed", timeout=10)
    
    if "exists" in output:
        print("")
        print("✅ depot_tools already installed!")
        print("")
        
        # Check PATH
        success, path_output = run_command(ssh, 'echo $PATH | grep depot_tools && echo "in PATH" || echo "not in PATH"', "Checking PATH", timeout=10)
        
        if "not in PATH" in path_output:
            print("")
            print("📝 Adding to PATH...")
            run_command(ssh, '''echo 'export PATH="$PATH:/opt/depot_tools"' >> /root/.bashrc''', "Adding to .bashrc", timeout=10)
            print("✅ Added to PATH!")
        
        # Test fetch command
        print("")
        print("🧪 Testing fetch command...")
        success, test_output = run_command(ssh, 'export PATH="$PATH:/opt/depot_tools" && which fetch', "Testing fetch", timeout=10)
        
        if success and "/opt/depot_tools" in test_output:
            print("✅ depot_tools is working!")
        else:
            print("⚠️  fetch command not found, but directory exists")
        
        ssh.close()
        return
    
    # Install depot_tools
    print("📦 Installing depot_tools...")
    print("")
    
    commands = [
        ("cd /opt", "Navigating to /opt"),
        ("git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git", "Cloning depot_tools"),
        ("chmod -R 755 /opt/depot_tools", "Setting permissions"),
        ('''echo 'export PATH="$PATH:/opt/depot_tools"' >> /root/.bashrc''', "Adding to PATH"),
        ('export PATH="$PATH:/opt/depot_tools" && which fetch', "Verifying installation")
    ]
    
    for cmd, desc in commands:
        success, output = run_command(ssh, cmd, desc, timeout=180)
        if not success and "clone" not in cmd.lower():  # Clone might show warnings
            print(f"⚠️  Warning: {desc} may have had issues")
        print("")
    
    # Final verification
    print("=" * 60)
    print("✅ VERIFICATION")
    print("=" * 60)
    print("")
    
    success, output = run_command(ssh, 'export PATH="$PATH:/opt/depot_tools" && fetch --version 2>&1 | head -3', "Testing depot_tools", timeout=10)
    
    if success:
        print("")
        print("=" * 60)
        print("✅ depot_tools INSTALLED SUCCESSFULLY!")
        print("=" * 60)
        print("")
        print("📝 Next steps:")
        print("   cd /opt/phazebrowser/src")
        print("   export PATH=\"$PATH:/opt/depot_tools\"")
        print("   git apply ../patches/*.patch")
        print("   gn gen out/Default --args='is_debug=false'")
        print("   autoninja -C out/Default chrome")
        print("")
    else:
        print("")
        print("⚠️  Installation completed but verification had issues")
        print("   You may need to add depot_tools to PATH manually")
    
    ssh.close()

if __name__ == "__main__":
    main()

