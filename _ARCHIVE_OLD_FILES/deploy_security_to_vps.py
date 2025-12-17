#!/usr/bin/env python3
"""
Deploy All Security Features to VPS
Runs all setup scripts and configures everything
"""

import sys
from pathlib import Path

try:
    import paramiko
except ImportError:
    print("❌ Error: paramiko not installed")
    print("   Install with: pip3 install paramiko")
    sys.exit(1)

# VPS Configuration
VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_PATH = "/opt/secure-vpn"

def run_command(ssh, command, description):
    """Run a command on VPS and show output"""
    print(f"🔧 {description}...", end=" ", flush=True)
    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("✓")
            output = stdout.read().decode()
            if output.strip():
                print(f"   {output.strip()}")
            return True
        else:
            error = stderr.read().decode()
            print(f"✗ Error: {error}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("==========================================")
    print("🚀 DEPLOYING SECURITY TO VPS")
    print("==========================================")
    print("")
    print(f"VPS: {VPS_USER}@{VPS_IP}")
    print(f"Path: {VPS_PATH}")
    print("")
    
    # Connect to VPS
    print("🔌 Connecting to VPS...", end=" ", flush=True)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("✓")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
    
    print("")
    print("📋 Deployment Steps:")
    print("")
    
    # Step 1: Setup DDoS Protection
    print("[1/4] Setting up DDoS protection...")
    run_command(ssh, f"cd {VPS_PATH} && sudo ./scripts/setup-ddos-protection.sh", 
                "Running DDoS protection setup")
    
    # Step 2: Setup Privacy Enhancements
    print("")
    print("[2/4] Setting up privacy enhancements...")
    run_command(ssh, f"cd {VPS_PATH} && sudo ./scripts/enhance-privacy.sh", 
                "Running privacy enhancement setup")
    
    # Step 3: Verify OpenVPN service
    print("")
    print("[3/4] Checking OpenVPN service...")
    # Find OpenVPN service name
    stdin, stdout, stderr = ssh.exec_command("systemctl list-units | grep -i openvpn | head -1 | awk '{print $1}'")
    service_name = stdout.read().decode().strip()
    
    if service_name:
        print(f"   Found service: {service_name}")
        run_command(ssh, f"sudo systemctl restart {service_name}", 
                    f"Restarting {service_name}")
        run_command(ssh, f"sudo systemctl status {service_name} --no-pager -l | head -10", 
                    "Checking service status")
    else:
        print("   ⚠️  OpenVPN service not found")
        print("   You may need to restart manually:")
        print("   sudo systemctl restart openvpn@server")
        print("   # OR")
        print("   sudo systemctl restart secure-vpn")
    
    # Step 4: Verify security scripts
    print("")
    print("[4/4] Verifying security scripts...")
    run_command(ssh, f"ls -la {VPS_PATH}/scripts/*.sh | head -10", 
                "Checking script permissions")
    
    # Check if scripts are referenced in server config
    stdin, stdout, stderr = ssh.exec_command(f"grep 'up-ultimate-security' {VPS_PATH}/config/server.conf")
    if stdout.read().decode().strip():
        print("   ✓ Security scripts configured in server.conf")
    else:
        print("   ⚠️  Security scripts not found in server.conf")
        print("   You may need to update server.conf manually")
    
    # Close connection
    ssh.close()
    
    print("")
    print("==========================================")
    print("✅ DEPLOYMENT COMPLETE!")
    print("==========================================")
    print("")
    print("📝 Next Steps:")
    print("")
    print("1. Test VPN connection:")
    print("   - Connect from a client")
    print("   - Verify kill switch works")
    print("   - Test DNS leak protection")
    print("   - Test WebRTC through VPN")
    print("   - Test IPv6 through VPN")
    print("")
    print("2. Monitor security:")
    print(f"   ssh {VPS_USER}@{VPS_IP}")
    print(f"   cd {VPS_PATH}")
    print("   ./scripts/monitor-ddos.sh")
    print("")
    print("3. Check logs:")
    print(f"   tail -f {VPS_PATH}/logs/security.log")
    print("")
    print("==========================================")

if __name__ == "__main__":
    main()

