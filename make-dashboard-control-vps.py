#!/usr/bin/env python3
"""
Make Dashboard Control VPS VPN Remotely
Update dashboard to use SSH or API to control VPS VPN
"""

from paramiko import SSHClient, AutoAddPolicy
import json

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

print("=" * 70)
print("🔧 MAKING DASHBOARD CONTROL VPS VPN REMOTELY")
print("=" * 70)
print()

# Check if web portal has VPN control API
print("1️⃣ Checking if web portal has VPN control API...")
with open('/opt/phaze-vpn/web-portal/app.py', 'r') as f:
    app_content = f.read()
    if '@app.route' in app_content and 'vpn' in app_content.lower():
        print("   ✅ Web portal has VPN routes")
    else:
        print("   ⚠️  No VPN control API found in web portal")

print()
print("2️⃣ Options for reliable VPN control:")
print()
print("   Option A: Use SSH to control VPS (Most Reliable)")
print("   - Dashboard connects to VPS via SSH")
print("   - Runs systemctl commands on VPS")
print("   - Requires SSH key or password")
print("   - ✅ Very reliable - direct control")
print()
print("   Option B: Use Web Portal API (Easier)")
print("   - Dashboard calls web portal API endpoints")
print("   - Web portal runs commands on VPS")
print("   - ✅ No SSH needed")
print("   - ✅ More secure (API authentication)")
print()
print("   Option C: Hybrid (Best)")
print("   - Try API first (if available)")
print("   - Fallback to SSH")
print("   - ✅ Most reliable")
print()

# Check current dashboard approach
print("3️⃣ Current dashboard approach:")
print("   - Tries to control LOCAL VPN server")
print("   - Uses systemctl on local machine")
print("   - ❌ Won't work - VPN is on VPS, not local!")
print()

print("=" * 70)
print("💡 RECOMMENDATION")
print("=" * 70)
print()
print("Best approach: Add API endpoints to web portal for VPN control")
print("Then update dashboard to use API instead of local systemctl")
print()
print("This is more reliable because:")
print("   ✅ API handles authentication")
print("   ✅ Works from anywhere (not just local machine)")
print("   ✅ Web portal already has access to VPS")
print("   ✅ Can add logging/audit trail")
print("   ✅ More secure than SSH from client")
print()

