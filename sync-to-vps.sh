#!/bin/bash
# Sync all website files to VPS - keeps everything updated

set -e

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="Jakes1328!@"
VPS_PATH="/opt/secure-vpn/web-portal"
LOCAL_PATH="web-portal"

echo "=========================================="
echo "Syncing Website Files to VPS"
echo "=========================================="
echo ""

# Check if paramiko is available
if ! python3 -c "import paramiko" 2>/dev/null; then
    echo "Installing paramiko..."
    pip3 install paramiko --user 2>/dev/null || {
        echo "❌ Could not install paramiko"
        echo "Install manually: pip3 install paramiko"
        exit 1
    }
fi

python3 << 'PYTHON_SCRIPT'
import paramiko
from pathlib import Path
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPS_PATH = "/opt/secure-vpn/web-portal"
LOCAL_PATH = Path("web-portal")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected to VPS")
    
    sftp = ssh.open_sftp()
    
    # Sync templates
    print("\n[1/3] Syncing templates...")
    templates_dir = LOCAL_PATH / "templates"
    if templates_dir.exists():
        for template_file in templates_dir.rglob("*.html"):
            relative_path = template_file.relative_to(templates_dir)
            remote_path = f"{VPS_PATH}/templates/{relative_path}"
            
            # Create remote directory if needed
            remote_dir = "/".join(remote_path.split("/")[:-1])
            ssh.exec_command(f"mkdir -p {remote_dir}")
            
            sftp.put(str(template_file), remote_path)
            print(f"   ✅ {relative_path}")
    
    # Sync static files (CSS, JS, images)
    print("\n[2/3] Syncing static files...")
    static_dir = LOCAL_PATH / "static"
    if static_dir.exists():
        for static_file in static_dir.rglob("*"):
            if static_file.is_file():
                relative_path = static_file.relative_to(static_dir)
                remote_path = f"{VPS_PATH}/static/{relative_path}"
                
                # Create remote directory if needed
                remote_dir = "/".join(remote_path.split("/")[:-1])
                ssh.exec_command(f"mkdir -p {remote_dir}")
                
                sftp.put(str(static_file), remote_path)
                print(f"   ✅ {relative_path}")
    
    # Sync app.py if it exists
    print("\n[3/3] Syncing app.py...")
    app_py = LOCAL_PATH / "app.py"
    if app_py.exists():
        sftp.put(str(app_py), f"{VPS_PATH}/app.py")
        print("   ✅ app.py")
    
    sftp.close()
    
    # Restart web service
    print("\n[4/4] Restarting web service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl restart phazevpn-web 2>&1")
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        print("   ✅ Web service restarted")
    else:
        error = stderr.read().decode().strip()
        print(f"   ⚠️  Restart had issues: {error}")
    
    # Check service status
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active phazevpn-web 2>&1")
    status = stdout.read().decode().strip()
    if status == "active":
        print("   ✅ Web service is active")
    else:
        print(f"   ⚠️  Web service status: {status}")
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("✅ Sync Complete!")
    print("=" * 60)
    print("\n🌐 Site should be updated at:")
    print("   https://phazevpn.duckdns.org")
    print("   http://15.204.11.19")
    
except Exception as e:
    print(f"\n❌ Sync failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "✅ All files synced to VPS!"

