#!/usr/bin/env python3
"""
Fix Port Final - Update app.py default and systemd service
"""

from paramiko import SSHClient, AutoAddPolicy
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 70)
print("🔧 FIXING PORT FINAL - Using 5000 everywhere")
print("=" * 70)
print()

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected")
    print()
    
    # Upload fixed app.py
    print("1️⃣ Uploading fixed app.py...")
    sftp = ssh.open_sftp()
    local_app = "/opt/phaze-vpn/web-portal/app.py"
    remote_app = "/opt/secure-vpn/web-portal/app.py"
    sftp.put(local_app, remote_app)
    sftp.close()
    print("   ✅ app.py uploaded (default port 5000)")
    print()
    
    # Update systemd service to set PORT env var
    print("2️⃣ Updating systemd service...")
    service_content = f"""[Unit]
Description=PhazeVPN Web Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/secure-vpn/web-portal
Environment="PORT=5000"
Environment="FLASK_ENV=production"
ExecStart=/usr/bin/python3 /opt/secure-vpn/web-portal/app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    stdin, stdout, stderr = ssh.exec_command(
        f'cat > /etc/systemd/system/phazevpn-web.service << "EOF"\n{service_content}\nEOF'
    )
    stdout.channel.recv_exit_status()
    print("   ✅ Systemd service updated")
    print()
    
    # Reload and restart
    print("3️⃣ Restarting service...")
    ssh.exec_command("systemctl daemon-reload")
    ssh.exec_command("systemctl stop phazevpn-web")
    time.sleep(2)
    ssh.exec_command("pkill -f 'app.py'")
    time.sleep(1)
    ssh.exec_command("systemctl start phazevpn-web")
    time.sleep(5)
    print("   ✅ Service restarted")
    print()
    
    # Verify
    print("4️⃣ Verifying...")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1")
    status = stdout.read().decode().strip()
    print(f"   Service status: {status}")
    
    stdin, stdout, stderr = ssh.exec_command("netstat -tuln 2>/dev/null | grep :5000 || ss -tulpn 2>/dev/null | grep :5000")
    port_check = stdout.read().decode()
    if port_check:
        print(f"   ✅ Port 5000 listening")
    else:
        print(f"   ⚠️  Port 5000 not listening")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/ 2>&1")
    http_code = stdout.read().decode().strip()
    print(f"   HTTP status: {http_code}")
    
    # Check logs if failed
    if status != "active":
        stdin, stdout, stderr = ssh.exec_command("journalctl -u phazevpn-web --no-pager -n 10 2>&1")
        logs = stdout.read().decode()
        print(f"   Logs: {logs[-300:]}")
    
    print()
    print("=" * 70)
    print("✅ PORT FIXED - Using 5000 everywhere")
    print("=" * 70)
    print()
    print("📌 Configuration:")
    print("   ✅ app.py: default port 5000")
    print("   ✅ Systemd: PORT=5000 environment variable")
    print("   ✅ Nginx: proxy_pass to port 5000")
    print()
    print("🌐 Site: https://phazevpn.duckdns.org")
    print()
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

