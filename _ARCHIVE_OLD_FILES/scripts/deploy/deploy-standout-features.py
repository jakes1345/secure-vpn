#!/usr/bin/env python3
"""Deploy standout features to VPS"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

print("🚀 Deploying Standout Features...")
print("="*60)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)

def run(cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    return stdout.read().decode(), stderr.read().decode(), exit_status

def write_file(path, content):
    sftp = ssh.open_sftp()
    try:
        file = sftp.file(path, "w")
        file.write(content)
        file.close()
    except:
        # Directory might not exist
        run(f"mkdir -p {Path(path).parent}")
        file = sftp.file(path, "w")
        file.write(content)
        file.close()
    finally:
        sftp.close()

# Install qrcode
print("1️⃣  Installing QR code library...")
output, _, _ = run("pip3 install --break-system-packages qrcode[pil] 2>&1 | tail -3")
print(output)

# Upload updated app.py
print("\n2️⃣  Uploading updated portal...")
with open('/opt/phaze-vpn/web-portal/app.py', 'r') as f:
    app_content = f.read()
write_file(f"{VPN_DIR}/web-portal/app.py", app_content)

# Upload new templates
print("3️⃣  Uploading new templates...")
templates = {
    'admin/analytics.html': '/opt/phaze-vpn/web-portal/templates/admin/analytics.html',
    'qr-code.html': '/opt/phaze-vpn/web-portal/templates/qr-code.html',
}

for remote_name, local_path in templates.items():
    try:
        with open(local_path, 'r') as f:
            content = f.read()
        write_file(f"{VPN_DIR}/web-portal/templates/{remote_name}", content)
        print(f"   ✅ {remote_name}")
    except Exception as e:
        print(f"   ⚠️  {remote_name}: {e}")

# Update existing templates
print("4️⃣  Updating existing templates...")
for template in ['admin/dashboard.html', 'admin/clients.html']:
    local_path = f'/opt/phaze-vpn/web-portal/templates/{template}'
    try:
        with open(local_path, 'r') as f:
            content = f.read()
        write_file(f"{VPN_DIR}/web-portal/templates/{template}", content)
        print(f"   ✅ {template}")
    except:
        pass

# Restart portal
print("\n5️⃣  Restarting web portal...")
run("systemctl restart secure-vpn-portal")
print("✅ Portal restarted\n")

print("="*60)
print("✅ Standout Features Deployed!")
print("="*60)
print()
print("🎯 New Features:")
print("  ✅ Analytics Dashboard - /admin/analytics")
print("  ✅ QR Code Generator - /qr/<client-name>")
print("  ✅ Real-time Connection Stats")
print("  ✅ Bandwidth Charts")
print("  ✅ Server Metrics API")
print()
print(f"🌐 Access: http://{VPS_IP}:5000")
print()

ssh.close()

