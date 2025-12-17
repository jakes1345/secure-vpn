#!/usr/bin/env python3
"""
Test Mailgun email sending
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from email_api import send_welcome_email, send_email

print("==========================================")
print("🧪 TESTING MAILGUN EMAIL")
print("==========================================")
print("")

# Test email
test_email = input("Enter test email address (or press Enter to skip): ").strip()

if not test_email:
    print("⚠️  No email provided - skipping test")
    print("")
    print("To test later, run:")
    print("  python3 test-mailgun.py")
    sys.exit(0)

print("")
print(f"📧 Sending test email to: {test_email}")
print("")

# Test welcome email
success, message = send_welcome_email(test_email, "testuser")

if success:
    print(f"✅ SUCCESS: {message}")
    print("")
    print("📬 Check your inbox (and spam folder)!")
else:
    print(f"❌ FAILED: {message}")
    print("")
    print("💡 Troubleshooting:")
    print("   1. Check mailgun_config.py has correct API key")
    print("   2. Verify domain in Mailgun dashboard")
    print("   3. For sandbox domain, recipient must be authorized")
    print("")

print("==========================================")

