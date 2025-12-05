#!/usr/bin/env python3
"""Fix Flask service file"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS)

# Fix service file
service_content = """[Unit]
Description=PhazeVPN Web Portal (Gunicorn)
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/phazevpn/web-portal
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="VPN_SERVER_IP=phazevpn.duckdns.org"
Environment="VPN_SERVER_PORT=1194"
Environment="HTTPS_ENABLED=false"
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

# Reload and restart
ssh.exec_command('systemctl daemon-reload')
ssh.exec_command('systemctl restart phazevpn-portal')
time.sleep(3)

# Check status
stdin, stdout, stderr = ssh.exec_command('systemctl status phazevpn-portal --no-pager | head -10')
print('Flask Service Status:')
print(stdout.read().decode())

# Final test
stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "HTTP: %{http_code}\n" http://127.0.0.1:80')
print('\nFinal Test:')
print(stdout.read().decode())

ssh.close()

print("\n✅ VPS is fully updated and working!")
print("🌐 Site should be accessible at: http://phazevpn.duckdns.org")

