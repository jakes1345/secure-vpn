#!/usr/bin/env python3
"""
Add client registration system to VPS web portal
Clients register when they install, VPS tracks them
"""

import paramiko
import subprocess

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("="*80)
    print("🔧 ADDING CLIENT REGISTRATION SYSTEM")
    print("="*80)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # Read current app.py
    sftp = ssh.open_sftp()
    try:
        with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'r') as f:
            app_content = f.read().decode('utf-8')
    except Exception as e:
        print(f"   ❌ Failed to read app.py: {e}")
        sftp.close()
        ssh.close()
        return
    
    # Check if registration endpoints already exist
    if '/api/v1/client/register' in app_content:
        print("   ✅ Registration endpoints already exist")
        sftp.close()
        ssh.close()
        return
    
    # Add registration endpoints
    registration_code = '''

# ============================================
# CLIENT REGISTRATION API
# ============================================

@app.route('/api/v1/client/register', methods=['POST'])
def register_client():
    """Register a new client with the VPS"""
    try:
        data = request.json
        client_id = data.get('client_id')  # Unique client identifier (MAC address or generated UUID)
        hostname = data.get('hostname', 'unknown')
        os_type = data.get('os', 'unknown')
        os_version = data.get('os_version', 'unknown')
        client_version = data.get('version', '1.0.0')
        username = data.get('username', '')  # User account on VPS
        password = data.get('password', '')  # User password for authentication
        
        if not client_id:
            return jsonify({'error': 'client_id required'}), 400
        
        # Authenticate user if credentials provided
        user_authenticated = False
        if username and password:
            users_file = Path('users.json')
            if users_file.exists():
                with open(users_file, 'r') as f:
                    users_data = json.load(f)
                    user = users_data.get('users', {}).get(username)
                    if user:
                        if bcrypt.checkpw(password.encode(), user['password'].encode()):
                            user_authenticated = True
        
        # Load registered clients
        clients_file = Path('registered_clients.json')
        if clients_file.exists():
            with open(clients_file, 'r') as f:
                clients_data = json.load(f)
        else:
            clients_data = {'clients': {}}
        
        # Check if client already registered
        if client_id in clients_data['clients']:
            client = clients_data['clients'][client_id]
            client['last_seen'] = datetime.now().isoformat()
            client['hostname'] = hostname
            client['os'] = os_type
            client['os_version'] = os_version
            client['version'] = client_version
            # Update subscription if user authenticated
            if user_authenticated:
                client['username'] = username
        else:
            # New client registration
            client = {
                'client_id': client_id,
                'hostname': hostname,
                'os': os_type,
                'os_version': os_version,
                'version': client_version,
                'registered_at': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'username': username if user_authenticated else None,
                'subscription': {
                    'status': 'active' if user_authenticated else 'pending',
                    'expires_at': None,
                    'plan': 'free' if user_authenticated else None
                },
                'vpn_config': None,  # Will be assigned when client config created
                'status': 'registered'
            }
            clients_data['clients'][client_id] = client
        
        # Save updated clients
        with open(clients_file, 'w') as f:
            json.dump(clients_data, f, indent=2)
        
        return jsonify({
            'success': True,
            'client_id': client_id,
            'subscription': client['subscription'],
            'vpn_config_url': f"/download/{client.get('vpn_config')}" if client.get('vpn_config') else None,
            'message': 'Client registered successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/client/status', methods=['GET'])
@login_required
def get_client_status():
    """Get client status and subscription info"""
    try:
        client_id = request.args.get('client_id')
        if not client_id:
            return jsonify({'error': 'client_id required'}), 400
        
        clients_file = Path('registered_clients.json')
        if not clients_file.exists():
            return jsonify({'error': 'No clients registered'}), 404
        
        with open(clients_file, 'r') as f:
            clients_data = json.load(f)
        
        client = clients_data.get('clients', {}).get(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        return jsonify({
            'client_id': client_id,
            'subscription': client.get('subscription', {}),
            'vpn_config': client.get('vpn_config'),
            'status': client.get('status', 'unknown'),
            'last_seen': client.get('last_seen')
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/client/checkin', methods=['POST'])
def client_checkin():
    """Client periodic check-in to update status"""
    try:
        data = request.json
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({'error': 'client_id required'}), 400
        
        clients_file = Path('registered_clients.json')
        if clients_file.exists():
            with open(clients_file, 'r') as f:
                clients_data = json.load(f)
            
            if client_id in clients_data.get('clients', {}):
                clients_data['clients'][client_id]['last_seen'] = datetime.now().isoformat()
                
                with open(clients_file, 'w') as f:
                    json.dump(clients_data, f, indent=2)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/clients/list', methods=['GET'])
@admin_required
def list_registered_clients():
    """List all registered clients (admin only)"""
    try:
        clients_file = Path('registered_clients.json')
        if not clients_file.exists():
            return jsonify({'clients': []}), 200
        
        with open(clients_file, 'r') as f:
            clients_data = json.load(f)
        
        clients = []
        for client_id, client in clients_data.get('clients', {}).items():
            clients.append({
                'client_id': client_id,
                'hostname': client.get('hostname'),
                'os': client.get('os'),
                'version': client.get('version'),
                'username': client.get('username'),
                'subscription': client.get('subscription', {}),
                'registered_at': client.get('registered_at'),
                'last_seen': client.get('last_seen'),
                'status': client.get('status')
            })
        
        return jsonify({'clients': clients}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
'''
    
    # Find where to insert (before the last line or at end of routes)
    if '@app.route' in app_content:
        # Insert before the if __name__ block
        if 'if __name__ == "__main__":' in app_content:
            insert_pos = app_content.rfind('if __name__ == "__main__":')
            new_content = app_content[:insert_pos] + registration_code + '\n' + app_content[insert_pos:]
        else:
            new_content = app_content + registration_code
    else:
        new_content = app_content + registration_code
    
    # Write back
    try:
        with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'w') as f:
            f.write(new_content.encode('utf-8'))
        print("   ✅ Added registration endpoints")
    except Exception as e:
        print(f"   ❌ Failed to write: {e}")
        sftp.close()
        ssh.close()
        return
    
    sftp.close()
    
    # Restart web portal
    print("\n🔄 Restarting web portal...")
    stdin, stdout, stderr = ssh.exec_command("systemctl restart phazevpn-portal")
    stdout.channel.recv_exit_status()
    print("   ✅ Web portal restarted")
    
    print("\n" + "="*80)
    print("✅ CLIENT REGISTRATION SYSTEM ADDED")
    print("="*80)
    print("\n📊 API Endpoints:")
    print("   POST /api/v1/client/register - Register new client")
    print("   GET  /api/v1/client/status - Get client status")
    print("   POST /api/v1/client/checkin - Client check-in")
    print("   GET  /api/v1/clients/list - List all clients (admin)")
    
    ssh.close()

if __name__ == "__main__":
    main()

