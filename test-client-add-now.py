#!/usr/bin/env python3
"""
Test adding a NEW client (not existing one)
"""

import requests
import json

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_BASE = "https://phazevpn.com/api"

# Create session
session = requests.Session()
session.verify = False

print("="*70)
print("TESTING NEW CLIENT ADDITION")
print("="*70)
print("")

# Step 1: Login
print("1. Logging in as admin...")
login_response = session.post(
    f"{API_BASE}/app/login",
    json={"username": "admin", "password": "admin123"},
    timeout=10
)
print(f"   Status: {login_response.status_code}")
if login_response.status_code != 200:
    print(f"   ❌ Login failed: {login_response.text[:200]}")
    exit(1)
print("   ✅ Logged in")
print("")

# Step 2: Try to add a NEW client (with timestamp to make it unique)
import time
client_name = f"newclient-{int(time.time())}"
print(f"2. Attempting to add NEW client '{client_name}'...")
add_response = session.post(
    f"{API_BASE}/clients",
    json={"name": client_name},
    timeout=60
)
print(f"   Status: {add_response.status_code}")
print("")
print("   Full response:")
try:
    response_data = add_response.json()
    print(json.dumps(response_data, indent=2))
    if response_data.get('success'):
        print("   ✅ CLIENT CREATED SUCCESSFULLY!")
    else:
        print(f"   ❌ Failed: {response_data.get('error')}")
except:
    print(f"   Raw response: {add_response.text[:500]}")

print("")

# Step 3: Check clients
print("3. Checking clients list...")
clients_response = session.get(f"{API_BASE}/my-clients", timeout=10)
if clients_response.status_code == 200:
    data = clients_response.json()
    clients = data.get('clients', [])
    print(f"   Total clients: {len(clients)}")
    for client in clients[-5:]:  # Show last 5
        if isinstance(client, dict):
            print(f"      - {client.get('name', client)}")
        else:
            print(f"      - {client}")

print("")
print("="*70)

