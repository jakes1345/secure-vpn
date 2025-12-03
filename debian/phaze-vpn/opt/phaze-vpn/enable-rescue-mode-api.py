#!/usr/bin/env python3
"""
Enable OVH VPS Rescue Mode using OVH API
This is an alternative if you can't find rescue mode in the web interface
"""

import requests
import time
import hashlib
import base64
import json

# OVH API Configuration
# Get these from: https://us.ovhcloud.com/auth/api/createToken
APPLICATION_KEY = "c623a0225525fa7d"
APPLICATION_SECRET = "0b7942f04defcc3f3dba9352c40f2347"
CONSUMER_KEY = "30f79d3012c01f89d06f1e7368bb6f20"

# VPS Information
VPS_SERVICE_NAME = ""  # Will be auto-detected if only one VPS
VPS_IP = "15.204.11.19"

# OVH API Endpoints
BASE_URL = "https://api.us.ovh.com/1.0"

def generate_signature(method, url, body, timestamp):
    """Generate OVH API signature"""
    signature_string = f"{APPLICATION_SECRET}+{CONSUMER_KEY}+{method}+{url}+{body}+{timestamp}"
    signature = hashlib.sha1(signature_string.encode()).hexdigest()
    return f"$1${signature}"

def make_api_request(method, endpoint, body=""):
    """Make authenticated API request to OVH"""
    if not APPLICATION_KEY or not APPLICATION_SECRET or not CONSUMER_KEY:
        print("❌ Error: API credentials not configured!")
        print("")
        print("📋 Setup Instructions:")
        print("   1. Go to: https://us.ovhcloud.com/auth/api/createToken")
        print("   2. Create API keys with these rights:")
        print("      - GET /vps")
        print("      - GET /vps/*")
        print("      - POST /vps/*/reboot")
        print("      - POST /vps/*/startRescueMode")
        print("   3. Copy Application Key, Secret, and Consumer Key")
        print("   4. Paste them in this script")
        return None
    
    timestamp = str(int(time.time() * 1000))
    url = f"{BASE_URL}{endpoint}"
    signature = generate_signature(method, url, body, timestamp)
    
    headers = {
        "X-Ovh-Application": APPLICATION_KEY,
        "X-Ovh-Consumer": CONSUMER_KEY,
        "X-Ovh-Signature": signature,
        "X-Ovh-Timestamp": timestamp,
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, data=body)
        else:
            response = requests.request(method, url, headers=headers, data=body)
        
        return response
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return None

def get_vps_list():
    """Get list of VPS services"""
    print("📋 Getting VPS list...")
    response = make_api_request("GET", "/vps")
    if response and response.status_code == 200:
        vps_list = response.json()
        print(f"   ✅ Found {len(vps_list)} VPS service(s)")
        return vps_list
    else:
        print(f"   ❌ Failed: {response.status_code if response else 'No response'}")
        return []

def get_vps_info(service_name):
    """Get VPS information"""
    print(f"📋 Getting VPS info for {service_name}...")
    response = make_api_request("GET", f"/vps/{service_name}")
    if response and response.status_code == 200:
        info = response.json()
        print(f"   ✅ VPS Name: {info.get('name', 'N/A')}")
        print(f"   ✅ IP: {info.get('ip', 'N/A')}")
        return info
    else:
        print(f"   ❌ Failed: {response.status_code if response else 'No response'}")
        return None

def enable_rescue_mode(service_name, email):
    """Enable rescue mode for VPS"""
    print(f"🚀 Enabling rescue mode for {service_name}...")
    
    body = json.dumps({
        "rescueEmail": email,
        "bootId": None  # Will use default rescue64-pro
    })
    
    response = make_api_request("POST", f"/vps/{service_name}/startRescueMode", body)
    
    if response and response.status_code == 200:
        result = response.json()
        print("   ✅ Rescue mode enabled!")
        print(f"   📧 Check email ({email}) for rescue credentials")
        return result
    else:
        error_msg = response.json() if response else "No response"
        print(f"   ❌ Failed: {response.status_code if response else 'No response'}")
        print(f"   Error: {error_msg}")
        return None

def main():
    print("==========================================")
    print("🚀 OVH VPS RESCUE MODE ENABLER (API)")
    print("==========================================")
    print("")
    
    # Check if credentials are configured
    if not APPLICATION_KEY or not APPLICATION_SECRET or not CONSUMER_KEY:
        print("⚠️  API credentials not configured!")
        print("")
        print("📋 To use this script:")
        print("   1. Go to: https://us.ovhcloud.com/auth/api/createToken")
        print("   2. Create API keys with these rights:")
        print("      - GET /vps")
        print("      - GET /vps/*")
        print("      - POST /vps/*/startRescueMode")
        print("   3. Edit this script and add:")
        print("      - APPLICATION_KEY")
        print("      - APPLICATION_SECRET")
        print("      - CONSUMER_KEY")
        print("      - VPS_SERVICE_NAME (your VPS service name)")
        print("")
        print("💡 Alternative: Use the web interface:")
        print("   1. Go to: https://us.ovhcloud.com")
        print("   2. Navigate to: Bare Metal Cloud → VPS")
        print("   3. Click your VPS")
        print("   4. Look for 'Rescue Mode' or 'Boot' tab")
        print("   5. Click 'Reboot in rescue mode'")
        print("")
        return
    
    # Get VPS list if service name not provided
    if not VPS_SERVICE_NAME:
        vps_list = get_vps_list()
        if not vps_list:
            print("❌ Could not get VPS list")
            return
        
        if len(vps_list) == 1:
            service_name = vps_list[0]
            print(f"   Using VPS: {service_name}")
        else:
            print("   Multiple VPS found. Please set VPS_SERVICE_NAME in script.")
            return
    else:
        service_name = VPS_SERVICE_NAME
    
    # Get VPS info
    vps_info = get_vps_info(service_name)
    if not vps_info:
        return
    
    # Verify IP matches
    if VPS_IP and vps_info.get('ip') != VPS_IP:
        print(f"   ⚠️  IP mismatch: Expected {VPS_IP}, got {vps_info.get('ip')}")
    
    # Enable rescue mode
    email = input("Enter your email for rescue mode credentials: ").strip()
    if not email:
        print("❌ Email required")
        return
    
    result = enable_rescue_mode(service_name, email)
    
    if result:
        print("")
        print("==========================================")
        print("✅ RESCUE MODE ENABLED!")
        print("==========================================")
        print("")
        print("📧 Check your email for:")
        print("   - Rescue IP address")
        print("   - Root password")
        print("")
        print("🔧 Next steps:")
        print("   1. SSH to rescue IP: ssh root@<RESCUE_IP>")
        print("   2. Mount your disk and fix firewall")
        print("   3. See: QUICK-RESCUE-FIX.md for commands")
        print("")

if __name__ == "__main__":
    main()

