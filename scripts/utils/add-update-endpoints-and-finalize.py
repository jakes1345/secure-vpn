#!/usr/bin/env python3
"""
Add update endpoints and finalize everything
"""

import paramiko
import re

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("="*80)
    print("🔧 ADDING UPDATE ENDPOINTS & FINALIZING")
    print("="*80)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # Read app.py
    sftp = ssh.open_sftp()
    with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'r') as f:
        content = f.read().decode('utf-8')
    
    # Check if update endpoints exist
    if '/api/v1/update/check' not in content:
        # Find a good place to add them (after mobile app endpoints)
        insert_pos = content.find('@app.route(\'/api/app/configs')
        if insert_pos > 0:
            # Find end of that function
            end_pos = content.find('\n\n@app.route', insert_pos + 500)
            if end_pos < 0:
                end_pos = content.find('\n\n# ============================================', insert_pos + 500)
            
            if end_pos > 0:
                update_endpoints = '''

# ============================================
# UPDATE API ENDPOINTS
# ============================================

def get_current_version():
    """Get current version from VERSION file"""
    version_file = Path(__file__).parent.parent / 'VERSION'
    if version_file.exists():
        try:
            with open(version_file) as f:
                return f.read().strip()
        except:
            pass
    return '1.0.1'  # Default version

def parse_version(version_str):
    """Parse version string to tuple for comparison"""
    try:
        parts = version_str.split('.')
        return tuple(int(p) for p in parts[:3])
    except:
        return (0, 0, 0)

@app.route('/api/v1/update/check', methods=['GET'])
def check_for_update():
    """Check if update is available"""
    try:
        client_version = request.args.get('version', '0.0.0')
        current_version = get_current_version()
        has_update = parse_version(current_version) > parse_version(client_version)
        
        return jsonify({
            'update_available': has_update,
            'current_version': current_version,
            'client_version': client_version,
            'download_url': url_for('download_client', platform='linux', _external=True),
            'changelog_url': url_for('changelog', _external=True) if hasattr(app, 'changelog') else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/update/version', methods=['GET'])
def get_latest_version():
    """Get latest version number"""
    try:
        return jsonify({'version': get_current_version()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

'''
                content = content[:end_pos] + update_endpoints + content[end_pos:]
                print("   ✅ Added update endpoints")
    
    # Write back
    with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'w') as f:
        f.write(content.encode('utf-8'))
    sftp.close()
    
    # Test
    stdin, stdout, stderr = ssh.exec_command('cd /opt/phaze-vpn/web-portal && python3 -c "import app; print(\"OK\")" 2>&1')
    output = stdout.read().decode()
    if 'OK' in output:
        print("   ✅ App.py is valid!")
    else:
        print(f"   ⚠️  Error: {output[:300]}")
    
    # Restart
    print("\n🔄 Restarting portal...")
    stdin, stdout, stderr = ssh.exec_command('systemctl restart phazevpn-portal && sleep 3 && systemctl status phazevpn-portal --no-pager | head -5')
    print(stdout.read().decode())
    
    # Test update endpoint
    print("\n🧪 Testing update endpoint...")
    stdin, stdout, stderr = ssh.exec_command('curl -s "http://127.0.0.1:5000/api/v1/update/check?version=1.0.0" 2>&1')
    response = stdout.read().decode()
    if 'update_available' in response:
        print(f"   ✅ Update endpoint working: {response[:200]}")
    else:
        print(f"   ⚠️  Response: {response[:200]}")
    
    ssh.close()

if __name__ == "__main__":
    from pathlib import Path
    main()

