#!/usr/bin/env python3
"""
Complete VPS Deployment - PhazeVPN Portal + PhazeVPN Protocol
Deploys everything: web portal, PhazeVPN Protocol, production setup
"""

import paramiko
import os
from pathlib import Path
import sys

# VPS Configuration
VPS_HOST = os.environ.get('VPS_HOST', '15.204.11.19')  # Your VPS IP
VPS_USER = os.environ.get('VPS_USER', 'root')
VPS_PORT = int(os.environ.get('VPS_PORT', '22'))
VPS_KEY_PATH = os.environ.get('VPS_SSH_KEY', None)  # Path to SSH key if using key auth

BASE_DIR = Path(__file__).parent
WEB_PORTAL_DIR = BASE_DIR / 'web-portal'
PROTOCOL_DIR = BASE_DIR / 'phazevpn-protocol'

def run_command(ssh, command, description=""):
    """Run command on remote server"""
    if description:
        print(f"   {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    if exit_status != 0:
        print(f"   ⚠️  Error: {error}")
        return False, error
    return True, output

def upload_file(sftp, local_path, remote_path):
    """Upload file to VPS"""
    try:
        # Create remote directory if needed
        remote_dir = '/'.join(remote_path.split('/')[:-1])
        run_command(sftp.get_channel().get_transport().open_session(), f'mkdir -p {remote_dir}')
        
        sftp.put(str(local_path), remote_path)
        return True
    except Exception as e:
        print(f"   ❌ Failed to upload {local_path}: {e}")
        return False

def upload_directory(sftp, local_dir, remote_dir):
    """Upload directory recursively"""
    local_path = Path(local_dir)
    for item in local_path.rglob('*'):
        if item.is_file():
            relative = item.relative_to(local_path)
            remote_path = f"{remote_dir}/{relative}"
            print(f"   Uploading: {relative}")
            upload_file(sftp, item, remote_path)

print("=" * 80)
print("🚀 Complete VPS Deployment - PhazeVPN")
print("=" * 80)
print("")
print(f"VPS: {VPS_USER}@{VPS_HOST}:{VPS_PORT}")
print("")

# Get SSH password if not using key
if not VPS_KEY_PATH:
    import getpass
    ssh_password = getpass.getpass(f"Enter SSH password for {VPS_USER}@{VPS_HOST}: ")
else:
    ssh_password = None

# Connect to VPS
print("1️⃣  Connecting to VPS...")
try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    if VPS_KEY_PATH:
        ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, key_filename=VPS_KEY_PATH)
    else:
        ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=ssh_password)
    
    print("   ✅ Connected to VPS")
except Exception as e:
    print(f"   ❌ Failed to connect: {e}")
    sys.exit(1)

sftp = ssh.open_sftp()

# Step 2: Upload web portal
print("")
print("2️⃣  Uploading web portal files...")
remote_web_dir = '/opt/phazevpn/web-portal'
run_command(ssh, f'mkdir -p {remote_web_dir}')
upload_directory(sftp, WEB_PORTAL_DIR, remote_web_dir)
print("   ✅ Web portal uploaded")

# Step 3: Upload PhazeVPN Protocol
print("")
print("3️⃣  Uploading PhazeVPN Protocol...")
remote_protocol_dir = '/opt/phazevpn/phazevpn-protocol'
run_command(ssh, f'mkdir -p {remote_protocol_dir}')
upload_directory(sftp, PROTOCOL_DIR, remote_protocol_dir)
print("   ✅ PhazeVPN Protocol uploaded")

# Step 4: Upload other critical files
print("")
print("4️⃣  Uploading configuration files...")
files_to_upload = [
    ('vpn-manager.py', '/opt/phazevpn/vpn-manager.py'),
    ('client-download-server.py', '/opt/phazevpn/client-download-server.py'),
    ('setup-production-deployment.sh', '/opt/phazevpn/setup-production-deployment.sh'),
]

for local_file, remote_file in files_to_upload:
    local_path = BASE_DIR / local_file
    if local_path.exists():
        upload_file(sftp, local_path, remote_file)
        print(f"   ✅ {local_file} uploaded")

# Step 5: Install dependencies
print("")
print("5️⃣  Installing dependencies on VPS...")
run_command(ssh, 'apt-get update -qq')
run_command(ssh, 'apt-get install -y python3-pip python3-venv nginx certbot python3-certbot-nginx')
run_command(ssh, f'cd {remote_web_dir} && pip3 install -r requirements.txt --quiet')
print("   ✅ Dependencies installed")

# Step 6: Set up systemd service for portal
print("")
print("6️⃣  Setting up systemd service for web portal...")
service_content = f"""[Unit]
Description=PhazeVPN Web Portal (Gunicorn)
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory={remote_web_dir}
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="VPN_SERVER_IP=phazevpn.duckdns.org"
Environment="VPN_SERVER_PORT=1194"
Environment="HTTPS_ENABLED=true"
ExecStart=/usr/local/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 --timeout 120 --access-logfile /var/log/phazevpn-portal-access.log --error-logfile /var/log/phazevpn-portal-error.log app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

# Write service file
stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/systemd/system/phazevpn-portal.service << "EOFSERVICE"\n{service_content}\nEOFSERVICE\n')
stdout.channel.recv_exit_status()
run_command(ssh, 'systemctl daemon-reload')
run_command(ssh, 'systemctl enable phazevpn-portal')
print("   ✅ Systemd service created")

# Step 7: Set up systemd service for PhazeVPN Protocol
print("")
print("7️⃣  Setting up systemd service for PhazeVPN Protocol...")
protocol_service = f"""[Unit]
Description=PhazeVPN Protocol Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={remote_protocol_dir}
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 {remote_protocol_dir}/phazevpn-server-production.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/systemd/system/phazevpn-protocol.service << "EOFSERVICE"\n{protocol_service}\nEOFSERVICE\n')
stdout.channel.recv_exit_status()
run_command(ssh, 'systemctl daemon-reload')
run_command(ssh, 'systemctl enable phazevpn-protocol')
print("   ✅ PhazeVPN Protocol service created")

