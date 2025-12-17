#!/usr/bin/env python3
"""
Test both Mailgun API keys to see which one works
"""

import sys
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).parent))

from mailgun_config import MAILGUN_API_KEY, MAILGUN_API_KEY_ALT, MAILGUN_DOMAIN, FROM_EMAIL, FROM_NAME

print("==========================================")
print("🧪 TESTING BOTH MAILGUN API KEYS")
print("==========================================")
print("")

# Test email (must be authorized in Mailgun sandbox)
test_email = input("Enter authorized test email (or press Enter to skip): ").strip()

if not test_email:
    print("⚠️  No email provided - testing API key format only")
    print("")
    print("API Key 1 (Main - from API Keys section):")
    print(f"   Length: {len(MAILGUN_API_KEY)} chars")
    print(f"   Format: {'✅ Valid' if len(MAILGUN_API_KEY) > 30 else '❌ Too short'}")
    print("")
    print("API Key 2 (Alternative - unknown origin):")
    print(f"   Length: {len(MAILGUN_API_KEY_ALT)} chars")
    print(f"   Format: {'✅ Valid' if len(MAILGUN_API_KEY_ALT) > 30 else '❌ Too short'}")
    sys.exit(0)

print("")
print(f"📧 Testing with email: {test_email}")
print("")

# Test API Key 1 (Main - from API Keys section)
print("🔑 Testing API Key 1 (Main - from API Keys section):")
print(f"   Key: {MAILGUN_API_KEY[:20]}...")
try:
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"{FROM_NAME} <{FROM_EMAIL}>",
            "to": test_email,
            "subject": "Test Email - API Key 1",
            "html": "<p>This is a test from API Key 1 (main key from API Keys section)</p>"
        },
        timeout=10
    )
    
    if response.status_code == 200:
        print(f"   ✅ SUCCESS! Status: {response.status_code}")
        print(f"   Message ID: {response.json().get('id', 'N/A')}")
    else:
        print(f"   ❌ FAILED! Status: {response.status_code}")
        print(f"   Error: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ ERROR: {str(e)}")

print("")

# Test API Key 2 (Alternative - unknown origin)
print("🔑 Testing API Key 2 (Alternative - unknown origin):")
print(f"   Key: {MAILGUN_API_KEY_ALT[:20]}...")
try:
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY_ALT),
        data={
            "from": f"{FROM_NAME} <{FROM_EMAIL}>",
            "to": test_email,
            "subject": "Test Email - API Key 2",
            "html": "<p>This is a test from API Key 2 (alternative key)</p>"
        },
        timeout=10
    )
    
    if response.status_code == 200:
        print(f"   ✅ SUCCESS! Status: {response.status_code}")
        print(f"   Message ID: {response.json().get('id', 'N/A')}")
    else:
        print(f"   ❌ FAILED! Status: {response.status_code}")
        print(f"   Error: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ ERROR: {str(e)}")

print("")
print("==========================================")
print("✅ TEST COMPLETE")
print("==========================================")
print("")
print("📝 Recommendation:")
print("   Use the API key that returned SUCCESS (200 status)")
print("   Update mailgun_config.py with the working key")
print("")

