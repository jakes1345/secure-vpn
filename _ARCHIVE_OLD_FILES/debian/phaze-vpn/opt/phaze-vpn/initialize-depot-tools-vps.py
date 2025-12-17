#!/usr/bin/env python3
"""
Initialize depot_tools on VPS
Fixes the "need to initialize depot_tools" error
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

def run_command(ssh, command, description="", timeout=300, show_output=True):
    """Run a command and return output"""
    if description and show_output:
        print(f"🔧 {description}...")
        print("")
    
    try:
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True, timeout=timeout)
        
        output_lines = []
        for line in iter(stdout.readline, ""):
            if line:
                line = line.rstrip()
                if show_output:
                    print(f"   {line}")
                output_lines.append(line)
        
        error_lines = []
        for line in iter(stderr.readline, ""):
            if line:
                line = line.rstrip()
                if line and "WARNING" not in line.upper() and "INFO" not in line.upper():
                    if show_output:
                        print(f"   ⚠️  {line}")
                    error_lines.append(line)
        
        exit_status = stdout.channel.recv_exit_status()
        return exit_status == 0, "\n".join(output_lines)
            
    except Exception as e:
        if show_output:
            print(f"   ❌ Error: {e}")
        return False, str(e)

def main():
    print("=" * 60)
    print("🔧 INITIALIZING depot_tools ON VPS")
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
    
    # Initialize depot_tools
    print("📦 Initializing depot_tools...")
    print("   This sets up the Python environment and tools")
    print("")
    
    # Method 1: Run gclient to initialize
    print("Method 1: Running gclient (should auto-initialize)...")
    success, output = run_command(
        ssh,
        'export PATH="$PATH:/opt/depot_tools" && cd /opt/phazebrowser/src && gclient --version',
        "Testing gclient",
        timeout=60
    )
    
    if not success or "python3_bin_reldir.txt" in output:
        print("")
        print("Method 2: Running ensure_bootstrap...")
        success2, output2 = run_command(
            ssh,
            'export PATH="$PATH:/opt/depot_tools" && /opt/depot_tools/ensure_bootstrap',
            "Running ensure_bootstrap",
            timeout=180
        )
    
    # Verify initialization
    print("")
    print("🧪 Verifying depot_tools is initialized...")
    success, output = run_command(
        ssh,
        'export PATH="$PATH:/opt/depot_tools" && test -f /opt/depot_tools/python3_bin_reldir.txt && echo "initialized" || echo "not initialized"',
        "Checking initialization status",
        timeout=10
    )
    
    if "initialized" in output:
        print("")
        print("✅ depot_tools is initialized!")
        print("")
        print("🧪 Testing gn command...")
        success, output = run_command(
            ssh,
            'export PATH="$PATH:/opt/depot_tools" && gn --version',
            "Testing gn command",
            timeout=30
        )
        
        if success:
            print("")
            print("=" * 60)
            print("✅ depot_tools FULLY INITIALIZED AND WORKING!")
            print("=" * 60)
            print("")
            print("📝 You can now run:")
            print("   cd /opt/phazebrowser/src")
            print("   export PATH=\"$PATH:/opt/depot_tools\"")
            print("   gn gen out/Default --args='is_debug=false'")
            print("")
        else:
            print("")
            print("⚠️  gn command still not working")
            print("   May need to run: cd /opt/phazebrowser/src && gclient sync")
    else:
        print("")
        print("⚠️  depot_tools may still need initialization")
        print("")
        print("Try running this manually:")
        print("   ssh root@15.204.11.19")
        print("   export PATH=\"$PATH:/opt/depot_tools\"")
        print("   cd /opt/phazebrowser/src")
        print("   gclient sync")
        print("")
    
    ssh.close()

if __name__ == "__main__":
    main()

