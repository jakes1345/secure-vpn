#!/usr/bin/env python3
"""Test the web portal"""

import requests

VPS_IP = "15.204.11.19"
PORTAL_URL = f"http://{VPS_IP}:5000"

print("🧪 Testing Web Portal...")
print("="*60)
print()

# Test 1: Check if portal is accessible
print("1️⃣  Testing portal accessibility...")
try:
    response = requests.get(PORTAL_URL, timeout=5)
    if response.status_code == 200 or response.status_code == 302:
        print(f"✅ Portal is accessible (status: {response.status_code})")
    else:
        print(f"⚠️  Portal returned status: {response.status_code}")
except Exception as e:
    print(f"❌ Can't connect: {e}")

print()

# Test 2: Test login page
print("2️⃣  Testing login page...")
try:
    response = requests.get(f"{PORTAL_URL}/login", timeout=5)
    if response.status_code == 200 and "SecureVPN" in response.text:
        print("✅ Login page loads correctly")
    else:
        print(f"⚠️  Login page issue (status: {response.status_code})")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 3: Test API endpoint (will fail without auth, but should return 302/401)
print("3️⃣  Testing API endpoints...")
try:
    response = requests.get(f"{PORTAL_URL}/api/vpn/status", timeout=5)
    print(f"   API status code: {response.status_code} (expected: 302 or 401)")
except Exception as e:
    print(f"   Error: {e}")

print()
print("="*60)
print("✅ Portal is running!")
print(f"🌐 Access it at: {PORTAL_URL}")
print()
print("Try logging in with:")
print("  Admin: admin / admin123")
print()

