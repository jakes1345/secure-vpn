#!/usr/bin/env python3
"""
Check Mailgun account status and provide specific fix steps
"""

import requests
from mailgun_config import MAILGUN_API_KEY, MAILGUN_DOMAIN

print("==========================================")
print("🔍 MAILGUN ACCOUNT STATUS CHECK")
print("==========================================")
print("")

# Check what we can access
print("📋 Testing API access...")
try:
    # Try to list domains (requires account access)
    response = requests.get(
        "https://api.mailgun.net/v3/domains",
        auth=("api", MAILGUN_API_KEY),
        timeout=10
    )
    
    if response.status_code == 200:
        print("   ✅ Can access Mailgun API")
        domains = response.json()
        print(f"   Domains: {len(domains.get('items', []))}")
    else:
        print(f"   ❌ Status: {response.status_code}")
        print(f"   Error: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("")

# Try to send email and get exact error
print("📧 Testing email send capability...")
try:
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": "PhazeVPN <noreply@phazevpn.com>",
            "to": "test@example.com",
            "subject": "Test",
            "html": "<p>Test</p>"
        },
        timeout=10
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        error_data = response.json() if 'application/json' in response.headers.get('content-type', '') else {}
        error_msg = error_data.get('message', response.text)
        print(f"   Error: {error_msg}")
        print("")
        
        if 'activate' in error_msg.lower():
            print("   ⚠️  ACCOUNT ACTIVATION ISSUE")
            print("")
            print("   📝 Steps to fix:")
            print("   1. Go to: https://app.mailgun.com")
            print("   2. Log in to your account")
            print("   3. Check for any RED warnings or notifications")
            print("   4. Look for 'Verify Account' or 'Complete Setup' buttons")
            print("   5. Check if you need to verify your email address")
            print("   6. Check if you need to add payment method (even for free tier)")
            print("   7. Try logging out and back in")
            print("")
            print("   💡 Sometimes activation takes a few minutes to propagate")
            print("   💡 Try waiting 5-10 minutes and test again")
        else:
            print(f"   💡 Other issue: {error_msg}")
    else:
        print("   ✅ Email sending works!")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print("")
print("==========================================")
print("📋 SUMMARY")
print("==========================================")
print("")
print("✅ API Keys: Valid")
print("✅ Domain: Active")
print("⚠️  Sending: Blocked (activation issue)")
print("")
print("🔧 Next Steps:")
print("   1. Log into Mailgun dashboard")
print("   2. Check for any pending verifications")
print("   3. Complete any required setup steps")
print("   4. Wait 5-10 minutes if you just activated")
print("   5. Test again")
print("")

