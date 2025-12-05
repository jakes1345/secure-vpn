#!/usr/bin/env python3
"""
Diagnose and fix VPS network/DNS issues
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
    """Run a command and return output"""
    print(f"🔧 {description}...")
    try:
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        print(f"   Output:")
        for line in output.split('\n')[:10]:
            if line.strip():
                print(f"   {line}")
        
        if error:
            print(f"   Errors:")
            for line in error.split('\n')[:5]:
                if line.strip():
                    print(f"   {line}")
        
        return exit_status == 0, output
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, str(e)

def main():
    print("==========================================")
    print("🔍 DIAGNOSING VPS NETWORK/DNS")
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
    
    # Check network interfaces
    print("📋 Step 1: Checking network interfaces...")
    print("")
    run_command(ssh, "ip addr show | grep -E '^[0-9]+:|inet '", "Network interfaces")
    
    print("")
    
    # Check DNS config
    print("📋 Step 2: Checking DNS configuration...")
    print("")
    run_command(ssh, "cat /etc/resolv.conf", "Current DNS config")
    run_command(ssh, "cat /etc/systemd/resolved.conf | grep -v '^#' | grep -v '^$'", "systemd-resolved config")
    
    print("")
    
    # Check if DNS service is running
    print("📋 Step 3: Checking DNS services...")
    print("")
    run_command(ssh, "systemctl status systemd-resolved 2>&1 | head -10", "systemd-resolved status")
    
    print("")
    
    # Try to fix DNS
    print("📋 Step 4: Attempting DNS fix...")
    print("")
    
    # Fix resolv.conf
    dns_fix = """cat > /etc/resolv.conf << 'EOF'
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
EOF"""
    run_command(ssh, dns_fix, "Setting DNS in resolv.conf")
    
    # Fix systemd-resolved
    run_command(ssh, "sed -i 's/#DNS=/DNS=8.8.8.8 8.8.4.4 1.1.1.1/' /etc/systemd/resolved.conf 2>/dev/null || echo 'DNS=8.8.8.8 8.8.4.4 1.1.1.1' >> /etc/systemd/resolved.conf", 
               "Setting DNS in systemd-resolved")
    
    # Restart service
    run_command(ssh, "systemctl restart systemd-resolved 2>/dev/null || true", "Restarting DNS service")
    
    print("")
    
    # Test DNS
    print("📋 Step 5: Testing DNS...")
    print("")
    run_command(ssh, "ping -c 2 -W 3 8.8.8.8", "Testing connectivity to 8.8.8.8")
    run_command(ssh, "nslookup google.com 8.8.8.8 2>&1 | head -5", "Testing DNS lookup")
    run_command(ssh, "getent hosts google.com", "Testing getent")
    
    print("")
    
    # Check routing
    print("📋 Step 6: Checking routing...")
    print("")
    run_command(ssh, "ip route show", "Routing table")
    
    print("")
    
    ssh.close()
    
    print("==========================================")
    print("✅ DIAGNOSIS COMPLETE")
    print("==========================================")
    print("")
    print("📝 If DNS still doesn't work:")
    print("")
    print("Option 1: Download depot_tools on your PC and upload:")
    print("   # On your PC:")
    print("   cd ~")
    print("   git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git")
    print("   scp -r depot_tools root@15.204.11.19:/opt/")
    print("")
    print("   # On VPS:")
    print("   chmod +x /opt/depot_tools/*")
    print("")
    print("Option 2: Use VPN's DNS if VPN is running")
    print("   # Check VPN DNS")
    print("   cat /etc/openvpn/server.conf | grep push.*dns")
    print("")
    print("")

if __name__ == "__main__":
    main()

