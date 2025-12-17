#!/usr/bin/env python3
"""
Test Outlook SMTP configuration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web-portal'))

from email_smtp import send_email

print("=" * 60)
print("🧪 TESTING OUTLOOK SMTP")
print("=" * 60)
print("")

# Test email
test_email = "aceisgaming369@gmail.com"
print(f"Sending test email to: {test_email}")
print("")

result = send_email(
    test_email,
    "PhazeVPN Test - Outlook SMTP",
    "<p>This is a test email from PhazeVPN using Outlook SMTP!</p><p>If you receive this, Outlook SMTP is working! ✅</p>"
)

if result[0]:
    print("✅ SUCCESS!")
    print(f"   {result[1]}")
else:
    print("❌ FAILED!")
    print(f"   {result[1]}")
    print("")
    print("Common issues:")
    print("  1. Outlook requires an App Password (not regular password)")
    print("  2. Get App Password: https://account.microsoft.com/security")
    print("  3. Go to: Advanced security options → App passwords")
    print("  4. Generate password for 'Mail'")
    print("  5. Update smtp_config.py with the App Password")

