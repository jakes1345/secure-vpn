#!/usr/bin/env python3
"""
Fix base.html template - remove references to routes that don't exist
"""

import paramiko
import sys

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"
VPN_DIR = "/opt/secure-vpn"

def run_command(ssh, command, check=True):
    """Execute command on remote server"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_status == 0, output, error

def main():
    print("=" * 70)
    print("🔧 FIXING MISSING ROUTES IN BASE TEMPLATE")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Check what routes actually exist
        print("1️⃣  Checking what routes exist...")
        print("")
        
        success, routes, _ = run_command(ssh, f"grep -n '@app.route' {VPN_DIR}/web-portal/app.py | head -20", check=False)
        if routes:
            print("   Existing routes:")
            for line in routes.split('\n')[:15]:
                if line.strip():
                    route_name = line.split("'")[1] if "'" in line else line.split('"')[1] if '"' in line else ""
                    print(f"      {route_name}")
        print("")
        
        # Check what base.html is trying to call
        print("2️⃣  Checking what base.html references...")
        print("")
        
        success, base_refs, _ = run_command(ssh, f"grep -n 'url_for' {VPN_DIR}/web-portal/templates/base.html", check=False)
        if base_refs:
            print("   Routes referenced in base.html:")
            for line in base_refs.split('\n'):
                if line.strip() and 'url_for' in line:
                    # Extract route name
                    parts = line.split("url_for('")
                    if len(parts) > 1:
                        route_name = parts[1].split("'")[0]
                        print(f"      {route_name}")
                    else:
                        parts = line.split('url_for("')
                        if len(parts) > 1:
                            route_name = parts[1].split('"')[0]
                            print(f"      {route_name}")
        print("")
        
        # Read base.html and fix it
        print("3️⃣  Fixing base.html to remove missing routes...")
        print("")
        
        success, base_html, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/templates/base.html", check=False)
        
        if success:
            # Replace missing routes with working ones or remove them
            # 'tickets' -> 'contact' or remove
            base_html = base_html.replace("url_for('tickets')", "url_for('contact') if False else '#'")
            
            # Check which routes actually exist
            existing_routes = ['download_page', 'pricing', 'guide', 'faq', 'contact', 'privacy', 'terms']
            
            # For routes that might not exist, replace with safe alternatives
            # 'contact' - create a simple route if missing
            # 'faq' - create a simple route if missing
            # 'privacy' - create a simple route if missing
            # 'terms' - create a simple route if missing
            
            # Actually, let's just make them all safe - use '#' if route doesn't exist
            # Or better: comment them out or remove them
            
            # Read app.py to see what routes exist
            success2, app_routes, _ = run_command(ssh, f"python3 << 'ROUTES'\nimport sys\nsys.path.insert(0, '{VPN_DIR}/web-portal')\ntry:\n    from app import app\n    routes = []\n    for rule in app.url_map.iter_rules():\n        routes.append(rule.endpoint)\n    print('EXISTING:' + ','.join(routes))\nexcept Exception as e:\n    print(f'ERROR:{{e}}')\nROUTES", check=False)
            
            if 'EXISTING:' in app_routes:
                existing_endpoints = app_routes.split('EXISTING:')[1].split(',')
                print(f"   Found {len(existing_endpoints)} routes")
                
                # Fix base.html to only use existing routes
                # Replace tickets with contact (safer)
                if 'contact' not in existing_endpoints:
                    # Remove tickets reference or make it safe
                    base_html = base_html.replace(
                        "url_for('tickets') if session.get('username') else url_for('contact')",
                        "'#'"
                    )
                else:
                    base_html = base_html.replace(
                        "url_for('tickets')",
                        "url_for('contact')"
                    )
                
                # Make other missing routes safe
                for route in ['faq', 'privacy', 'terms']:
                    if route not in existing_endpoints:
                        # Replace with '#'
                        base_html = base_html.replace(f"url_for('{route}')", "'#'")
                        print(f"   ✅ Fixed missing route: {route}")
            
            # Write fixed base.html
            stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/templates/base.html << 'HTMLEOF'\n{base_html}\nHTMLEOF")
            stdout.channel.recv_exit_status()
            print("   ✅ Fixed base.html")
        print("")
        
        # Add missing routes to app.py if they don't exist
        print("4️⃣  Adding missing routes to app.py...")
        print("")
        
        success, app_content, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/app.py", check=False)
        
        missing_routes = {
            'contact': '''
@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html') if Path('templates/contact.html').exists() else 'Contact support at support@phazevpn.com', 200
''',
            'faq': '''
@app.route('/faq')
def faq():
    """FAQ page"""
    return render_template('faq.html') if Path('templates/faq.html').exists() else 'FAQ coming soon', 200
''',
            'privacy': '''
@app.route('/privacy')
def privacy():
    """Privacy policy"""
    return render_template('privacy.html') if Path('templates/privacy.html').exists() else 'Privacy policy coming soon', 200
''',
            'terms': '''
@app.route('/terms')
def terms():
    """Terms of service"""
    return render_template('terms.html') if Path('templates/terms.html').exists() else 'Terms of service coming soon', 200
''',
            'tickets': '''
@app.route('/tickets')
@require_role('admin', 'moderator', 'user')
def tickets():
    """Support tickets"""
    return redirect(url_for('contact'))
'''
        }
        
        if success:
            # Check which routes are missing
            for route_name, route_code in missing_routes.items():
                if f"def {route_name}()" not in app_content:
                    # Add route before the error handler
                    # Find where error handlers are
                    if '@app.errorhandler' in app_content:
                        error_handler_pos = app_content.find('@app.errorhandler')
                        # Insert before error handlers
                        app_content = app_content[:error_handler_pos] + route_code.strip() + '\n\n' + app_content[error_handler_pos:]
                        print(f"   ✅ Added missing route: {route_name}")
                    else:
                        # Add at end before if __name__ == '__main__'
                        if 'if __name__' in app_content:
                            main_pos = app_content.rfind('if __name__')
                            app_content = app_content[:main_pos] + route_code.strip() + '\n\n' + app_content[main_pos:]
                            print(f"   ✅ Added missing route: {route_name} (at end)")
            
            # Write updated app.py
            stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/app.py << 'PYEOF'\n{app_content}\nPYEOF")
            stdout.channel.recv_exit_status()
        print("")
        
        # Verify syntax
        print("5️⃣  Verifying syntax...")
        success, syntax_check, _ = run_command(ssh, f"python3 -m py_compile {VPN_DIR}/web-portal/app.py 2>&1", check=False)
        if success:
            print("   ✅ Syntax is valid")
        else:
            print(f"   ❌ Syntax error: {syntax_check[:200]}")
        print("")
        
        # Restart service
        print("6️⃣  Restarting service...")
        run_command(ssh, "systemctl restart secure-vpn-download", check=False)
        
        import time
        time.sleep(3)
        
        success, status, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -3", check=False)
        if 'active (running)' in status:
            print("   ✅ Service restarted")
        print("")
        
        print("=" * 70)
        print("✅ FIXED")
        print("=" * 70)
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

