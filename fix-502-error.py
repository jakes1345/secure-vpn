#!/usr/bin/env python3
"""
Fix 502 Bad Gateway Error
Nginx is running but can't reach backend service on port 8081
"""

import paramiko
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
    print("🔧 FIXING 502 BAD GATEWAY ERROR")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Step 1: Check if port 8081 is listening
        print("1️⃣ Checking if web portal is running on port 8081...")
        success, output, _ = run_command(ssh, "netstat -tuln | grep :8081 || ss -tuln | grep :8081", check=False)
        if success and output:
            print(f"   ✅ Port 8081 is listening: {output}")
        else:
            print("   ❌ Port 8081 is NOT listening - web portal is down!")
        print("")
        
        # Step 2: Check web portal service
        print("2️⃣ Checking web portal service...")
        success, output, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -10", check=False)
        print(output)
        print("")
        
        # Step 3: Check if web portal process exists
        print("3️⃣ Checking for web portal process...")
        success, output, _ = run_command(ssh, "ps aux | grep -E 'app.py|web-portal|8081' | grep -v grep", check=False)
        if output:
            print(f"   Found processes: {output[:200]}")
        else:
            print("   ❌ No web portal process found")
        print("")
        
        # Step 4: Check if web portal files exist
        print("4️⃣ Checking web portal files...")
        success, output, _ = run_command(ssh, f"ls -la {VPN_DIR}/web-portal/app.py 2>&1", check=False)
        if success:
            print(f"   ✅ Web portal file exists: {VPN_DIR}/web-portal/app.py")
        else:
            print(f"   ❌ Web portal file NOT found: {output}")
        print("")
        
        # Step 5: Try to start web portal
        print("5️⃣ Starting web portal service...")
        
        # Check if service file exists
        success, _, _ = run_command(ssh, "test -f /etc/systemd/system/secure-vpn-download.service", check=False)
        if not success:
            print("   Creating web portal service...")
            service_file = f"""
[Unit]
Description=PhazeVPN Web Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={VPN_DIR}/web-portal
ExecStart=/usr/bin/python3 {VPN_DIR}/web-portal/app.py
Restart=always
RestartSec=10
Environment="PORT=8081"

[Install]
WantedBy=multi-user.target
"""
            stdin, stdout, stderr = ssh.exec_command(f"cat > /etc/systemd/system/secure-vpn-download.service << 'SERVICEEOF'\n{service_file}\nSERVICEEOF")
            stdout.channel.recv_exit_status()
            run_command(ssh, "systemctl daemon-reload", check=False)
            print("   ✅ Service file created")
        
        # Start the service
        success, output, error = run_command(ssh, "systemctl start secure-vpn-download", check=False)
        if success:
            print("   ✅ Service started")
        else:
            print(f"   ⚠️  Start attempt: {error}")
        
        # Check status
        success, output, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -5", check=False)
        print(output)
        print("")
        
        # Step 6: If service won't start, try running directly
        print("6️⃣ Testing web portal directly...")
        success, output, _ = run_command(ssh, f"cd {VPN_DIR}/web-portal && timeout 2 python3 app.py 2>&1 | head -10 || true", check=False)
        if output:
            print(f"   Output: {output[:300]}")
        print("")
        
        # Step 7: Check Nginx config
        print("7️⃣ Checking Nginx configuration...")
        success, output, _ = run_command(ssh, "grep -A 5 'proxy_pass' /etc/nginx/sites-available/phazevpn", check=False)
        if output:
            print("   Current Nginx proxy config:")
            print(f"   {output}")
        print("")
        
        # Step 8: Check if we can reach localhost:8081
        print("8️⃣ Testing connection to localhost:8081...")
        success, output, _ = run_command(ssh, "curl -I http://localhost:8081 2>&1 | head -5", check=False)
        if success and "200" in output:
            print("   ✅ localhost:8081 is responding!")
        else:
            print(f"   ❌ localhost:8081 not responding: {output[:200]}")
        print("")
        
        # Step 9: Final restart
        print("9️⃣ Restarting services...")
        run_command(ssh, "systemctl restart secure-vpn-download", check=False)
        run_command(ssh, "systemctl restart nginx", check=False)
        sleep(2)
        
        # Final check
        success, output, _ = run_command(ssh, "netstat -tuln | grep :8081 || ss -tuln | grep :8081", check=False)
        if success and output:
            print(f"   ✅ Port 8081 is now listening: {output}")
        else:
            print("   ⚠️  Port 8081 still not listening")
        
        print("")
        print("=" * 70)
        print("✅ DIAGNOSIS COMPLETE")
        print("=" * 70)
        print("")
        print("Check the output above to see what's wrong.")
        print("")
        print("If port 8081 is not listening:")
        print("  - Web portal service might not be installed")
        print("  - Or web portal code might have errors")
        print("")
        print("Try accessing: http://localhost:8081 (from VPS)")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

