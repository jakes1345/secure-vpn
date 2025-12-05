#!/usr/bin/env python3
"""
Test PhazeVPN Client Connection
Check if client can login and get config
"""

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_BASE_URL = "https://phazevpn.duckdns.org"

print("=" * 70)
print("🧪 TESTING CLIENT CONNECTION")
print("=" * 70)
print()

# Test 1: Check if site is accessible
print("1️⃣ Testing site accessibility...")
try:
    resp = requests.get(f"{API_BASE_URL}/", timeout=5, verify=False)
    print(f"   ✅ Site accessible: {resp.status_code}")
except Exception as e:
    print(f"   ❌ Site not accessible: {e}")
    exit(1)
print()

# Test 2: Test login endpoint
print("2️⃣ Testing login endpoint...")
try:
    # Try with default admin credentials
    resp = requests.post(f"{API_BASE_URL}/login",
                        data={'username': 'admin', 'password': 'admin123'},
                        timeout=5, verify=False, allow_redirects=False)
    print(f"   Login response: {resp.status_code}")
    if resp.status_code in [200, 302]:
        print("   ✅ Login endpoint working")
        cookies = resp.cookies
        print(f"   Session cookie: {cookies.get('session', 'None')}")
    else:
        print(f"   ⚠️  Unexpected status: {resp.status_code}")
except Exception as e:
    print(f"   ❌ Login failed: {e}")
print()

# Test 3: Test API endpoint
print("3️⃣ Testing API endpoint...")
try:
    session = requests.Session()
    # Login first
    login_resp = session.post(f"{API_BASE_URL}/login",
                             data={'username': 'admin', 'password': 'admin123'},
                             timeout=5, verify=False)
    
    # Get clients
    api_resp = session.get(f"{API_BASE_URL}/api/my-clients",
                          timeout=5, verify=False)
    print(f"   API response: {api_resp.status_code}")
    if api_resp.status_code == 200:
        data = api_resp.json()
        print(f"   ✅ API working")
        print(f"   Clients: {data.get('clients', [])}")
        if data.get('clients'):
            client_name = data['clients'][0]['name']
            print(f"   First client: {client_name}")
            
            # Test download
            print()
            print("4️⃣ Testing config download...")
            download_resp = session.get(f"{API_BASE_URL}/download/{client_name}",
                                       timeout=5, verify=False)
            print(f"   Download response: {download_resp.status_code}")
            if download_resp.status_code == 200:
                print(f"   ✅ Config download working")
                print(f"   Config size: {len(download_resp.text)} bytes")
            else:
                print(f"   ❌ Config download failed")
        else:
            print("   ⚠️  No clients found - need to create one")
    else:
        print(f"   ❌ API failed: {api_resp.status_code}")
        print(f"   Response: {api_resp.text[:200]}")
except Exception as e:
    print(f"   ❌ API test failed: {e}")
    import traceback
    traceback.print_exc()
print()

print("=" * 70)
print("📋 SUMMARY")
print("=" * 70)
print()
print("To use PhazeVPN client:")
print("1. Open PhazeVPN client")
print("2. Click CONNECT")
print("3. Login with your credentials:")
print("   - Username: admin (or your username)")
print("   - Password: admin123 (or your password)")
print("4. Client will download config and connect")
print()

