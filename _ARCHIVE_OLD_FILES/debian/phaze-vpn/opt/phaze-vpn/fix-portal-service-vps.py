#!/usr/bin/env python3
"""Fix portal service on VPS - fix log permissions and port conflict"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS)

print("🔧 Fixing portal service...")

# Check what's using port 5000
print("1️⃣  Checking port 5000...")
stdin, stdout, stderr = ssh.exec_command('lsof -i :5000 || ss -tlnp | grep 5000')
port_info = stdout.read().decode()
print(port_info)

# Stop old process if needed
print("2️⃣  Stopping conflicting services...")
ssh.exec_command('pkill -f "python.*app.py" || true')
ssh.exec_command('systemctl stop phazevpn-portal || true')

# Fix log directory permissions
print("3️⃣  Fixing log permissions...")
ssh.exec_command('touch /var/log/phazevpn-portal-access.log /var/log/phazevpn-portal-error.log')
ssh.exec_command('chown www-data:www-data /var/log/phazevpn-portal-*.log')
ssh.exec_command('chmod 644 /var/log/phazevpn-portal-*.log')

# Update service to use journald instead of files (more reliable)
print("4️⃣  Updating service file...")
service_content = """[Unit]
Description=PhazeVPN Web Portal (Gunicorn)
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/phazevpn/web-portal
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="VPN_SERVER_IP=phazevpn.duckdns.org"
Environment="VPN_SERVER_PORT=1194"
Environment="HTTPS_ENABLED=true"
ExecStart=/usr/local/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 --timeout 120 app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/systemd/system/phazevpn-portal.service << "EOFSERVICE"\n{service_content}\nEOFSERVICE\n')
stdout.channel.recv_exit_status()

# Reload and start
print("5️⃣  Reloading and starting service...")
ssh.exec_command('systemctl daemon-reload')
ssh.exec_command('systemctl restart phazevpn-portal')
time.sleep(3)

# Check status
print("6️⃣  Checking status...")
stdin, stdout, stderr = ssh.exec_command('systemctl status phazevpn-portal --no-pager -l | head -20')
status = stdout.read().decode()
print(status)

ssh.close()
print("✅ Fix complete!")

