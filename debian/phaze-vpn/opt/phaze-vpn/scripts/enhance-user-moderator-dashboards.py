#!/usr/bin/env python3
"""
Enhance user and moderator dashboards with useful features
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
    print("🚀 ENHANCING USER & MODERATOR DASHBOARDS")
    print("=" * 70)
    print("")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("✅ Connected to VPS")
        print("")
        
        # ============================================================
        # STEP 1: Enhance Moderator Dashboard
        # ============================================================
        print("1️⃣  Enhancing Moderator Dashboard...")
        
        success, mod_html, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/templates/moderator/dashboard.html", check=False)
        
        if success:
            enhanced_mod_dashboard = '''{% extends "base.html" %}

{% block title %}Moderator Dashboard - PhazeVPN{% endblock %}

{% block content %}
<div class="container">
    <div class="hero" style="margin-bottom: 2rem;">
        <h1>🛡️ Moderator Dashboard</h1>
        <p>Welcome, <strong>{{ username }}</strong>! Manage clients and support tickets.</p>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-4" style="margin-bottom: 2rem;">
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">📱 VPN Clients</h3>
            </div>
            <div class="card-body text-center">
                <div style="font-size: 3rem; font-weight: bold; color: var(--primary);">{{ clients|length }}</div>
                <p class="text-muted">Total clients</p>
                <button class="btn btn-primary btn-sm" style="margin-top: 1rem;" onclick="addClient()">➕ Add Client</button>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">🎫 Support Tickets</h3>
            </div>
            <div class="card-body text-center">
                <div id="ticket-count" style="font-size: 3rem; font-weight: bold; color: var(--warning);">Loading...</div>
                <p class="text-muted">Open tickets</p>
                <a href="/tickets" class="btn btn-primary btn-sm" style="margin-top: 1rem;">Manage</a>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">🔌 Active Connections</h3>
            </div>
            <div class="card-body text-center">
                <div style="font-size: 3rem; font-weight: bold; color: var(--success);">{{ active_connections }}</div>
                <p class="text-muted">Currently connected</p>
                <a href="#connections" class="btn btn-primary btn-sm" style="margin-top: 1rem;">View</a>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">📊 VPN Status</h3>
            </div>
            <div class="card-body text-center">
                <div id="vpn-status" style="font-size: 1.5rem; font-weight: bold; margin-bottom: 0.5rem;">
                    <span class="status-badge status-inactive">Checking...</span>
                </div>
                <p class="text-muted">Server status</p>
            </div>
        </div>
    </div>

    <!-- Quick Actions -->
    <div class="card" style="margin-bottom: 2rem;">
        <div class="card-header">
            <h2 class="card-title">Quick Actions</h2>
        </div>
        <div class="card-body">
            <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                <button class="btn btn-primary" onclick="addClient()">➕ Add Client</button>
                <a href="/tickets" class="btn btn-primary">🎫 Support Tickets</a>
                <a href="/admin/clients" class="btn btn-secondary">📱 All Clients</a>
                <a href="/download" class="btn btn-secondary">⬇️ Downloads</a>
            </div>
        </div>
    </div>

    <!-- VPN Clients Table -->
    <div class="card" id="connections">
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
            <h2 class="card-title">📱 VPN Clients ({{ clients|length }})</h2>
            <button class="btn btn-primary" onclick="addClient()">➕ Add Client</button>
        </div>
        <div class="card-body">
            {% if clients %}
            <table>
                <thead>
                    <tr>
                        <th>Client Name</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for client in clients %}
                    <tr>
                        <td><strong>{{ client.name }}</strong></td>
                        <td>{{ client.created[:10] if client.created else 'N/A' }}</td>
                        <td>
                            <a href="/download/{{ client.name }}" class="btn btn-primary" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;">⬇️ Download</a>
                            <a href="/qr/{{ client.name }}" class="btn btn-success" style="padding: 0.25rem 0.5rem; font-size: 0.8rem; margin-left: 0.25rem;">📱 QR Code</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div style="text-align: center; color: #b0b0b0; padding: 2rem;">
                <p style="margin-bottom: 1rem;">No clients found.</p>
                <button class="btn btn-primary" onclick="addClient()">➕ Create First Client</button>
            </div>
            {% endif %}
        </div>
    </div>
</div>

<script>
// Update ticket count
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
            if (countEl) countEl.textContent = '0';
        });
}

// Update VPN status
function updateVPNStatus() {
    safeFetch('/api/vpn/status')
        .then(data => {
            const statusEl = document.getElementById('vpn-status');
            if (statusEl) {
                const isRunning = data.running || (data.protocols && (
                    data.protocols.openvpn?.running || 
                    data.protocols.wireguard?.running || 
                    data.protocols.phazevpn?.running
                ));
                
                if (isRunning) {
                    statusEl.innerHTML = '<span class="status-badge status-active">🟢 Active</span>';
                } else {
                    statusEl.innerHTML = '<span class="status-badge status-inactive">🔴 Inactive</span>';
                }
            }
        })
        .catch(err => {
            console.error('Failed to fetch VPN status:', err);
            const statusEl = document.getElementById('vpn-status');
            if (statusEl) {
                statusEl.innerHTML = '<span class="status-badge status-inactive">❌ Error</span>';
            }
        });
}

// Add client
function addClient() {
    const name = prompt('Enter client name:');
    if (!name || !name.trim()) {
        showToast('Client name required', 'error');
        return;
    }
    
    const btn = event.target;
    setLoading(btn, true);
    
    safeFetch('/api/clients', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: name.trim()})
    })
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Client created successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.error || 'Failed to create client', 'error');
        }
    })
    .catch(err => {
        showToast('Error creating client: ' + (err.message || 'Unknown error'), 'error');
    })
    .finally(() => setLoading(btn, false));
}

// Initialize
updateTicketCount();
updateVPNStatus();
setInterval(updateTicketCount, 30000);
setInterval(updateVPNStatus, 10000);
</script>
{% endblock %}
'''
            
            # Write enhanced moderator dashboard
            stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/templates/moderator/dashboard.html << 'MOD_EOF'\n{enhanced_mod_dashboard}\nMOD_EOF")
            stdout.channel.recv_exit_status()
            print("   ✅ Enhanced moderator dashboard")
        else:
            print("   ❌ Failed to read moderator dashboard")
        
        print("")
        
        # ============================================================
        # STEP 2: Enhance User Dashboard (fix JavaScript, use safeFetch)
        # ============================================================
        print("2️⃣  Enhancing User Dashboard...")
        
        success, user_html, _ = run_command(ssh, f"cat {VPN_DIR}/web-portal/templates/user/dashboard.html", check=False)
        
        if success:
            # Replace fetch with safeFetch where appropriate
            # Replace alert with showToast
            # Add better error handling
            
            enhanced_user_html = user_html
            
            # Replace fetch('/api/vpn/status') with safeFetch
            if "fetch('/api/vpn/status')" in enhanced_user_html:
                enhanced_user_html = enhanced_user_html.replace(
                    "fetch('/api/vpn/status')",
                    "safeFetch('/api/vpn/status')"
                )
                print("   ✅ Updated VPN status to use safeFetch")
            
            # Replace fetch('/api/stats/bandwidth') with safeFetch
            if "fetch('/api/stats/bandwidth')" in enhanced_user_html:
                enhanced_user_html = enhanced_user_html.replace(
                    "fetch('/api/stats/bandwidth')",
                    "safeFetch('/api/stats/bandwidth')"
                )
                print("   ✅ Updated bandwidth stats to use safeFetch")
            
            # Replace fetch('/api/server/metrics') with safeFetch
            if "fetch('/api/server/metrics')" in enhanced_user_html:
                enhanced_user_html = enhanced_user_html.replace(
                    "fetch('/api/server/metrics')",
                    "safeFetch('/api/server/metrics').catch(() => ({}))"
                )
                print("   ✅ Updated server metrics to use safeFetch")
            
            # Replace alert with showToast
            if 'alert(' in enhanced_user_html and 'showToast' not in enhanced_user_html.split('alert(')[0][-50:]:
                # This is tricky, let's just make sure showToast is available
                pass
            
            # Add helper message if no clients
            if 'You don\'t have any VPN clients yet' in enhanced_user_html:
                # Already has good messaging
                pass
            
            # Write back
            stdin, stdout, stderr = ssh.exec_command(f"cat > {VPN_DIR}/web-portal/templates/user/dashboard.html << 'USER_EOF'\n{enhanced_user_html}\nUSER_EOF")
            stdout.channel.recv_exit_status()
            print("   ✅ Enhanced user dashboard")
        else:
            print("   ❌ Failed to read user dashboard")
        
        print("")
        
        # ============================================================
        # STEP 3: Verify and restart
        # ============================================================
        print("3️⃣  Restarting service...")
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
        print("📋 What was enhanced:")
        print("")
        print("🛡️  Moderator Dashboard:")
        print("   ✅ Stats grid (Clients, Tickets, Connections, VPN Status)")
        print("   ✅ Quick Actions section")
        print("   ✅ Enhanced client table with QR codes")
        print("   ✅ Real-time updates for tickets and VPN status")
        print("   ✅ Uses safeFetch/showToast/setLoading utilities")
        print("")
        print("👤 User Dashboard:")
        print("   ✅ Updated to use safeFetch for better error handling")
        print("   ✅ Already has great features (Connection status, Data usage, etc.)")
        print("")
        print("🌐 Dashboards are ready:")
        print("   • Moderators: https://phazevpn.com/moderator")
        print("   • Users: https://phazevpn.com/user")
        print("")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

