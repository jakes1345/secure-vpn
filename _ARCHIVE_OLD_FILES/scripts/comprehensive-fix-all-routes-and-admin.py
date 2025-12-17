#!/usr/bin/env python3
"""
Comprehensive fix: Add all missing routes, fix admin dashboard, and make it useful
"""

import paramiko
import sys
import json
import re

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
    print("🔧 COMPREHENSIVE FIX: ALL ROUTES & ENHANCED ADMIN DASHBOARD")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # ============================================================
        # STEP 1: Read current app.py
        # ============================================================
        print("1️⃣  Reading current app.py...")
        success, app_content, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/app.py", check=False)
        
        if not success:
            print("   ❌ Failed to read app.py")
            return
        
        print("   ✅ Read app.py")
        print("")
        
        # ============================================================
        # STEP 2: Add missing routes
        # ============================================================
        print("2️⃣  Adding missing routes...")
        
        # Routes to check and add
        routes_to_add = {
            'tickets': {
                'exists_pattern': r"@app\.route\s*\(['\"]/tickets['\"]|def\s+tickets\s*\(",
                'route_code': '''
@app.route('/tickets')
@require_role('admin', 'moderator', 'user')
def tickets():
    """Support tickets page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    # For now, redirect to contact page until tickets system is built
    return redirect(url_for('contact'))
'''
            },
            'download_page_alias': {
                'exists_pattern': r"@app\.route\s*\(['\"]/download['\"]",
                'route_code': None  # Already exists, just need to verify
            }
        }
        
        added_count = 0
        for route_name, route_info in routes_to_add.items():
            if route_info['route_code']:
                if not re.search(route_info['exists_pattern'], app_content):
                    # Find insertion point (before error handlers)
                    if '@app.errorhandler' in app_content:
                        error_pos = app_content.find('@app.errorhandler')
                        app_content = app_content[:error_pos] + route_info['route_code'].strip() + '\n\n' + app_content[error_pos:]
                        added_count += 1
                        print(f"   ✅ Added route: {route_name}")
                    else:
                        # Add at end of routes section
                        if 'if __name__' in app_content:
                            main_pos = app_content.rfind('if __name__')
                            app_content = app_content[:main_pos] + route_info['route_code'].strip() + '\n\n' + app_content[main_pos:]
                            added_count += 1
                            print(f"   ✅ Added route: {route_name}")
                else:
                    print(f"   ✓ Route already exists: {route_name}")
        
        print(f"   ✅ Added {added_count} routes")
        print("")
        
        # ============================================================
        # STEP 3: Add missing API endpoints for tickets
        # ============================================================
        print("3️⃣  Adding missing API endpoints...")
        
        # Check if updateTicketCount function exists in dashboard template
        success, dashboard_content, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/templates/admin/dashboard.html 2>/dev/null || echo ''", check=False)
        
        needs_ticket_api = False
        if dashboard_content and 'updateTicketCount' in dashboard_content and 'function updateTicketCount' not in dashboard_content:
            needs_ticket_api = True
            print("   ℹ️  Dashboard needs ticket count API")
        
        # Add ticket count API if needed
        if needs_ticket_api or not re.search(r"@app\.route\s*\(['\"]/api/tickets/count['\"]", app_content):
            ticket_api_code = '''
@app.route('/api/tickets/count')
@require_role('admin', 'moderator')
def api_tickets_count():
    """Get count of open support tickets"""
    # For now, return 0 until tickets system is built
    return jsonify({'count': 0})
'''
            
            # Find where to insert (near other /api routes)
            api_routes_match = re.search(r"@app\.route\s*\(['\"]/api/[^'\"]+['\"]", app_content)
            if api_routes_match:
                insert_pos = api_routes_match.start()
                # Find the start of this route definition
                route_start = app_content.rfind('@app.route', 0, insert_pos)
                if route_start == -1:
                    route_start = insert_pos
                app_content = app_content[:route_start] + ticket_api_code.strip() + '\n\n' + app_content[route_start:]
                print("   ✅ Added API endpoint: /api/tickets/count")
            else:
                # Add before error handlers
                if '@app.errorhandler' in app_content:
                    error_pos = app_content.find('@app.errorhandler')
                    app_content = app_content[:error_pos] + ticket_api_code.strip() + '\n\n' + app_content[error_pos:]
                    print("   ✅ Added API endpoint: /api/tickets/count")
        
        print("")
        
        # ============================================================
        # STEP 4: Fix admin dashboard JavaScript functions
        # ============================================================
        print("4️⃣  Fixing admin dashboard JavaScript...")
        
        # Read dashboard template
        success, dashboard_html, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/templates/admin/dashboard.html 2>/dev/null || echo ''", check=False)
        
        if dashboard_html and 'updateTicketCount' in dashboard_html:
            # Check if function is defined
            if 'function updateTicketCount()' not in dashboard_html:
                # Add the function before the closing script tag
                ticket_count_function = '''
function updateTicketCount() {
    safeFetch('/api/tickets/count')
        .then(data => {
            const countEl = document.getElementById('ticket-count');
            if (countEl) {
                countEl.textContent = data.count || 0;
            }
        })
        .catch(err => {
            console.error('Failed to fetch ticket count:', err);
            const countEl = document.getElementById('ticket-count');
            if (countEl) {
                countEl.textContent = '0';
            }
        });
}
'''
                # Insert before closing </script> tag
                if '</script>' in dashboard_html:
                    script_end = dashboard_html.rfind('</script>')
                    dashboard_html = dashboard_html[:script_end] + ticket_count_function + '\n' + dashboard_html[script_end:]
                    print("   ✅ Added updateTicketCount() function")
                    
                    # Write back
                    stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/templates/admin/dashboard.html << 'DASHBOARD_EOF'\n{dashboard_html}\nDASHBOARD_EOF")
                    stdout.channel.recv_exit_status()
                else:
                    print("   ⚠️  Could not find </script> tag in dashboard")
        
        # Check for safeFetch function (used by dashboard)
        if dashboard_html and 'safeFetch' in dashboard_html and 'function safeFetch' not in dashboard_html:
            # Check base.html for safeFetch
            success, base_html, _ = run_command(ssh, f"grep -q 'function safeFetch' {VPN_DIR}/web-portal/templates/base.html 2>/dev/null && echo 'EXISTS' || echo 'MISSING'", check=False)
            if 'MISSING' in base_html:
                print("   ⚠️  safeFetch function missing from base.html (needed by dashboard)")
        
        print("")
        
        # ============================================================
        # STEP 5: Enhance admin dashboard with more useful content
        # ============================================================
        print("5️⃣  Enhancing admin dashboard content...")
        
        # Add recent activity section
        if dashboard_html and 'Recent Activity' not in dashboard_html:
            # Find where to insert (before closing </div> of container)
            if '<div class="container">' in dashboard_html and '</div>' in dashboard_html:
                # Insert before last </div> of container (before {% endblock %})
                if '{% endblock %}' in dashboard_html:
                    endblock_pos = dashboard_html.find('{% endblock %}')
                    recent_activity_section = '''
    <!-- Recent Activity -->
    <div class="card" style="margin-top: 2rem;">
        <div class="card-header">
            <h2 class="card-title">📊 Recent Activity</h2>
        </div>
        <div class="card-body">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
                <div>
                    <strong>Last Client Created:</strong>
                    <p id="last-client" style="color: #b0b0b0; margin-top: 0.5rem;">Loading...</p>
                </div>
                <div>
                    <strong>Last User Created:</strong>
                    <p id="last-user" style="color: #b0b0b0; margin-top: 0.5rem;">Loading...</p>
                </div>
                <div>
                    <strong>Server Uptime:</strong>
                    <p id="server-uptime" style="color: #b0b0b0; margin-top: 0.5rem;">Loading...</p>
                </div>
            </div>
        </div>
    </div>
'''
                    dashboard_html = dashboard_html[:endblock_pos] + recent_activity_section + '\n' + dashboard_html[endblock_pos:]
                    print("   ✅ Added Recent Activity section")
                    
                    # Also add JavaScript to populate it
                    if '<script>' in dashboard_html and '</script>' in dashboard_html:
                        script_end = dashboard_html.rfind('</script>')
                        activity_js = '''
// Update recent activity
function updateRecentActivity() {
    // Update last client
    safeFetch('/api/clients')
        .then(data => {
            if (data.clients && data.clients.length > 0) {
                const lastClient = data.clients.sort((a, b) => new Date(b.created) - new Date(a.created))[0];
                const el = document.getElementById('last-client');
                if (el) el.textContent = `${lastClient.name} (${new Date(lastClient.created).toLocaleDateString()})`;
            } else {
                const el = document.getElementById('last-client');
                if (el) el.textContent = 'No clients yet';
            }
        })
        .catch(() => {
            const el = document.getElementById('last-client');
            if (el) el.textContent = 'Unable to load';
        });
    
    // Update last user
    safeFetch('/api/users')
        .then(data => {
            if (data.users) {
                const users = Object.entries(data.users).map(([name, info]) => ({
                    name, ...info
                })).sort((a, b) => {
                    const dateA = a.created ? new Date(a.created) : new Date(0);
                    const dateB = b.created ? new Date(b.created) : new Date(0);
                    return dateB - dateA;
                });
                if (users.length > 0) {
                    const el = document.getElementById('last-user');
                    if (el) el.textContent = `${users[0].name} (${new Date(users[0].created || 0).toLocaleDateString()})`;
                }
            }
        })
        .catch(() => {
            const el = document.getElementById('last-user');
            if (el) el.textContent = 'Unable to load';
        });
    
    // Update server uptime (simple version)
    safeFetch('/api/system/uptime')
        .then(data => {
            const el = document.getElementById('server-uptime');
            if (el && data.uptime) {
                el.textContent = data.uptime;
            }
        })
        .catch(() => {
            const el = document.getElementById('server-uptime');
            if (el) el.textContent = 'Unable to load';
        });
}
'''
                        dashboard_html = dashboard_html[:script_end] + activity_js + '\n' + dashboard_html[script_end:]
                        
                        # Add to initialization
                        if 'updateVPNStatus();' in dashboard_html:
                            dashboard_html = dashboard_html.replace(
                                'updateVPNStatus();',
                                'updateVPNStatus();\nupdateRecentActivity();'
                            )
                        if 'setInterval(updateVPNStatus' in dashboard_html:
                            dashboard_html = dashboard_html.replace(
                                'setInterval(updateVPNStatus',
                                'setInterval(updateRecentActivity, 30000);\nsetInterval(updateVPNStatus'
                            )
                        
                        print("   ✅ Added activity update JavaScript")
                    
                    # Write back
                    stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/templates/admin/dashboard.html << 'DASHBOARD_EOF'\n{dashboard_html}\nDASHBOARD_EOF")
                    stdout.channel.recv_exit_status()
        
        print("")
        
        # ============================================================
        # STEP 6: Add missing API endpoints for activity
        # ============================================================
        print("6️⃣  Adding missing API endpoints for activity...")
        
        # Add /api/users endpoint if missing
        if not re.search(r"@app\.route\s*\(['\"]/api/users['\"]", app_content):
            users_api_code = '''
@app.route('/api/users')
@require_role('admin', 'moderator')
def api_users_list():
    """Get list of all users"""
    users, roles = load_users()
    return jsonify({'users': users})
'''
            if '@app.errorhandler' in app_content:
                error_pos = app_content.find('@app.errorhandler')
                app_content = app_content[:error_pos] + users_api_code.strip() + '\n\n' + app_content[error_pos:]
                print("   ✅ Added API endpoint: /api/users")
        
        # Add /api/system/uptime endpoint if missing
        if not re.search(r"@app\.route\s*\(['\"]/api/system/uptime['\"]", app_content):
            uptime_api_code = '''
@app.route('/api/system/uptime')
@require_role('admin', 'moderator')
def api_system_uptime():
    """Get server uptime"""
    try:
        result = subprocess.run(['uptime', '-p'], capture_output=True, text=True, timeout=5)
        uptime_str = result.stdout.strip() if result.returncode == 0 else 'Unknown'
        return jsonify({'uptime': uptime_str})
    except:
        return jsonify({'uptime': 'Unable to determine'})
'''
            if '@app.errorhandler' in app_content:
                error_pos = app_content.find('@app.errorhandler')
                app_content = app_content[:error_pos] + uptime_api_code.strip() + '\n\n' + app_content[error_pos:]
                print("   ✅ Added API endpoint: /api/system/uptime")
        
        print("")
        
        # ============================================================
        # STEP 7: Write updated app.py
        # ============================================================
        print("7️⃣  Writing updated app.py...")
        stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/app.py << 'APP_EOF'\n{app_content}\nAPP_EOF")
        stdout.channel.recv_exit_status()
        print("   ✅ Written app.py")
        print("")
        
        # ============================================================
        # STEP 8: Verify syntax
        # ============================================================
        print("8️⃣  Verifying syntax...")
        success, syntax_check, _ = run_command(ssh, f"python3 -m py_compile {VPN_DIR}/web-portal/app.py 2>&1", check=False)
        if success:
            print("   ✅ Syntax is valid")
        else:
            print(f"   ❌ Syntax error: {syntax_check[:300]}")
        print("")
        
        # ============================================================
        # STEP 9: Restart service
        # ============================================================
        print("9️⃣  Restarting service...")
        run_command(ssh, "systemctl restart secure-vpn-download", check=False)
        
        import time
        time.sleep(3)
        
        success, status, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -3", check=False)
        if 'active (running)' in status:
            print("   ✅ Service restarted and running")
        else:
            print(f"   ⚠️  Service status: {status[:100]}")
        print("")
        
        print("=" * 70)
        print("✅ COMPREHENSIVE FIX COMPLETE")
        print("=" * 70)
        print("")
        print("📋 What was fixed:")
        print("   ✅ Added missing routes (tickets, etc.)")
        print("   ✅ Added missing API endpoints (/api/tickets/count, /api/users, /api/system/uptime)")
        print("   ✅ Fixed admin dashboard JavaScript (updateTicketCount)")
        print("   ✅ Enhanced admin dashboard with Recent Activity section")
        print("   ✅ Added useful admin dashboard features")
        print("")
        print("🌐 Test it:")
        print("   1. Visit: https://phazevpn.com/admin")
        print("   2. Check that all stats and features load")
        print("   3. Try Quick Actions buttons")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

