#!/usr/bin/env python3
"""
Setup Remote Desktop (RDP) access to the VPS using XRDP
"""

import paramiko
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("🖥️  SETTING UP REMOTE DESKTOP (RDP) ACCESS")
    print("=" * 70)
    print("")
    print("This will install XRDP so you can:")
    print("   ✅ Connect using Windows Remote Desktop")
    print("   ✅ Connect using Mac Remote Desktop")
    print("   ✅ Connect using Linux RDP clients")
    print("   ✅ Get full desktop GUI access")
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Check if XRDP is already installed
        print("1️⃣  Checking if XRDP is already installed...")
        success, check, _ = run_command(ssh, "which xrdp || systemctl status xrdp --no-pager | head -1 || echo 'NOT_INSTALLED'", check=False)
        if 'NOT_INSTALLED' not in check and ('xrdp' in check.lower() or 'active' in check.lower()):
            print("   ✅ XRDP appears to be installed")
            success, status, _ = run_command(ssh, "systemctl status xrdp --no-pager | head -5", check=False)
            print(status)
            print("")
            print("   Connection info:")
            print(f"   Host: {VPS_IP}")
            print("   Port: 3389 (default RDP port)")
            print(f"   Username: {VPS_USER}")
            print(f"   Password: {VPS_PASS}")
            return
        
        print("   ✅ XRDP not installed, proceeding...")
        print("")
        
        # Check if desktop environment is installed
        print("2️⃣  Checking for desktop environment...")
        success, desktop_check, _ = run_command(ssh, "dpkg -l | grep -E 'xfce|gnome|kde|lxde' | head -1 || echo 'NO_DESKTOP'", check=False)
        
        needs_desktop = 'NO_DESKTOP' in desktop_check
        
        if needs_desktop:
            print("   ⚠️  No desktop environment found")
            print("   Installing XFCE (lightweight desktop)...")
            print("")
            
            # Install XFCE
            install_commands = [
                "apt-get update -y",
                "DEBIAN_FRONTEND=noninteractive apt-get install -y xfce4 xfce4-goodies",
            ]
            
            for cmd in install_commands:
                print(f"   Running: {cmd.split()[0]}...")
                run_command(ssh, cmd, check=False)
                print("   ✅ Done")
        else:
            print("   ✅ Desktop environment found")
        
        print("")
        
        # Install XRDP
        print("3️⃣  Installing XRDP...")
        install_commands = [
            "apt-get update -y",
            "DEBIAN_FRONTEND=noninteractive apt-get install -y xrdp",
        ]
        
        for cmd in install_commands:
            print(f"   Running: {cmd.split()[0]}...")
            success, output, error = run_command(ssh, cmd, check=False)
            if success:
                print("   ✅ Done")
            else:
                print(f"   ⚠️  Warning: {error[:100]}")
        
        print("")
        
        # Configure XRDP to use XFCE
        if needs_desktop:
            print("4️⃣  Configuring XRDP to use XFCE...")
            xrdp_config = "xfce4-session\n"
            stdin, stdout, stderr = ssh.exec_command(f"echo '{xrdp_config}' > /etc/xrdp/startwm.sh")
            stdout.channel.recv_exit_status()
            
            # Also add to xrdp.ini
            run_command(ssh, "sed -i 's/use_vsyscall=.*/use_vsyscall=true/' /etc/xrdp/xrdp.ini", check=False)
            print("   ✅ Configured")
            print("")
        
        # Enable and start XRDP
        print("5️⃣  Starting XRDP service...")
        run_command(ssh, "systemctl enable xrdp", check=False)
        run_command(ssh, "systemctl restart xrdp", check=False)
        
        import time
        time.sleep(2)
        
        success, status, _ = run_command(ssh, "systemctl status xrdp --no-pager | head -5", check=False)
        print(status)
        print("")
        
        # Configure firewall to allow RDP (port 3389)
        print("6️⃣  Configuring firewall for RDP access...")
        
        # Check what firewall is being used
        success, ufw_status, _ = run_command(ssh, "which ufw && ufw status | head -1 || echo 'NO_UFW'", check=False)
        
        if 'NO_UFW' not in ufw_status:
            print("   Found UFW firewall, allowing RDP port...")
            run_command(ssh, "ufw allow 3389/tcp", check=False)
            run_command(ssh, "ufw reload", check=False)
            print("   ✅ Firewall configured")
        else:
            # Check for iptables
            success, iptables_check, _ = run_command(ssh, "which iptables && echo 'FOUND' || echo 'NO_IPTABLES'", check=False)
            if 'FOUND' in iptables_check:
                print("   Found iptables, adding RDP rule...")
                run_command(ssh, "iptables -A INPUT -p tcp --dport 3389 -j ACCEPT", check=False)
                print("   ✅ Firewall rule added")
            else:
                print("   ⚠️  No firewall detected (or using different firewall)")
        
        print("")
        
        # Get connection info
        print("=" * 70)
        print("✅ REMOTE DESKTOP SETUP COMPLETE!")
        print("=" * 70)
        print("")
        print("🖥️  Connection Information:")
        print(f"   Host/IP: {VPS_IP}")
        print("   Port: 3389")
        print(f"   Username: {VPS_USER}")
        print(f"   Password: {VPS_PASS}")
        print("")
        print("📱 How to Connect:")
        print("")
        print("   Windows:")
        print("   1. Press Win+R, type: mstsc")
        print("   2. Enter: " + VPS_IP)
        print("   3. Click Connect")
        print("   4. Enter username and password")
        print("")
        print("   Mac:")
        print("   1. Download Microsoft Remote Desktop from App Store")
        print("   2. Add new connection: " + VPS_IP + ":3389")
        print("   3. Enter username and password")
        print("")
        print("   Linux:")
        print("   1. Install: sudo apt-get install remmina remmina-plugin-rdp")
        print("   2. Open Remmina and create new RDP connection")
        print("   3. Enter: " + VPS_IP + ":3389")
        print("")
        print("⚠️  Troubleshooting:")
        print("   • If connection fails, check firewall allows port 3389")
        print("   • Make sure XRDP service is running: systemctl status xrdp")
        print("   • Restart XRDP: systemctl restart xrdp")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

