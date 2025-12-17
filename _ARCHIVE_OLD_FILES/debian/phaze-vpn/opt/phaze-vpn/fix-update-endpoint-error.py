#!/usr/bin/env python3
"""
Fix update endpoint error - make it simpler and more robust
"""

import paramiko

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("="*80)
    print("🔧 FIXING UPDATE ENDPOINT ERROR")
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
    
    # Find and fix update endpoints
    if '/api/v1/update/check' in content:
        # Replace the problematic url_for calls with direct URLs
        old_check = '''@app.route('/api/v1/update/check', methods=['GET'])
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
        return jsonify({'error': str(e)}), 500'''
        
        new_check = '''@app.route('/api/v1/update/check', methods=['GET'])
def check_for_update():
    """Check if update is available"""
    try:
        client_version = request.args.get('version', '0.0.0')
        current_version = get_current_version()
        has_update = parse_version(current_version) > parse_version(client_version)
        
        # Use direct URL instead of url_for to avoid errors
        base_url = request.url_root.rstrip('/')
        download_url = f"{base_url}/repo/pool/main/p/phaze-vpn/phaze-vpn_{current_version}_all.deb"
        
        return jsonify({
            'update_available': has_update,
            'current_version': current_version,
            'client_version': client_version,
            'download_url': download_url,
            'changelog_url': None
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500'''
        
        if old_check in content:
            content = content.replace(old_check, new_check)
            print("   ✅ Fixed update check endpoint")
        elif 'url_for(\'download_client' in content:
            # Just replace the url_for calls
            content = content.replace(
                "url_for('download_client', platform='linux', _external=True)",
                "f\"{request.url_root.rstrip('/')}/repo/pool/main/p/phaze-vpn/phaze-vpn_{get_current_version()}_all.deb\""
            )
            content = content.replace(
                "url_for('changelog', _external=True) if hasattr(app, 'changelog') else None",
                "None"
            )
            print("   ✅ Fixed url_for calls")
    
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
    stdin, stdout, stderr = ssh.exec_command('systemctl restart phazevpn-portal && sleep 5')
    stdout.read()
    
    # Test
    print("\n🧪 Testing update endpoint...")
    stdin, stdout, stderr = ssh.exec_command('curl -s "http://127.0.0.1:5000/api/v1/update/check?version=1.0.0" 2>&1')
    response = stdout.read().decode()
    if 'update_available' in response or 'current_version' in response:
        print(f"   ✅ Update endpoint working!")
        print(f"   Response: {response[:300]}")
    else:
        print(f"   ⚠️  Response: {response[:300]}")
    
    ssh.close()

if __name__ == "__main__":
    main()

