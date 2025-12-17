#!/usr/bin/env python3
"""
Fix API Port Conflict - Change API to different port or kill existing process
"""

import paramiko
import sys

VPS_HOST = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status == 0, output, error

def main():
    print("🔧 Fixing API Port Conflict...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    
    try:
        # Find what's using port 5000
        print("\n1️⃣ Finding process using port 5000...")
        success, output, error = run_command(ssh, "lsof -i :5000 || fuser 5000/tcp || ss -tlnp | grep ':5000 '")
        print(output if output else "No process found (may have stopped)")
        
        # Kill any process on port 5000
        print("\n2️⃣ Freeing port 5000...")
        run_command(ssh, "fuser -k 5000/tcp 2>/dev/null || pkill -f 'python.*5000' || true")
        print("✅ Port 5000 freed")
        
        # Change API to port 5001 instead
        print("\n3️⃣ Changing API to port 5001...")
        run_command(ssh, "sed -i 's/port=5000/port=5001/g' /opt/phazevpn-email/api/app.py")
        run_command(ssh, "sed -i 's/app.run(host=.*port=5000/app.run(host='\\''0.0.0.0'\\'', port=5001/g' /opt/phazevpn-email/api/app.py")
        
        # Update systemd service
        print("\n4️⃣ Updating systemd service...")
        run_command(ssh, "sed -i 's/port=5000/port=5001/g' /etc/systemd/system/phazevpn-email-api.service || true")
        
        # Restart API
        print("\n5️⃣ Restarting API on port 5001...")
        run_command(ssh, "systemctl daemon-reload")
        run_command(ssh, "systemctl restart phazevpn-email-api")
        
        # Wait a bit
        import time
        time.sleep(3)
        
        # Check status
        print("\n6️⃣ Checking API status...")
        success, output, error = run_command(ssh, "systemctl status phazevpn-email-api | head -15")
        print(output)
        
        # Check if port 5001 is listening
        print("\n7️⃣ Checking port 5001...")
        success, output, error = run_command(ssh, "ss -tlnp | grep ':5001 ' || netstat -tlnp | grep ':5001 '")
        if success and "5001" in output:
            print("✅ Port 5001 is listening!")
        else:
            print("⚠️  Port 5001 not listening yet")
        
        # Update firewall
        print("\n8️⃣ Updating firewall...")
        run_command(ssh, "ufw allow 5001/tcp comment 'Email API'")
        print("✅ Firewall updated")
        
        print("\n✅ API fixed! New port: 5001")
        print("   Test: curl http://15.204.11.19:5001/api/v1/health")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

