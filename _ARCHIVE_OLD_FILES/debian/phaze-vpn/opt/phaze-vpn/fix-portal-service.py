#!/usr/bin/env python3
"""
Fix Portal Service - Ensure it starts properly
"""

import paramiko
import sys
import time

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, check=True):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    if check and exit_status != 0:
        print(f"❌ Error: {error}")
        return False, output, error
    return True, output, error

def main():
    print("🔧 Fixing Portal Service...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # Check if portal directory exists
        print("\n1️⃣ Checking portal files...")
        success, output, error = run_command(
            ssh,
            "ls -la /opt/phazevpn-portal/",
            check=False
        )
        print(output)
        
        # Check if app.py exists
        success, output, error = run_command(
            ssh,
            "test -f /opt/phazevpn-portal/app.py && echo 'EXISTS' || echo 'MISSING'",
            check=False
        )
        print(f"   app.py: {output.strip()}")
        
        # Install dependencies if needed
        print("\n2️⃣ Installing Python dependencies...")
        run_command(ssh, "pip3 install flask flask-cors requests gunicorn", check=False)
        
        # Create proper systemd service
        print("\n3️⃣ Creating systemd service...")
        service_content = """[Unit]
Description=PhazeVPN Unified Web Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/phazevpn-portal
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /opt/phazevpn-portal/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"""
        
        sftp = ssh.open_sftp()
        f = sftp.file('/etc/systemd/system/phazevpn-portal.service', 'w')
        f.write(service_content)
        f.close()
        sftp.close()
        
        # Make app.py executable
        run_command(ssh, "chmod +x /opt/phazevpn-portal/app.py", check=False)
        
        # Reload systemd
        run_command(ssh, "systemctl daemon-reload")
        
        # Stop and start service
        print("\n4️⃣ Restarting service...")
        run_command(ssh, "systemctl stop phazevpn-portal", check=False)
        time.sleep(2)
        run_command(ssh, "systemctl start phazevpn-portal")
        run_command(ssh, "systemctl enable phazevpn-portal")
        
        # Wait for service to start
        print("\n5️⃣ Waiting for service to start...")
        time.sleep(5)
        
        # Check status
        print("\n6️⃣ Checking service status...")
        success, output, error = run_command(
            ssh,
            "systemctl status phazevpn-portal --no-pager | head -20",
            check=False
        )
        print(output)
        
        # Check logs
        print("\n7️⃣ Checking service logs...")
        success, output, error = run_command(
            ssh,
            "journalctl -u phazevpn-portal -n 20 --no-pager",
            check=False
        )
        print(output)
        
        # Test if it's listening
        print("\n8️⃣ Testing if service is listening...")
        success, output, error = run_command(
            ssh,
            "ss -tlnp | grep ':8080' || netstat -tlnp | grep ':8080'",
            check=False
        )
        if "8080" in output:
            print(f"   ✅ Service is listening on port 8080")
        else:
            print(f"   ⚠️  Service not listening yet")
        
        # Test HTTP response
        print("\n9️⃣ Testing HTTP response...")
        success, output, error = run_command(
            ssh,
            "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/ || echo 'FAILED'",
            check=False
        )
        print(f"   HTTP Status: {output.strip()}")
        
        print("\n✅ Portal Service Fixed!")
        print("\n🌐 Access URLs:")
        print("   - http://phazevpn.duckdns.org")
        print("   - http://15.204.11.19")
        print("   - http://15.204.11.19:8080")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
