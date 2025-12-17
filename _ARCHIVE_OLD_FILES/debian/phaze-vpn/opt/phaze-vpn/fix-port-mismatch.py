#!/usr/bin/env python3
"""
Fix Port Mismatch: Web portal is on 5000, Nginx expects 8081
"""

import paramiko
import time
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

def run_command(ssh, command, check=True):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("🔧 FIXING PORT MISMATCH (5000 → 8081)")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Step 1: Update service file to use PORT=8081
        print("1️⃣ Updating web portal service to use port 8081...")
        service_file = f"""[Unit]
Description=PhazeVPN Web Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={VPN_DIR}/web-portal
Environment="PORT=8081"
ExecStart=/usr/bin/python3 {VPN_DIR}/web-portal/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target"""
        
        stdin, stdout, stderr = ssh.exec_command(f"cat > /etc/systemd/system/secure-vpn-download.service << 'SERVICEEOF'\n{service_file}\nSERVICEEOF")
        stdout.channel.recv_exit_status()
        print("   ✅ Service file updated")
        print("")
        
        # Step 2: Reload systemd
        print("2️⃣ Reloading systemd daemon...")
        run_command(ssh, "systemctl daemon-reload")
        print("   ✅ Daemon reloaded")
        print("")
        
        # Step 3: Stop any existing processes on port 5000
        print("3️⃣ Stopping old web portal processes...")
        run_command(ssh, "pkill -f 'app.py' || true", check=False)
        time.sleep(2)
        print("   ✅ Old processes stopped")
        print("")
        
        # Step 4: Start the service
        print("4️⃣ Starting web portal service on port 8081...")
        success, output, error = run_command(ssh, "systemctl restart secure-vpn-download", check=False)
        if success:
            print("   ✅ Service restarted")
        else:
            print(f"   ⚠️  Warning: {error}")
        print("")
        
        # Step 5: Wait a moment for service to start
        print("5️⃣ Waiting for service to start...")
        time.sleep(3)
        
        # Step 6: Check if port 8081 is now listening
        print("6️⃣ Checking if port 8081 is listening...")
        success, output, _ = run_command(ssh, "netstat -tuln | grep :8081 || ss -tuln | grep :8081", check=False)
        if success and output:
            print(f"   ✅ Port 8081 is listening: {output}")
        else:
            print("   ❌ Port 8081 still not listening")
            print("   Checking service status...")
            success, output, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -15", check=False)
            print(output)
        print("")
        
        # Step 7: Test connection
        print("7️⃣ Testing connection to localhost:8081...")
        time.sleep(2)
        success, output, _ = run_command(ssh, "curl -I http://localhost:8081 2>&1 | head -5", check=False)
        if success and ("200" in output or "302" in output or "301" in output):
            print("   ✅ localhost:8081 is responding!")
        else:
            print(f"   Output: {output[:300]}")
        print("")
        
        # Step 8: Restart Nginx
        print("8️⃣ Restarting Nginx...")
        run_command(ssh, "systemctl restart nginx", check=False)
        print("   ✅ Nginx restarted")
        print("")
        
        # Step 9: Final status check
        print("9️⃣ Final status check...")
        success, output, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -10", check=False)
        print(output)
        print("")
        
        print("=" * 70)
        print("✅ PORT FIX COMPLETE")
        print("=" * 70)
        print("")
        print("The web portal should now be running on port 8081.")
        print("Try accessing: https://phazevpn.com")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

