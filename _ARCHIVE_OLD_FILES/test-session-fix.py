#!/usr/bin/env python3
"""
Test Session Cookie Fix
"""

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_BASE_URL = "https://phazevpn.duckdns.org"

session = requests.Session()
session.timeout = 5

print("Testing session cookie...")
print()

# Login
login_resp = session.post(f"{API_BASE_URL}/login",
                         data={'username': 'admin', 'password': 'admin123'},
                         timeout=5, verify=False, allow_redirects=True)

print(f"Login status: {login_resp.status_code}")
print(f"Cookies after login: {[c.name for c in session.cookies]}")
print()

# Try API
api_resp = session.get(f"{API_BASE_URL}/api/my-clients",
                      timeout=5, verify=False)

print(f"API status: {api_resp.status_code}")
print(f"API response: {api_resp.text[:200]}")

if api_resp.status_code == 200:
    print("✅ SUCCESS! Session cookie is working!")
    data = api_resp.json()
    print(f"Clients: {data.get('clients', [])}")
else:
    print("❌ Still failing - need to check Flask session config")

