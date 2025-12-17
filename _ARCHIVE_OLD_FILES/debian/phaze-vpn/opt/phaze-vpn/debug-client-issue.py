#!/usr/bin/env python3
"""
Debug Client Issue - Test the exact flow the client uses
"""

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_BASE_URL = "https://phazevpn.duckdns.org"

print("=" * 70)
print("🔍 DEBUGGING CLIENT ISSUE")
print("=" * 70)
print()

session = requests.Session()
session.timeout = 5

# Step 1: Login
print("1️⃣ Testing login...")
try:
    login_resp = session.post(f"{API_BASE_URL}/login",
                             data={'username': 'admin', 'password': 'admin123'},
                             timeout=5, verify=False, allow_redirects=False)
    print(f"   Status: {login_resp.status_code}")
    print(f"   Cookies: {dict(session.cookies)}")
    if login_resp.status_code in [200, 302]:
        print("   ✅ Login successful")
    else:
        print(f"   ❌ Login failed: {login_resp.text[:200]}")
        exit(1)
except Exception as e:
    print(f"   ❌ Login error: {e}")
    exit(1)
print()

# Step 2: Get clients
print("2️⃣ Getting clients...")
try:
    resp = session.get(f"{API_BASE_URL}/api/my-clients",
                      timeout=5, verify=False)
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.text[:500]}")
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✅ API call successful")
        print(f"   Clients: {data.get('clients', [])}")
        clients = data.get('clients', [])
        
        if clients:
            client_name = clients[0]['name']
            print(f"   ✅ Found client: {client_name}")
            
            # Step 3: Download config
            print()
            print("3️⃣ Downloading config...")
            config_resp = session.get(f"{API_BASE_URL}/download/{client_name}",
                                     timeout=5, verify=False)
            print(f"   Status: {config_resp.status_code}")
            print(f"   Content-Type: {config_resp.headers.get('Content-Type', 'N/A')}")
            print(f"   Content-Length: {len(config_resp.text)} bytes")
            
            if config_resp.status_code == 200:
                print(f"   ✅ Config downloaded successfully")
                print(f"   First 200 chars: {config_resp.text[:200]}")
            else:
                print(f"   ❌ Download failed: {config_resp.text[:200]}")
        else:
            print("   ❌ No clients found!")
            print("   Trying to create one...")
            
            # Try to create client
            create_resp = session.post(f"{API_BASE_URL}/api/my-clients",
                                      json={'name': 'admin'},
                                      timeout=5, verify=False)
            print(f"   Create status: {create_resp.status_code}")
            print(f"   Create response: {create_resp.text[:200]}")
    else:
        print(f"   ❌ API call failed: {resp.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

