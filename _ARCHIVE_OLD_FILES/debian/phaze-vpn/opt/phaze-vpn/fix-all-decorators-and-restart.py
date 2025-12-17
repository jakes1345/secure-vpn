#!/usr/bin/env python3
"""
Fix all decorator errors and restart services properly
"""

import paramiko
import re

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

def main():
    print("="*80)
    print("🔧 FIXING ALL DECORATORS AND RESTARTING")
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
    try:
        with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'r') as f:
            content = f.read().decode('utf-8')
    except Exception as e:
        print(f"   ❌ Error: {e}")
        sftp.close()
        ssh.close()
        return
    
    # Fix 1: Add admin_required decorator
    if 'def admin_required' not in content:
        # Add after require_permission
        require_permission_end = content.find('    return decorator\n', content.find('def require_permission'))
        if require_permission_end > 0:
            admin_required_code = '''

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        role = session.get('role')
        if role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function
'''
            content = content[:require_permission_end + 20] + admin_required_code + content[require_permission_end + 20:]
            print("   ✅ Added admin_required decorator")
    
    # Fix 2: Replace @login_required with @require_api_auth for API endpoints that don't need admin
    # Actually, let's keep login_required but make sure it exists
    
    # Fix 3: Replace @admin_required with @require_role('admin') for consistency
    # Or keep admin_required - let's just make sure it's defined
    
    # Write back
    with sftp.open('/opt/phaze-vpn/web-portal/app.py', 'w') as f:
        f.write(content.encode('utf-8'))
    sftp.close()
    
    # Test
    print("\n🔍 Testing app.py...")
    stdin, stdout, stderr = ssh.exec_command('cd /opt/phaze-vpn/web-portal && python3 -c "import app; print(\"OK\")" 2>&1')
    output = stdout.read().decode()
    if 'OK' in output:
        print("   ✅ App.py imports successfully!")
    else:
        print(f"   ⚠️  Still has errors: {output[:500]}")
        # Try to find the exact line
        if 'line' in output.lower():
            line_match = re.search(r'line (\d+)', output)
            if line_match:
                line_num = line_match.group(1)
                stdin, stdout, stderr = ssh.exec_command(f'sed -n "{int(line_num)-2},{int(line_num)+2}p" /opt/phaze-vpn/web-portal/app.py')
                print(f"   Line {line_num} context:")
                print(stdout.read().decode())
    
    # Kill all processes and restart
    print("\n🔄 Restarting portal...")
    stdin, stdout, stderr = ssh.exec_command('''
    systemctl stop phazevpn-portal
    pkill -9 -f gunicorn
    pkill -9 -f 'app.py'
    fuser -k 5000/tcp 2>/dev/null || true
    sleep 2
    systemctl start phazevpn-portal
    sleep 5
    systemctl status phazevpn-portal --no-pager | head -10
    ''')
    print(stdout.read().decode())
    
    # Test website
    print("\n🌐 Testing website...")
    stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:5000/ 2>&1')
    status = stdout.read().decode().strip()
    if '200' in status or '302' in status:
        print(f"   ✅ Website responding: {status}")
    else:
        print(f"   ❌ Website error: {status}")
        # Get error details
        stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:5000/ 2>&1 | head -5')
        print(f"   Error: {stdout.read().decode()[:200]}")
    
    ssh.close()

if __name__ == "__main__":
    main()

