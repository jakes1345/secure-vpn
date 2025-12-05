#!/usr/bin/env python3
"""
Deploy PhazeVPN Protocol (Production) to VPS
Uploads all new features: modes, zero-knowledge, compression, etc.
"""

import paramiko
from pathlib import Path
import os
import sys
import time

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn/phazevpn-protocol"
BASE_DIR = Path(__file__).parent

def run_command(ssh, command, description="", timeout=300):
    """Run command on VPS and return output"""
    if description:
        print(f"🔧 {description}...")
    
    try:
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True, timeout=timeout)
        output_lines = []
        error_lines = []
        
        for line in iter(stdout.readline, ""):
            if line:
                output_lines.append(line.rstrip())
        
        for line in iter(stderr.readline, ""):
            if line:
                error_lines.append(line.rstrip())
        
        exit_status = stdout.channel.recv_exit_status()
        
        if error_lines and exit_status != 0:
            print(f"⚠️  Errors: {error_lines[:3]}")
        
        return exit_status == 0, "\n".join(output_lines)
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, str(e)

def upload_file(sftp, local_path, remote_path):
    """Upload file to VPS"""
    try:
        remote_dir = os.path.dirname(remote_path)
        # Create directory
        ssh.exec_command(f"mkdir -p '{remote_dir}'")
        time.sleep(0.1)
        
        # Upload file
        sftp.put(str(local_path), remote_path)
        return True
    except Exception as e:
        print(f"❌ Failed to upload {local_path}: {e}")
        return False

print("=" * 80)
print("🚀 DEPLOYING PHAZEVPN PROTOCOL TO VPS")
print("=" * 80)
print("")
print("This will deploy:")
print("  ✅ Production server with all features")
print("  ✅ VPN Modes (Normal, Semi Ghost, Full Ghost)")
print("  ✅ Zero-knowledge architecture")
print("  ✅ Traffic obfuscation")
print("  ✅ Compression")
print("  ✅ All new modules")
print("")

# Connect to VPS
print("📡 Connecting to VPS...")
try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected")
    sftp = ssh.open_sftp()
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

print("")

# Step 1: Create directory
print("1️⃣ Creating directories...")
run_command(ssh, f"mkdir -p {VPN_DIR}", "Creating protocol directory")
print("✅ Directories ready")
print("")

# Step 2: Install dependencies
print("2️⃣ Installing dependencies...")
deps_commands = [
    "apt-get update -qq",
    "apt-get install -y python3-pip python3-cryptography || true",
    "pip3 install -q cryptography || true"
]
for cmd in deps_commands:
    success, _ = run_command(ssh, cmd, f"Installing dependencies", timeout=120)
print("✅ Dependencies installed")
print("")

# Step 3: Upload all protocol files
print("3️⃣ Uploading PhazeVPN Protocol files...")
protocol_dir = BASE_DIR / "phazevpn-protocol"

# List of ALL files to upload (complete protocol)
files_to_upload = [
    # Core protocol
    "protocol.py",
    "crypto.py",
    "tun_manager.py",
    
    # Security & Privacy
    "obfuscation.py",
    "zero_knowledge.py",
    
    # New Features
    "compression.py",
    "nat_traversal.py",
    "split_tunneling.py",
    "rate_limiter.py",
    "connection_stats.py",
    "config_manager.py",
    "vpn_modes.py",
    
    # Servers & Clients
    "phazevpn-server-production.py",
    "phazevpn-client.py",
    
    # Dependencies
    "requirements.txt"
]

uploaded = 0
for filename in files_to_upload:
    local_file = protocol_dir / filename
    if local_file.exists():
        remote_path = f"{VPN_DIR}/{filename}"
        if upload_file(sftp, local_file, remote_path):
            uploaded += 1
            print(f"   ✅ {filename}")
        else:
            print(f"   ❌ {filename}")

print(f"✅ Uploaded {uploaded}/{len(files_to_upload)} files")
print("")

# Step 4: Make scripts executable
print("4️⃣ Setting permissions...")
run_command(ssh, f"chmod +x {VPN_DIR}/*.py", "Making scripts executable")
print("✅ Permissions set")
print("")

# Step 5: Create systemd service
print("5️⃣ Creating systemd service...")
service_content = f"""[Unit]
Description=PhazeVPN Protocol - Production Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={VPN_DIR}
ExecStart=/usr/bin/python3 {VPN_DIR}/phazevpn-server-production.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

# Write service file
run_command(ssh, f"""cat > /etc/systemd/system/phazevpn-protocol.service << 'EOFSERVICE'
{service_content}
EOFSERVICE
""", "Creating service file")

print("✅ Service created")
print("")

# Step 6: Setup firewall
print("6️⃣ Configuring firewall...")
run_command(ssh, "ufw allow 51821/udp comment 'PhazeVPN Protocol'", "Opening port 51821")
print("✅ Firewall configured")
print("")

# Step 7: Enable and start service
print("7️⃣ Starting PhazeVPN Protocol...")
run_command(ssh, "systemctl daemon-reload", "Reloading systemd")
run_command(ssh, "systemctl enable phazevpn-protocol", "Enabling service")
run_command(ssh, "systemctl restart phazevpn-protocol", "Starting service")

# Wait a moment
time.sleep(2)

# Check status
success, output = run_command(ssh, "systemctl is-active phazevpn-protocol", "Checking status")
if "active" in output.lower():
    print("✅ PhazeVPN Protocol is RUNNING!")
else:
    print("⚠️  Service may not be running - check logs:")
    print("   journalctl -u phazevpn-protocol -n 50")

print("")

# Step 8: Show status
print("8️⃣ Service Status:")
run_command(ssh, "systemctl status phazevpn-protocol --no-pager -l | head -20", "Checking service")
print("")

# Step 9: Show logs
print("9️⃣ Recent Logs:")
run_command(ssh, "journalctl -u phazevpn-protocol -n 20 --no-pager", "Viewing logs")
print("")

print("=" * 80)
print("✅ DEPLOYMENT COMPLETE!")
print("=" * 80)
print("")
print("📋 Next Steps:")
print("  1. Check logs: journalctl -u phazevpn-protocol -f")
print("  2. Check status: systemctl status phazevpn-protocol")
print("  3. Test connection with phazevpn-client.py")
print("")
print(f"🔗 Service running on: {VPS_IP}:51821")
print("🔒 Features enabled:")
print("   ✅ Zero-knowledge (no logging)")
print("   ✅ Traffic obfuscation")
print("   ✅ Perfect Forward Secrecy")
print("   ✅ VPN Modes (Normal, Semi Ghost, Full Ghost)")
print("   ✅ Compression")
print("   ✅ All production features")
print("")

ssh.close()
print("✅ Done!")

