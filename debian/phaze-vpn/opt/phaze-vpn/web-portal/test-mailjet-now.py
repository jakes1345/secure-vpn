#!/usr/bin/env python3
"""
Test Mailjet email sending
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from email_mailjet import send_welcome_email

print("==========================================")
print("🧪 TESTING MAILJET EMAIL")
print("==========================================")
print("")
print("📧 Mailjet Configuration:")
print("   ✅ API Key: Configured")
print("   ✅ Secret Key: Configured")
print("   ✅ From Email: noreply@phazevpn.duckdns.org (just display)")
print("")
print("💡 IMPORTANT: Mailjet does NOT use your personal email!")
print("   - Emails sent from Mailjet's servers")
print("   - 'From' address is just what recipients see")
print("   - Your email account is NOT involved")
print("")

# Test email
test_email = input("Enter test email address (or press Enter to skip): ").strip()

if not test_email:
    print("")
    print("⚠️  No email provided - skipping test")
    print("")
    print("To test later:")
    print("  python3 test-mailjet-now.py")
    sys.exit(0)

print("")
print(f"📧 Sending test email to: {test_email}")
print("")

success, msg = send_welcome_email(test_email, "testuser")

if success:
    print(f"✅ SUCCESS: {msg}")
    print("")
    print("📬 Check your inbox!")
    print("")
    print("💡 The email will show:")
    print("   From: PhazeVPN <noreply@phazevpn.duckdns.org>")
    print("   (This is just display - not your personal email!)")
else:
    print(f"❌ FAILED: {msg}")
    print("")
    print("💡 Troubleshooting:")
    print("   1. Check mailjet_config.py has correct API keys")
    print("   2. Install: pip install mailjet-rest")
    print("   3. Check Mailjet dashboard for any issues")

print("")
print("==========================================")