# Step 8: Set up Nginx
print("")
print("8️⃣  Setting up Nginx...")
nginx_config = f"""# HTTP to HTTPS redirect
server {{
    listen 80;
    listen [::]:80;
    server_name phazevpn.duckdns.org;

    location /.well-known/acme-challenge/ {{
        root /var/www/html;
    }}

    location / {{
        return 301 https://$server_name$request_uri;
    }}
}}

# HTTPS server
server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name phazevpn.duckdns.org;

    ssl_certificate /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/phazevpn.duckdns.org/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location /static {{
        alias {remote_web_dir}/static;
        expires 30d;
    }}
}}
"""

stdin, stdout, stderr = ssh.exec_command(f'cat > /etc/nginx/sites-available/phazevpn << "EOFCONFIG"\n{nginx_config}\nEOFCONFIG\n')
stdout.channel.recv_exit_status()
run_command(ssh, 'ln -sf /etc/nginx/sites-available/phazevpn /etc/nginx/sites-enabled/phazevpn')
run_command(ssh, 'rm -f /etc/nginx/sites-enabled/default')
run_command(ssh, 'nginx -t')
print("   ✅ Nginx configured")

# Step 9: Set up HTTPS (if certificate doesn't exist)
print("")
print("9️⃣  Setting up HTTPS...")
cert_check, _ = run_command(ssh, 'test -f /etc/letsencrypt/live/phazevpn.duckdns.org/fullchain.pem && echo "EXISTS" || echo "MISSING"')
if 'MISSING' in cert_check:
    print("   Requesting SSL certificate...")
    run_command(ssh, 'systemctl start nginx')  # Start nginx for Let's Encrypt challenge
    run_command(ssh, f'certbot --nginx -d phazevpn.duckdns.org --non-interactive --agree-tos --email admin@phazevpn.duckdns.org --redirect')
    print("   ✅ SSL certificate installed")
else:
    print("   ✅ SSL certificate already exists")

# Step 10: Create PhazeVPN Protocol users database if needed
print("")
print("🔟 Setting up PhazeVPN Protocol...")
run_command(ssh, f'mkdir -p {remote_protocol_dir}')
users_db_check, _ = run_command(ssh, f'test -f {remote_protocol_dir}/phazevpn-users.json && echo "EXISTS" || echo "MISSING"')
if 'MISSING' in users_db_check:
    # Create default users database
    create_users = f"""python3 << 'EOF'
import sys
sys.path.insert(0, '{remote_protocol_dir}')
from crypto import PhazeVPNCrypto
import json
from pathlib import Path

crypto = PhazeVPNCrypto()
users = {{}}
password = 'admin123'
password_hash, salt = crypto.hash_password(password)
users['admin'] = {{
    'password_hash': password_hash.hex(),
    'password_salt': salt.hex()
}}

db_path = Path('{remote_protocol_dir}/phazevpn-users.json')
with open(db_path, 'w') as f:
    json.dump(users, f, indent=2)
print('Users database created')
EOF
"""
    run_command(ssh, f'cd {remote_protocol_dir} && {create_users}')
    print("   ✅ PhazeVPN Protocol users database created")

# Step 11: Open firewall ports
print("")
print("1️⃣1️⃣  Configuring firewall...")
run_command(ssh, 'ufw allow 80/tcp')
run_command(ssh, 'ufw allow 443/tcp')
run_command(ssh, 'ufw allow 1194/udp')  # OpenVPN
run_command(ssh, 'ufw allow 51821/udp')  # PhazeVPN Protocol
run_command(ssh, 'ufw allow 8081/tcp')   # Download server
print("   ✅ Firewall configured")

# Step 12: Start services
print("")
print("1️⃣2️⃣  Starting services...")
run_command(ssh, 'systemctl restart phazevpn-portal')
run_command(ssh, 'systemctl restart phazevpn-protocol')
run_command(ssh, 'systemctl restart nginx')
print("   ✅ Services started")

# Step 13: Check status
print("")
print("1️⃣3️⃣  Checking service status...")
print("")
print("PhazeVPN Portal:")
run_command(ssh, 'systemctl status phazevpn-portal --no-pager -l | head -10')
print("")
print("PhazeVPN Protocol:")
run_command(ssh, 'systemctl status phazevpn-protocol --no-pager -l | head -10')
print("")
print("Nginx:")
run_command(ssh, 'systemctl status nginx --no-pager -l | head -5')

# Cleanup
sftp.close()
ssh.close()

print("")
print("=" * 80)
print("✅ DEPLOYMENT COMPLETE!")
print("=" * 80)
print("")
print("🌐 Your site should be accessible at:")
print("   https://phazevpn.duckdns.org")
print("")
print("🔒 VPN Services:")
print("   - OpenVPN: phazevpn.duckdns.org:1194")
print("   - PhazeVPN Protocol: phazevpn.duckdns.org:51821")
print("")
print("📝 Check logs:")
print("   ssh {VPS_USER}@{VPS_HOST} 'journalctl -u phazevpn-portal -f'")
print("   ssh {VPS_USER}@{VPS_HOST} 'journalctl -u phazevpn-protocol -f'")
print("")

