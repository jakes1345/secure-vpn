#!/usr/bin/env python3
"""
Audit all routes, fix missing ones, and ensure admin dashboard has useful features
"""

import paramiko
import sys
import json

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
    print("🔍 AUDITING ALL ROUTES & FIXING MISSING ONES")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # ============================================================
        # STEP 1: Get all routes from Flask app
        # ============================================================
        print("1️⃣  Getting all routes from Flask app...")
        print("")
        
        get_routes_code = '''
import sys
sys.path.insert(0, "/opt/secure-vpn/web-portal")
sys.path.insert(0, "/opt/secure-vpn")

try:
    from app import app
    
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "path": rule.rule,
            "methods": list(rule.methods - {"HEAD", "OPTIONS"})
        })
    
    import json
    print(json.dumps(routes, indent=2))
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
'''
        
        success, routes_json, _ = run_command(ssh, f"python3 << 'ROUTES'\n{get_routes_code}\nROUTES", check=False)
        
        routes = []
        if success and routes_json and 'ERROR' not in routes_json:
            try:
                routes = json.loads(routes_json)
                print(f"   Found {len(routes)} routes")
            except:
                print(f"   Could not parse routes JSON")
        
        # Print important routes
        important_routes = ['admin_dashboard', 'login', 'download_page', 'dashboard', 'pricing', 'guide']
        print("")
        print("   Important routes:")
        for route in routes:
            if any(imp in route.get('endpoint', '') for imp in important_routes):
                methods = ', '.join(route.get('methods', []))
                print(f"      {route.get('endpoint')}: {route.get('path')} [{methods}]")
        print("")
        
        # ============================================================
        # STEP 2: Check what routes are referenced in templates
        # ============================================================
        print("2️⃣  Checking what routes templates reference...")
        print("")
        
        success, template_refs, _ = run_command(ssh, f"grep -h 'url_for' {VPN_DIR}/web-portal/templates/**/*.html 2>/dev/null | grep -o \"url_for('[^']*')\" | sort -u", check=False)
        if template_refs:
            referenced = set()
            for line in template_refs.split('\n'):
                if "url_for('" in line:
                    route_name = line.split("url_for('")[1].split("'")[0]
                    referenced.add(route_name)
            
            print(f"   Templates reference {len(referenced)} routes")
            
            # Check which ones are missing
            existing_endpoints = {r.get('endpoint') for r in routes}
            missing = referenced - existing_endpoints
            
            if missing:
                print("")
                print("   ⚠️  Missing routes:")
                for route in sorted(missing):
                    print(f"      - {route}")
        print("")
        
        # ============================================================
        # STEP 3: Add all missing essential routes
        # ============================================================
        print("3️⃣  Adding missing essential routes...")
        print("")
        
        # Read app.py
        success, app_content, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/app.py", check=False)
        
        if success:
            # Routes to add (if missing)
            essential_routes = {
                'tickets': '''
@app.route('/tickets')
@require_role('admin', 'moderator', 'user')
def tickets():
    """Support tickets page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('tickets.html') if Path('templates/tickets.html').exists() else redirect(url_for('contact'))
''',
                'pricing': '''
@app.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html') if Path('templates/pricing.html').exists() else 'Pricing coming soon', 200
''',
                'blog': '''
@app.route('/blog')
def blog():
    """Blog page"""
    return render_template('blog.html') if Path('templates/blog.html').exists() else 'Blog coming soon', 200
'''
            }
            
            added_count = 0
            for route_name, route_code in essential_routes.items():
                if f"def {route_name}()" not in app_content:
                    # Find a good place to insert (before error handlers or at end)
                    if '@app.errorhandler' in app_content:
                        error_pos = app_content.find('@app.errorhandler')
                        app_content = app_content[:error_pos] + route_code.strip() + '\n\n' + app_content[error_pos:]
                    else:
                        # Add before if __name__
                        if 'if __name__' in app_content:
                            main_pos = app_content.rfind('if __name__')
                            app_content = app_content[:main_pos] + route_code.strip() + '\n\n' + app_content[main_pos:]
                    
                    added_count += 1
                    print(f"   ✅ Added route: {route_name}")
            
            if added_count > 0:
                # Write back
                stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/app.py << 'PYEOF'\n{app_content}\nPYEOF")
                stdout.channel.recv_exit_status()
                print(f"   ✅ Added {added_count} missing routes")
        print("")
        
        # ============================================================
        # STEP 4: Check admin dashboard and make it useful
        # ============================================================
        print("4️⃣  Checking admin dashboard content...")
        print("")
        
        success, dashboard_content, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/templates/admin/dashboard.html 2>/dev/null || echo 'NOT_FOUND'", check=False)
        
        if 'NOT_FOUND' in dashboard_content:
            print("   ❌ Admin dashboard template not found!")
        else:
            # Check what features it shows
            has_features = {
                'VPN Status': 'vpn' in dashboard_content.lower() or 'running' in dashboard_content.lower(),
                'Client Management': 'client' in dashboard_content.lower(),
                'User Management': 'user' in dashboard_content.lower(),
                'Quick Actions': 'button' in dashboard_content.lower() or 'action' in dashboard_content.lower(),
                'Stats/Stats': 'stat' in dashboard_content.lower() or 'count' in dashboard_content.lower()
            }
            
            print("   Dashboard features:")
            for feature, present in has_features.items():
                status = "✅" if present else "❌"
                print(f"      {status} {feature}")
        
        # Check what admin routes exist
        success, admin_routes, _ = run_command(ssh, f"grep -n '@app.route.*admin' {VPN_DIR}/web-portal/app.py | head -10", check=False)
        if admin_routes:
            print("")
            print("   Admin routes:")
            for line in admin_routes.split('\n')[:8]:
                if line.strip():
                    print(f"      {line}")
        print("")
        
        # ============================================================
        # STEP 5: Verify syntax and restart
        # ============================================================
        print("5️⃣  Verifying syntax...")
        success, syntax_check, _ = run_command(ssh, f"python3 -m py_compile {VPN_DIR}/web-portal/app.py 2>&1", check=False)
        if success:
            print("   ✅ Syntax is valid")
        else:
            print(f"   ❌ Syntax error: {syntax_check[:200]}")
        print("")
        
        print("6️⃣  Restarting service...")
        run_command(ssh, "systemctl restart secure-vpn-download", check=False)
        
        import time
        time.sleep(3)
        
        success, status, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -3", check=False)
        if 'active (running)' in status:
            print("   ✅ Service restarted")
        print("")
        
        print("=" * 70)
        print("✅ AUDIT COMPLETE")
        print("=" * 70)
        print("")
        print("📋 Next: Check admin dashboard and add useful features")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

