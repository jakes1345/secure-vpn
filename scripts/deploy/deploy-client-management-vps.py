#!/usr/bin/env python3
"""
Deploy Client Management System to VPS
Uploads client_manager.py and manage-clients.py
"""

import paramiko
from pathlib import Path
import os

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn/phazevpn-protocol"
BASE_DIR = Path(__file__).parent

print("=" * 80)
print("🚀 DEPLOYING CLIENT MANAGEMENT TO VPS")
print("=" * 80)
print("")

try:
    print("📡 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("✅ Connected")
    print("")
    
    sftp = ssh.open_sftp()
    
    # Upload client_manager.py
    print("1️⃣ Uploading client_manager.py...")
    local_file = BASE_DIR / "phazevpn-protocol" / "client_manager.py"
    remote_path = f"{VPN_DIR}/client_manager.py"
    sftp.put(str(local_file), remote_path)
    print("   ✅ client_manager.py uploaded")
    
    # Upload manage-clients.py
    print("2️⃣ Uploading manage-clients.py...")
    local_file = BASE_DIR / "phazevpn-protocol" / "manage-clients.py"
    remote_path = f"{VPN_DIR}/manage-clients.py"
    sftp.put(str(local_file), remote_path)
    print("   ✅ manage-clients.py uploaded")
    
    # Upload create-client.sh
    print("3️⃣ Uploading create-client.sh...")
    local_file = BASE_DIR / "phazevpn-protocol" / "create-client.sh"
    remote_path = f"{VPN_DIR}/create-client.sh"
    sftp.put(str(local_file), remote_path)
    print("   ✅ create-client.sh uploaded")
    
    # Make scripts executable
    print("4️⃣ Setting permissions...")
    ssh.exec_command(f"chmod +x {VPN_DIR}/manage-clients.py {VPN_DIR}/create-client.sh")
    print("   ✅ Permissions set")
    
    # Create client configs directory
    print("5️⃣ Creating directories...")
    ssh.exec_command(f"mkdir -p {VPN_DIR.replace('/phazevpn-protocol', '')}/phazevpn-client-configs")
    ssh.exec_command(f"mkdir -p {VPN_DIR.replace('/phazevpn-protocol', '')}/phazevpn-protocol")
    print("   ✅ Directories created")
    
    sftp.close()
    
    print("")
    print("=" * 80)
    print("✅ CLIENT MANAGEMENT DEPLOYED!")
    print("=" * 80)
    print("")
    print("📋 Usage:")
    print("")
    print("  # Create a client")
    print("  cd /opt/secure-vpn/phazevpn-protocol")
    print("  python3 manage-clients.py create john")
    print("")
    print("  # List all clients")
    print("  python3 manage-clients.py list")
    print("")
    print("  # Reset password")
    print("  python3 manage-clients.py reset-password john")
    print("")
    print("  # Quick create")
    print("  ./create-client.sh alice semi_ghost")
    print("")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

