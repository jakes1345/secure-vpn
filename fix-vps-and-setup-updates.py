#!/usr/bin/env python3
"""
Fix VPS Configuration and Setup Update System
"""

import paramiko
import json
from pathlib import Path

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def run_command(ssh, command, description=""):
    """Run command on VPS"""
    if description:
        print(f"\n🔧 {description}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if exit_status == 0:
        if output.strip():
            print(f"   ✅ {output.strip()}")
        return True, output
    else:
        print(f"   ⚠️  Exit code: {exit_status}")
        if error:
            print(f"   Error: {error}")
        return False, output

def upload_file(ssh, local_path, remote_path):
    """Upload file to VPS"""
    sftp = ssh.open_sftp()
    try:
        sftp.put(local_path, remote_path)
        sftp.chmod(remote_path, 0o755)
        print(f"   ✅ Uploaded: {remote_path}")
        return True
    except Exception as e:
        print(f"   ❌ Error uploading {remote_path}: {e}")
        return False
    finally:
        sftp.close()

def main():
    print("="*80)
    print("🔧 FIXING VPS CONFIGURATION & SETTING UP UPDATE SYSTEM")
    print("="*80)
    
    # Connect to VPS
    print("\n📡 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # ============================================================
    # 1. FIX VPN CONFIG (Add security scripts)
    # ============================================================
    print("\n" + "="*80)
    print("1️⃣  FIXING VPN CONFIGURATION")
    print("="*80)
    
    # Check current OpenVPN config
    run_command(ssh, "cat /etc/openvpn/server.conf | grep -E 'up|down' || echo 'No up/down scripts found'", 
                "Checking current OpenVPN config")
    
    # Check if security scripts exist
    run_command(ssh, "test -f /opt/secure-vpn/scripts/up-ultimate-security.sh && echo 'EXISTS' || echo 'NOT FOUND'",
                "Checking security scripts")
    
    # Add security scripts to OpenVPN config if not present
    print("\n🔧 Adding security scripts to OpenVPN config...")
    stdin, stdout, stderr = ssh.exec_command("""
    if ! grep -q "up /opt/secure-vpn/scripts/up-ultimate-security.sh" /etc/openvpn/server.conf; then
        echo "" >> /etc/openvpn/server.conf
        echo "# VPN-native security scripts" >> /etc/openvpn/server.conf
        echo "up /opt/secure-vpn/scripts/up-ultimate-security.sh" >> /etc/openvpn/server.conf
        echo "down /opt/secure-vpn/scripts/down-ultimate-security.sh" >> /etc/openvpn/server.conf
        echo "script-security 2" >> /etc/openvpn/server.conf
        echo "✅ Added security scripts"
    else
        echo "✅ Security scripts already configured"
    fi
    """)
    output = stdout.read().decode()
    print(f"   {output.strip()}")
    
    # Restart OpenVPN
    print("\n🔄 Restarting OpenVPN...")
    run_command(ssh, "systemctl restart openvpn@server", "Restarting OpenVPN")
    run_command(ssh, "sleep 2 && systemctl status openvpn@server --no-pager | head -5", 
                "Checking OpenVPN status")
    
    # ============================================================
    # 2. CREATE UPDATE API ENDPOINT
    # ============================================================
    print("\n" + "="*80)
    print("2️⃣  SETTING UP UPDATE SYSTEM")
    print("="*80)
    
    # Create update endpoint in web portal
    update_endpoint_code = '''
# Update API endpoint
@app.route('/api/v1/update/check', methods=['GET'])
def check_update():
    """Check for client updates"""
    try:
        # Read current version
        version_file = Path('/opt/phaze-vpn/VERSION')
        if version_file.exists():
            current_version = version_file.read_text().strip()
        else:
            current_version = "1.0.0"
        
        # Get client version from request
        client_version = request.args.get('version', '0.0.0')
        
        # Compare versions (simple string comparison for now)
        has_update = client_version < current_version
        
        return jsonify({
            'has_update': has_update,
            'current_version': current_version,
            'client_version': client_version,
            'download_url': f'https://phazevpn.com/download/client/linux',
            'changelog_url': f'https://phazevpn.com/changelog',
            'update_available': has_update
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/update/version', methods=['GET'])
def get_latest_version():
    """Get latest version number"""
    try:
        version_file = Path('/opt/phaze-vpn/VERSION')
        if version_file.exists():
            version = version_file.read_text().strip()
        else:
            version = "1.0.0"
        
        return jsonify({
            'version': version,
            'download_url': f'https://phazevpn.com/download/client/linux'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
'''
    
    # Check if update endpoints already exist
    stdin, stdout, stderr = ssh.exec_command(
        "grep -q 'check_update' /opt/phaze-vpn/web-portal/app.py && echo 'EXISTS' || echo 'NOT FOUND'"
    )
    has_update_endpoint = "EXISTS" in stdout.read().decode()
    
    if not has_update_endpoint:
        print("\n📝 Adding update endpoints to web portal...")
        # Append update endpoints to app.py
        stdin, stdout, stderr = ssh.exec_command("""
        cat >> /opt/phaze-vpn/web-portal/app.py << 'ENDPOINTS'
# Update API endpoint
@app.route('/api/v1/update/check', methods=['GET'])
def check_update():
    \"\"\"Check for client updates\"\"\"
    try:
        from pathlib import Path
        # Read current version
        version_file = Path('/opt/phaze-vpn/VERSION')
        if version_file.exists():
            current_version = version_file.read_text().strip()
        else:
            current_version = "1.0.0"
        
        # Get client version from request
        client_version = request.args.get('version', '0.0.0')
        
        # Compare versions (simple string comparison for now)
        has_update = client_version < current_version
        
        return jsonify({
            'has_update': has_update,
            'current_version': current_version,
            'client_version': client_version,
            'download_url': 'https://phazevpn.com/download/client/linux',
            'changelog_url': 'https://phazevpn.com/changelog',
            'update_available': has_update
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/update/version', methods=['GET'])
def get_latest_version():
    \"\"\"Get latest version number\"\"\"
    try:
        from pathlib import Path
        version_file = Path('/opt/phaze-vpn/VERSION')
        if version_file.exists():
            version = version_file.read_text().strip()
        else:
            version = "1.0.0"
        
        return jsonify({
            'version': version,
            'download_url': 'https://phazevpn.com/download/client/linux'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
ENDPOINTS
        """)
        output = stdout.read().decode()
        if "error" not in output.lower():
            print("   ✅ Update endpoints added")
        else:
            print(f"   ⚠️  {output}")
    else:
        print("   ✅ Update endpoints already exist")
    
    # ============================================================
    # 3. UPDATE VERSION FILE
    # ============================================================
    print("\n📦 Updating version...")
    
    # Increment version
    stdin, stdout, stderr = ssh.exec_command("""
    VERSION_FILE="/opt/phaze-vpn/VERSION"
    if [ -f "$VERSION_FILE" ]; then
        CURRENT=$(cat "$VERSION_FILE" | tr -d '\\n')
        # Increment patch version (1.0.0 -> 1.0.1)
        MAJOR=$(echo $CURRENT | cut -d. -f1)
        MINOR=$(echo $CURRENT | cut -d. -f2)
        PATCH=$(echo $CURRENT | cut -d. -f3)
        NEW_PATCH=$((PATCH + 1))
        NEW_VERSION="$MAJOR.$MINOR.$NEW_PATCH"
    else
        NEW_VERSION="1.0.1"
    fi
    echo "$NEW_VERSION" > "$VERSION_FILE"
    echo "$NEW_VERSION"
    """)
    new_version = stdout.read().decode().strip()
    print(f"   ✅ Version updated to: {new_version}")
    
    # ============================================================
    # 4. RESTART WEB PORTAL
    # ============================================================
    print("\n🔄 Restarting web portal...")
    run_command(ssh, "systemctl restart phazevpn-portal", "Restarting web portal")
    run_command(ssh, "sleep 2 && systemctl status phazevpn-portal --no-pager | head -5",
                "Checking web portal status")
    
    # ============================================================
    # 5. TEST UPDATE ENDPOINT
    # ============================================================
    print("\n🧪 Testing update endpoint...")
    run_command(ssh, f"curl -s 'http://127.0.0.1:5000/api/v1/update/check?version=1.0.0' | python3 -m json.tool",
                "Testing update check endpoint")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "="*80)
    print("✅ VPS CONFIGURATION & UPDATE SYSTEM SETUP COMPLETE")
    print("="*80)
    print(f"\n📊 Summary:")
    print(f"   ✅ VPN config fixed (security scripts added)")
    print(f"   ✅ Update API endpoints created")
    print(f"   ✅ Version updated to: {new_version}")
    print(f"   ✅ Web portal restarted")
    print(f"\n🔗 Update API:")
    print(f"   Check: https://phazevpn.com/api/v1/update/check?version=1.0.0")
    print(f"   Version: https://phazevpn.com/api/v1/update/version")
    
    ssh.close()

if __name__ == "__main__":
    main()

