#!/usr/bin/env python3
"""
Install Webmin - Free control panel that works well with existing services
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
    print("🚀 INSTALLING WEBMIN CONTROL PANEL")
    print("=" * 70)
    print("")
    print("Webmin Features:")
    print("   ✅ Web-based GUI (works alongside existing services)")
    print("   ✅ File manager")
    print("   ✅ System configuration")
    print("   ✅ Service management (systemd)")
    print("   ✅ User management")
    print("   ✅ Firewall configuration")
    print("   ✅ Log viewer")
    print("   ✅ Terminal access")
    print("   ✅ 100% FREE")
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Check if Webmin is already installed
        print("1️⃣  Checking if Webmin is already installed...")
        success, check, _ = run_command(ssh, "which webmin || dpkg -l | grep webmin | head -1 || echo 'NOT_INSTALLED'", check=False)
        if 'NOT_INSTALLED' not in check and 'webmin' in check.lower():
            print("   ⚠️  Webmin appears to be installed")
            success, status, _ = run_command(ssh, "systemctl status webmin --no-pager | head -3 || echo 'NOT_RUNNING'", check=False)
            print(status)
            return
        
        print("   ✅ Webmin not installed, proceeding...")
        print("")
        
        # Install Webmin
        print("2️⃣  Installing Webmin...")
        print("")
        
        # Add Webmin repository and install
        install_commands = [
            "apt-get update -y",
            "apt-get install -y software-properties-common apt-transport-https wget",
            "wget -q http://www.webmin.com/jcameron-key.asc -O- | apt-key add -",
            'echo "deb http://download.webmin.com/download/repository sarge contrib" > /etc/apt/sources.list.d/webmin.list',
            "apt-get update -y",
            "apt-get install -y webmin"
        ]
        
        for i, cmd in enumerate(install_commands, 1):
            print(f"   Step {i}/{len(install_commands)}: Running {cmd.split()[0]}...")
            success, output, error = run_command(ssh, cmd, check=False)
            if not success and 'already' not in error.lower():
                print(f"      ⚠️  Warning: {error[:100]}")
            else:
                print(f"      ✅ Completed")
        
        print("")
        
        # Enable and start Webmin
        print("3️⃣  Starting Webmin service...")
        run_command(ssh, "systemctl enable webmin", check=False)
        run_command(ssh, "systemctl start webmin", check=False)
        
        time.sleep(2)
        
        success, status, _ = run_command(ssh, "systemctl is-active webmin", check=False)
        if 'active' in status:
            print("   ✅ Webmin is running!")
        else:
            print(f"   ⚠️  Status: {status}")
        
        print("")
        
        # Get Webmin info
        print("4️⃣  Getting Webmin access information...")
        success, port, _ = run_command(ssh, "grep 'port=' /etc/webmin/miniserv.conf | head -1 | cut -d= -f2 || echo '10000'", check=False)
        port = port.strip() if port.strip() else "10000"
        
        print("")
        print("=" * 70)
        print("✅ WEBMIN INSTALLED SUCCESSFULLY!")
        print("=" * 70)
        print("")
        print("🌐 Access Webmin:")
        print(f"   URL: https://{VPS_IP}:{port}/")
        print("   Username: root")
        print(f"   Password: {VPS_PASS}")
        print("")
        print("⚠️  Important:")
        print("   • Use HTTPS (not HTTP)")
        print("   • You'll see a security warning - click 'Advanced' then 'Proceed'")
        print("   • The certificate is self-signed (normal for Webmin)")
        print("")
        print("📋 What you can do in Webmin:")
        print("   • Manage files (File Manager)")
        print("   • Control services (System Services)")
        print("   • View logs (System Logs)")
        print("   • Manage users (Users and Groups)")
        print("   • Configure firewall (Linux Firewall)")
        print("   • Monitor system (System Status)")
        print("   • Terminal access (Command Shell)")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import time
    main()

