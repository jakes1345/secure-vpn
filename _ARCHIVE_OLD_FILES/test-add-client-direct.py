#!/usr/bin/env python3
"""
Test adding a client directly via API to see what's happening
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
print("TESTING CLIENT ADDITION")
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
if login_response.status_code == 200:
    data = login_response.json()
    print(f"   Success: {data.get('success')}")
    print(f"   User: {data.get('user', {})}")
    print("   ✅ Logged in")
else:
    print(f"   ❌ Login failed: {login_response.text[:200]}")
    exit(1)

print("")

# Step 2: Check current clients
print("2. Checking current clients...")
clients_response = session.get(f"{API_BASE}/my-clients", timeout=10)
print(f"   Status: {clients_response.status_code}")
if clients_response.status_code == 200:
    data = clients_response.json()
    print(f"   Success: {data.get('success')}")
    clients = data.get('clients', [])
    print(f"   Current clients: {len(clients)}")
    for client in clients:
        print(f"      - {client}")
else:
    print(f"   Response: {clients_response.text[:200]}")

print("")

# Step 3: Try to add a client
print("3. Attempting to add client 'test-client-123'...")
add_response = session.post(
    f"{API_BASE}/clients",
    json={"name": "test-client-123"},
    timeout=30
)
print(f"   Status: {add_response.status_code}")
print(f"   Response headers: {dict(add_response.headers)}")
print("")
print("   Full response:")
try:
    response_data = add_response.json()
    print(json.dumps(response_data, indent=2))
except:
    print(f"   Raw response: {add_response.text[:500]}")

print("")

# Step 4: Check clients again
print("4. Checking clients after add attempt...")
clients_response = session.get(f"{API_BASE}/my-clients", timeout=10)
if clients_response.status_code == 200:
    data = clients_response.json()
    clients = data.get('clients', [])
    print(f"   Clients now: {len(clients)}")
    for client in clients:
        print(f"      - {client}")

print("")
print("="*70)

