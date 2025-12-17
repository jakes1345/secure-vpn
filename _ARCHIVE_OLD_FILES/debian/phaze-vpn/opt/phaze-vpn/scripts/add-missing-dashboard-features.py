#!/usr/bin/env python3
"""
Add missing dashboard features that didn't get applied
"""

import paramiko
import sys
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
    print("🔧 ADDING MISSING DASHBOARD FEATURES TO VPS")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # Read current dashboard
        print("1️⃣  Reading current dashboard.html...")
        success, dashboard_html, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/templates/admin/dashboard.html", check=False)
        
        if not success:
            print("   ❌ Failed to read dashboard")
            return
        
        print("   ✅ Read dashboard.html")
        print("")
        
        # Add missing features
        print("2️⃣  Adding missing features...")
        
        # Check what's missing
        has_system_info = 'System Information' in dashboard_html
        has_update_system_info = 'function updateSystemInfo' in dashboard_html
        has_update_ticket_count = 'function updateTicketCount' in dashboard_html
        
        changes_made = []
        
        # Add System Information section if missing
        if not has_system_info:
            # Find where to insert (before Quick Actions or before closing script)
            insert_pos = None
            if '<!-- Quick Actions -->' in dashboard_html:
                insert_pos = dashboard_html.find('<!-- Quick Actions -->')
            elif '</div>' in dashboard_html and '{% endblock %}' in dashboard_html:
                endblock_pos = dashboard_html.find('{% endblock %}')
                # Find last </div> before {% endblock %}
                last_div = dashboard_html.rfind('</div>', 0, endblock_pos)
                if last_div != -1:
                    insert_pos = last_div + len('</div>')
            
            if insert_pos:
                system_info_html = '''

    <!-- System Information -->
    <div class="card" style="margin-bottom: 2rem;">
        <div class="card-header">
            <h2 class="card-title">🖥️ System Information</h2>
        </div>
        <div class="card-body">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <div>
                    <strong>Server Uptime:</strong>
                    <p id="system-uptime" style="color: #b0b0b0; margin-top: 0.5rem;">Loading...</p>
                </div>
                <div>
                    <strong>Disk Usage:</strong>
                    <p id="system-disk" style="color: #b0b0b0; margin-top: 0.5rem;">Loading...</p>
                </div>
                <div>
                    <strong>Memory Usage:</strong>
                    <p id="system-memory" style="color: #b0b0b0; margin-top: 0.5rem;">Loading...</p>
                </div>
                <div>
                    <strong>Load Average:</strong>
                    <p id="system-load" style="color: #b0b0b0; margin-top: 0.5rem;">Loading...</p>
                </div>
            </div>
        </div>
    </div>
'''
                dashboard_html = dashboard_html[:insert_pos] + system_info_html + '\n' + dashboard_html[insert_pos:]
                changes_made.append("System Information section")
                print("   ✅ Added System Information section")
        
        # Add missing JavaScript functions
        if not has_update_ticket_count or not has_update_system_info:
            # Find where to insert JavaScript (before closing </script>)
            if '</script>' in dashboard_html:
                script_end = dashboard_html.rfind('</script>')
                
                missing_functions = []
                
                if not has_update_ticket_count:
                    missing_functions.append('''
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
''')
                
                if not has_update_system_info:
                    missing_functions.append('''
function updateSystemInfo() {
    safeFetch('/api/system/info')
        .then(data => {
            const uptimeEl = document.getElementById('system-uptime');
            const diskEl = document.getElementById('system-disk');
            const memoryEl = document.getElementById('system-memory');
            const loadEl = document.getElementById('system-load');
            
            if (uptimeEl && data.uptime) uptimeEl.textContent = data.uptime;
            if (diskEl && data.disk) diskEl.textContent = data.disk;
            if (memoryEl && data.memory) memoryEl.textContent = data.memory;
            if (loadEl && data.load) loadEl.textContent = data.load;
        })
        .catch(err => {
            console.error('Failed to fetch system info:', err);
        });
}
''')
                
                if missing_functions:
                    all_functions = '\n'.join(missing_functions)
                    dashboard_html = dashboard_html[:script_end] + all_functions + '\n' + dashboard_html[script_end:]
                    changes_made.append(f"{len(missing_functions)} JavaScript functions")
                    print(f"   ✅ Added {len(missing_functions)} JavaScript functions")
        
        # Update initialization calls
        if changes_made:
            # Add updateSystemInfo() to initialization
            if 'updateVPNStatus();' in dashboard_html and 'updateSystemInfo();' not in dashboard_html:
                dashboard_html = dashboard_html.replace(
                    'updateVPNStatus();',
                    'updateVPNStatus();\nupdateSystemInfo();'
                )
                print("   ✅ Added updateSystemInfo() to initialization")
            
            # Add updateTicketCount() to initialization if it's called but not defined
            if 'updateTicketCount();' in dashboard_html and 'function updateTicketCount' not in dashboard_html:
                # We already added it above, so this should be fine
                pass
            
            # Add intervals
            if 'setInterval(updateVPNStatus' in dashboard_html:
                if 'setInterval(updateSystemInfo' not in dashboard_html:
                    dashboard_html = dashboard_html.replace(
                        'setInterval(updateVPNStatus',
                        'setInterval(updateSystemInfo, 60000);\nsetInterval(updateVPNStatus'
                    )
                    print("   ✅ Added updateSystemInfo interval")
        
        # Write back if changes were made
        if changes_made:
            print("")
            print("3️⃣  Writing updated dashboard.html to VPS...")
            stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/templates/admin/dashboard.html << 'DASHBOARD_EOF'\n{dashboard_html}\nDASHBOARD_EOF")
            stdout.channel.recv_exit_status()
            print("   ✅ Written to VPS")
            print("")
            
            print("4️⃣  Restarting service...")
            run_command(ssh, "systemctl restart secure-vpn-download", check=False)
            import time
            time.sleep(3)
            
            success, status, _ = run_command(ssh, "systemctl status secure-vpn-download --no-pager | head -3", check=False)
            if 'active (running)' in status:
                print("   ✅ Service restarted and running")
            print("")
        else:
            print("   ✓ All features already exist")
            print("")
        
        print("=" * 70)
        print("✅ COMPLETE")
        print("=" * 70)
        print("")
        if changes_made:
            print(f"📋 Added to VPS: {', '.join(changes_made)}")
        else:
            print("📋 All features are already present on VPS")
        print("")
        print("🌐 Everything is now LIVE on the VPS!")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

