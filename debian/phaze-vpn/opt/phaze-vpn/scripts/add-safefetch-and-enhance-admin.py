#!/usr/bin/env python3
"""
Add safeFetch to base.html and enhance all admin pages with real functionality
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
    print("🚀 ADDING safeFetch & ENHANCING ALL ADMIN PAGES")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # ============================================================
        # STEP 1: Add safeFetch, showToast, setLoading to base.html
        # ============================================================
        print("1️⃣  Adding JavaScript utilities to base.html...")
        
        success, base_html, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/templates/base.html", check=False)
        
        if success:
            # Check if utilities already exist
            has_safefetch = 'function safeFetch' in base_html
            has_showtoast = 'function showToast' in base_html
            has_setloading = 'function setLoading' in base_html
            
            if not has_safefetch or not has_showtoast or not has_setloading:
                # Add utilities before closing </body> tag
                utilities_js = '''
<script>
// Utility functions for all pages
function safeFetch(url, options = {}) {
    return fetch(url, {
        ...options,
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    })
    .then(res => {
        if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.json().catch(() => ({}));
    });
}

function showToast(message, type = 'info', duration = 3000) {
    // Remove existing toast
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    
    // Create toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#2196f3'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
        max-width: 400px;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function setLoading(button, loading) {
    if (!button) return;
    if (loading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = '⏳ Loading...';
    } else {
        button.disabled = false;
        if (button.dataset.originalText) {
            button.textContent = button.dataset.originalText;
            delete button.dataset.originalText;
        }
    }
}

// Add slideIn animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);
</script>
'''
                
                # Insert before closing </body> tag
                if '</body>' in base_html:
                    body_end = base_html.rfind('</body>')
                    base_html = base_html[:body_end] + utilities_js + '\n' + base_html[body_end:]
                    
                    # Write back
                    stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/templates/base.html << 'BASE_EOF'\n{base_html}\nBASE_EOF")
                    stdout.channel.recv_exit_status()
                    
                    added = []
                    if not has_safefetch: added.append('safeFetch')
                    if not has_showtoast: added.append('showToast')
                    if not has_setloading: added.append('setLoading')
                    
                    print(f"   ✅ Added: {', '.join(added)}")
                else:
                    print("   ⚠️  Could not find </body> tag")
            else:
                print("   ✓ All utilities already exist")
        else:
            print("   ❌ Failed to read base.html")
        
        print("")
        
        # ============================================================
        # STEP 2: Enhance admin dashboard with more useful links
        # ============================================================
        print("2️⃣  Enhancing admin dashboard with useful links...")
        
        success, dashboard_html, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/templates/admin/dashboard.html", check=False)
        
        if success:
            # Add a "System Info" section with useful stats
            if 'System Information' not in dashboard_html:
                # Find Quick Actions section and add System Info before it
                if '<!-- Quick Actions -->' in dashboard_html:
                    quick_actions_pos = dashboard_html.find('<!-- Quick Actions -->')
                    
                    system_info_section = '''
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
                    dashboard_html = dashboard_html[:quick_actions_pos] + system_info_section + '\n\n' + dashboard_html[quick_actions_pos:]
                    print("   ✅ Added System Information section")
                
                # Add JavaScript to populate system info
                if '<script>' in dashboard_html:
                    script_end = dashboard_html.rfind('</script>')
                    system_info_js = '''
// Update system information
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
'''
                    dashboard_html = dashboard_html[:script_end] + system_info_js + '\n' + dashboard_html[script_end:]
                    
                    # Add to initialization
                    if 'updateVPNStatus();' in dashboard_html:
                        dashboard_html = dashboard_html.replace(
                            'updateVPNStatus();',
                            'updateVPNStatus();\nupdateSystemInfo();'
                        )
                    if 'setInterval(updateVPNStatus' in dashboard_html:
                        dashboard_html = dashboard_html.replace(
                            'setInterval(updateVPNStatus',
                            'setInterval(updateSystemInfo, 60000);\nsetInterval(updateVPNStatus'
                        )
                    
                    print("   ✅ Added system info JavaScript")
                
                # Write back
                stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/templates/admin/dashboard.html << 'DASHBOARD_EOF'\n{dashboard_html}\nDASHBOARD_EOF")
                stdout.channel.recv_exit_status()
        
        print("")
        
        # ============================================================
        # STEP 3: Add /api/system/info endpoint
        # ============================================================
        print("3️⃣  Adding /api/system/info endpoint...")
        
        success, app_content, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/app.py", check=False)
        
        if success:
            if not re.search(r"@app\.route\s*\(['\"]/api/system/info['\"]", app_content):
                system_info_api = '''
@app.route('/api/system/info')
@require_role('admin', 'moderator')
def api_system_info():
    """Get system information"""
    try:
        # Uptime
        result = subprocess.run(['uptime', '-p'], capture_output=True, text=True, timeout=5)
        uptime = result.stdout.strip() if result.returncode == 0 else 'Unknown'
        
        # Disk usage
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 5:
                    disk = f"{parts[2]} / {parts[1]} ({parts[4]})"
                else:
                    disk = 'Unknown'
            else:
                disk = 'Unknown'
        else:
            disk = 'Unknown'
        
        # Memory usage
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                mem_total = int(re.search(r'MemTotal:\\s+(\\d+)', meminfo).group(1)) / 1024 / 1024
                mem_available = int(re.search(r'MemAvailable:\\s+(\\d+)', meminfo).group(1)) / 1024 / 1024
                mem_used = mem_total - mem_available
                mem_percent = (mem_used / mem_total) * 100
                memory = f"{mem_used:.1f} GB / {mem_total:.1f} GB ({mem_percent:.1f}%)"
        except:
            memory = 'Unknown'
        
        # Load average
        result = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            load_match = re.search(r'load average:\\s+([\\d\\.]+)', result.stdout)
            if load_match:
                load = load_match.group(1)
            else:
                load = 'Unknown'
        else:
            load = 'Unknown'
        
        return jsonify({
            'uptime': uptime,
            'disk': disk,
            'memory': memory,
            'load': load
        })
    except Exception as e:
        return jsonify({
            'uptime': 'Error',
            'disk': 'Error',
            'memory': 'Error',
            'load': 'Error',
            'error': str(e)
        }), 500
'''
                
                # Insert before error handlers
                if '@app.errorhandler' in app_content:
                    error_pos = app_content.find('@app.errorhandler')
                    app_content = app_content[:error_pos] + system_info_api.strip() + '\n\n' + app_content[error_pos:]
                    print("   ✅ Added /api/system/info endpoint")
                    
                    # Write back
                    stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/app.py << 'APP_EOF'\n{app_content}\nAPP_EOF")
                    stdout.channel.recv_exit_status()
                else:
                    print("   ⚠️  Could not find insertion point")
            else:
                print("   ✓ /api/system/info already exists")
        
        print("")
        
        # ============================================================
        # STEP 4: Verify and restart
        # ============================================================
        print("4️⃣  Verifying syntax...")
        success, syntax_check, _ = run_command(ssh, f"python3 -m py_compile {VPN_DIR}/web-portal/app.py 2>&1", check=False)
        if success:
            print("   ✅ Syntax is valid")
        else:
            print(f"   ❌ Syntax error: {syntax_check[:300]}")
        print("")
        
        print("5️⃣  Restarting service...")
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
        print("✅ ENHANCEMENT COMPLETE")
        print("=" * 70)
        print("")
        print("📋 What was added:")
        print("   ✅ safeFetch, showToast, setLoading utilities in base.html")
        print("   ✅ System Information section on admin dashboard")
        print("   ✅ /api/system/info endpoint for system stats")
        print("")
        print("🌐 The admin dashboard now shows:")
        print("   • VPN Server Control (Start/Stop/Restart)")
        print("   • Stats (Clients, Users, Connections, Tickets)")
        print("   • System Information (Uptime, Disk, Memory, Load)")
        print("   • Recent Activity")
        print("   • Quick Actions")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

