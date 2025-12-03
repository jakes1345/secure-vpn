#!/usr/bin/env python3
"""Setup web portal on VPS"""

import paramiko
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

print("🚀 Setting up Web Portal on VPS...")
print("="*60)
print()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    errors = stderr.read().decode()
    return output, errors, exit_status

def write_file(path, content):
    sftp = ssh.open_sftp()
    file = sftp.file(path, "w")
    file.write(content)
    file.close()
    sftp.close()

# Step 1: Install Flask
print("1️⃣  Installing Flask...")
output, errors, _ = run("pip3 install Flask==3.0.0 Werkzeug==3.0.1 2>&1 | tail -5")
print(output)
print("✅ Flask installed\n")

# Step 2: Create web portal directory
print("2️⃣  Creating web portal directory...")
run(f"mkdir -p {VPN_DIR}/web-portal/templates/admin")
run(f"mkdir -p {VPN_DIR}/web-portal/templates/moderator")
run(f"mkdir -p {VPN_DIR}/web-portal/templates/user")
print("✅ Directories created\n")

# Step 3: Transfer app.py
print("3️⃣  Uploading web portal files...")
print("   (Transferring app.py)")
with open('/opt/phaze-vpn/web-portal/app.py', 'r') as f:
    app_content = f.read()

write_file(f"{VPN_DIR}/web-portal/app.py", app_content)
run(f"chmod +x {VPN_DIR}/web-portal/app.py")
print("✅ app.py uploaded\n")

# Step 4: Transfer templates (simplified - just key files)
print("4️⃣  Uploading templates...")
template_files = [
    ('base.html', 'templates/base.html'),
    ('login.html', 'templates/login.html'),
    ('error.html', 'templates/error.html'),
    ('admin/dashboard.html', 'templates/admin/dashboard.html'),
    ('admin/clients.html', 'templates/admin/clients.html'),
    ('admin/users.html', 'templates/admin/users.html'),
    ('moderator/dashboard.html', 'templates/moderator/dashboard.html'),
    ('user/dashboard.html', 'templates/user/dashboard.html'),
]

for local_name, remote_path in template_files:
    local_path = f'/opt/phaze-vpn/web-portal/{remote_path}'
    try:
        with open(local_path, 'r') as f:
            content = f.read()
        write_file(f"{VPN_DIR}/web-portal/{remote_path}", content)
        print(f"   ✅ {remote_path}")
    except Exception as e:
        print(f"   ⚠️  {remote_path}: {e}")

print("✅ Templates uploaded\n")

# Step 5: Create systemd service
print("5️⃣  Creating systemd service...")
service_content = f"""[Unit]
Description=SecureVPN Web Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={VPN_DIR}/web-portal
ExecStart=/usr/bin/python3 {VPN_DIR}/web-portal/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment="FLASK_ENV=production"

[Install]
WantedBy=multi-user.target
"""

write_file("/etc/systemd/system/secure-vpn-portal.service", service_content)
run("systemctl daemon-reload")
run("systemctl enable secure-vpn-portal")
print("✅ Systemd service created\n")

# Step 6: Configure firewall
print("6️⃣  Configuring firewall...")
run("ufw allow 5000/tcp")
print("✅ Firewall configured\n")

# Step 7: Start service
print("7️⃣  Starting web portal...")
run("systemctl start secure-vpn-portal")
time.sleep(3)

status = run("systemctl is-active secure-vpn-portal")[0].strip()
print(f"Portal Status: {status}\n")

# Check if it's running
port_check = run("netstat -tulpn | grep 5000")[0]
if port_check.strip():
    print(f"✅ Port 5000 is listening!\n")
else:
    print("⚠️  Port 5000 not listening yet (may take a moment)\n")

print("="*60)
print("✅ Web Portal Setup Complete!")
print("="*60)
print()
print(f"🌐 Access the portal:")
print(f"   http://{VPS_IP}:5000")
print()
print("Default logins:")
print("  Admin: admin / admin123")
print("  Moderator: moderator / mod123")
print("  User: user / user123")
print()
print("Commands:")
print("  systemctl status secure-vpn-portal")
print("  systemctl restart secure-vpn-portal")
print("  tail -f /var/log/syslog | grep secure-vpn-portal")
print()

ssh.close()

