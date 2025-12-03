#!/usr/bin/env python3
"""
Add client identification system to distinguish PhazeVPN clients from OpenVPN clients
"""

import paramiko
import subprocess
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("="*80)
    print("🔍 ADDING CLIENT IDENTIFICATION SYSTEM")
    print("="*80)
    print("\nThis will allow the server to distinguish:")
    print("  ✅ PhazeVPN clients (custom client)")
    print("  ⚠️  OpenVPN clients (standard OpenVPN)")
    print("")
    
    # Connect to VPS
    print("📡 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # ============================================================
    # 1. ENABLE CLIENT CONFIG DIRECTORY
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  ENABLING CLIENT CONFIG DIRECTORY (CCD)")
    print("="*80)
    
    # Check if CCD is enabled
    stdin, stdout, stderr = ssh.exec_command(
        "grep -q 'client-config-dir' /opt/secure-vpn/config/server.conf && echo 'EXISTS' || echo 'NOT FOUND'"
    )
    has_ccd = "EXISTS" in stdout.read().decode()
    
    if not has_ccd:
        print("\n📝 Adding CCD to server config...")
        ccd_config = """
# Client Config Directory - Allows per-client configs and identification
client-config-dir ccd
ccd-exclusive
"""
        stdin, stdout, stderr = ssh.exec_command(f"""
        echo '{ccd_config}' >> /opt/secure-vpn/config/server.conf
        mkdir -p /opt/secure-vpn/config/ccd
        echo "CCD directory created"
        """)
        output = stdout.read().decode()
        print(f"   ✅ {output.strip()}")
    else:
        print("   ✅ CCD already configured")
    
    # ============================================================
    # 2. CREATE CLIENT IDENTIFICATION SCRIPT
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  CREATING CLIENT IDENTIFICATION SCRIPT")
    print("="*80)
    
    identify_script = """#!/bin/bash
# Client Identification Script
# Called by OpenVPN when client connects
# Distinguishes PhazeVPN clients from standard OpenVPN clients

CLIENT_NAME="$1"
CLIENT_IP="$2"

# Log directory
LOG_DIR="/opt/secure-vpn/logs"
mkdir -p "$LOG_DIR"

# Check if client is PhazeVPN client
# PhazeVPN clients have CN format: phazevpn-<name> or Organization=PhazeVPN
if echo "$CLIENT_NAME" | grep -qi "phazevpn"; then
    CLIENT_TYPE="PHAZEVPN"
    echo "[$(date)] PhazeVPN client connected: $CLIENT_NAME ($CLIENT_IP)" >> "$LOG_DIR/client-connections.log"
elif [ -f "/opt/secure-vpn/config/ccd/$CLIENT_NAME" ]; then
    # Check CCD file for client type marker
    if grep -q "PHAZEVPN_CLIENT" "/opt/secure-vpn/config/ccd/$CLIENT_NAME"; then
        CLIENT_TYPE="PHAZEVPN"
        echo "[$(date)] PhazeVPN client connected: $CLIENT_NAME ($CLIENT_IP)" >> "$LOG_DIR/client-connections.log"
    else
        CLIENT_TYPE="OPENVPN"
        echo "[$(date)] OpenVPN client connected: $CLIENT_NAME ($CLIENT_IP)" >> "$LOG_DIR/client-connections.log"
    fi
else
    CLIENT_TYPE="OPENVPN"
    echo "[$(date)] OpenVPN client connected: $CLIENT_NAME ($CLIENT_IP)" >> "$LOG_DIR/client-connections.log"
fi

# Export client type for use in other scripts
export CLIENT_TYPE
export CLIENT_NAME
export CLIENT_IP

# Apply different configs based on client type
if [ "$CLIENT_TYPE" = "PHAZEVPN" ]; then
    # PhazeVPN clients get enhanced features
    echo "push \"setenv PHAZEVPN_CLIENT 1\"" >> "/opt/secure-vpn/config/ccd/$CLIENT_NAME"
    echo "push \"route-metric 1\"" >> "/opt/secure-vpn/config/ccd/$CLIENT_NAME"
else
    # Standard OpenVPN clients get basic config
    echo "# Standard OpenVPN client" >> "/opt/secure-vpn/config/ccd/$CLIENT_NAME"
fi

exit 0
"""
    
    # Upload script
    sftp = ssh.open_sftp()
    try:
        with sftp.open('/opt/secure-vpn/scripts/identify-client.sh', 'w') as f:
            f.write(identify_script)
        ssh.exec_command("chmod +x /opt/secure-vpn/scripts/identify-client.sh")
        print("   ✅ Client identification script created")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
    finally:
        sftp.close()
    
    # ============================================================
    # 3. UPDATE VPN MANAGER TO MARK PHAZEVPN CLIENTS
    # ============================================================
    print("\n" + "="*80)
    print("3️⃣  UPDATING CLIENT GENERATION")
    print("="*80)
    
    # Check current vpn-manager.py
    stdin, stdout, stderr = ssh.exec_command(
        "grep -q 'O=PhazeVPN' /opt/secure-vpn/vpn-manager.py && echo 'EXISTS' || echo 'NOT FOUND'"
    )
    has_marker = "EXISTS" in stdout.read().decode()
    
    if not has_marker:
        print("\n📝 Updating client certificate generation...")
        # Update the CN format to include phazevpn prefix
        stdin, stdout, stderr = ssh.exec_command("""
        sed -i "s|'/C=US/ST=Secure/L=VPN/O=Client/CN=\${name}'|'/C=US/ST=Secure/L=VPN/O=PhazeVPN/CN=phazevpn-\${name}'|g" /opt/secure-vpn/vpn-manager.py 2>/dev/null || \\
        sed -i "s|O=Client|O=PhazeVPN|g" /opt/secure-vpn/vpn-manager.py
        echo "Updated certificate generation"
        """)
        output = stdout.read().decode()
        print(f"   ✅ {output.strip()}")
    else:
        print("   ✅ PhazeVPN marker already in certificates")
    
    # ============================================================
    # 4. CREATE CLIENT TYPE DETECTION SCRIPT
    # ============================================================
    print("\n" + "="*80)
    print("4️⃣  CREATING CLIENT TYPE DETECTION SCRIPT")
    print("="*80)
    
    detection_script = """#!/usr/bin/env python3
\"\"\"
Detect client type from OpenVPN status/logs
\"\"\"

import re
from pathlib import Path

def get_client_type(client_name):
    \"\"\"Determine if client is PhazeVPN or OpenVPN\"\"\"
    # Check CN format
    if 'phazevpn' in client_name.lower():
        return 'PHAZEVPN'
    
    # Check certificate Organization
    cert_file = Path(f'/opt/secure-vpn/certs/{client_name}.crt')
    if cert_file.exists():
        import subprocess
        try:
            result = subprocess.run(
                ['openssl', 'x509', '-in', str(cert_file), '-noout', '-subject'],
                capture_output=True, text=True
            )
            if 'O=PhazeVPN' in result.stdout or 'O = PhazeVPN' in result.stdout:
                return 'PHAZEVPN'
        except:
            pass
    
    # Check CCD file
    ccd_file = Path(f'/opt/secure-vpn/config/ccd/{client_name}')
    if ccd_file.exists():
        content = ccd_file.read_text()
        if 'PHAZEVPN_CLIENT' in content:
            return 'PHAZEVPN'
    
    return 'OPENVPN'

def get_connected_clients():
    \"\"\"Get list of connected clients with their types\"\"\"
    clients = []
    
    # Parse OpenVPN status
    status_file = Path('/run/openvpn/server.status')
    if not status_file.exists():
        status_file = Path('/opt/secure-vpn/logs/status.log')
    
    if status_file.exists():
        content = status_file.read_text()
        # Parse client lines (format: CLIENT_LIST,name,ip,port,protocol)
        for line in content.split('\\n'):
            if line.startswith('CLIENT_LIST'):
                parts = line.split(',')
                if len(parts) >= 3:
                    client_name = parts[1]
                    client_ip = parts[2]
                    client_type = get_client_type(client_name)
                    clients.append({
                        'name': client_name,
                        'ip': client_ip,
                        'type': client_type
                    })
    
    return clients

if __name__ == '__main__':
    clients = get_connected_clients()
    for client in clients:
        print(f"{client['name']}: {client['type']} ({client['ip']})")
"""
    
    # Upload detection script
    sftp = ssh.open_sftp()
    try:
        with sftp.open('/opt/secure-vpn/scripts/detect-client-type.py', 'w') as f:
            f.write(detection_script)
        ssh.exec_command("chmod +x /opt/secure-vpn/scripts/detect-client-type.py")
        print("   ✅ Client type detection script created")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
    finally:
        sftp.close()
    
    # ============================================================
    # 5. UPDATE SERVER CONFIG TO USE IDENTIFICATION
    # ============================================================
    print("\n" + "="*80)
    print("5️⃣  UPDATING SERVER CONFIG")
    print("="*80)
    
    # Add learn-address script to identify clients on connect
    stdin, stdout, stderr = ssh.exec_command("""
    if ! grep -q "learn-address" /opt/secure-vpn/config/server.conf; then
        echo "" >> /opt/secure-vpn/config/server.conf
        echo "# Client identification" >> /opt/secure-vpn/config/server.conf
        echo "learn-address /opt/secure-vpn/scripts/identify-client.sh" >> /opt/secure-vpn/config/server.conf
        echo "script-security 2" >> /opt/secure-vpn/config/server.conf
        echo "✅ Added learn-address script"
    else
        echo "✅ learn-address already configured"
    fi
    """)
    output = stdout.read().decode()
    print(f"   {output.strip()}")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "="*80)
    print("✅ CLIENT IDENTIFICATION SYSTEM ADDED")
    print("="*80)
    print("\n📊 How it works:")
    print("   1. PhazeVPN clients: CN=phazevpn-<name>, O=PhazeVPN")
    print("   2. OpenVPN clients: CN=<name>, O=Client")
    print("   3. Server detects type from certificate")
    print("   4. Different configs applied via CCD")
    print("\n🔍 To check client types:")
    print("   python3 /opt/secure-vpn/scripts/detect-client-type.py")
    print("\n📝 Next: Update vpn-manager.py to use PhazeVPN markers")
    
    ssh.close()

if __name__ == "__main__":
    main()

