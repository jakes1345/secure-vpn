#!/usr/bin/env python3
"""
Switch from Mailgun to SendGrid
Easier setup - no domain verification needed!
"""

import os
import sys

print("==========================================")
print("🚀 SWITCH TO SENDGRID")
print("==========================================")
print("")
print("SendGrid Benefits:")
print("  ✅ No domain verification needed")
print("  ✅ Can send to any email immediately")
print("  ✅ 100 emails/day free")
print("  ✅ Easier setup")
print("")
print("Steps:")
print("  1. Sign up: https://sendgrid.com")
print("  2. Get API key (Settings → API Keys)")
print("  3. Set: export SENDGRID_API_KEY='your-key'")
print("  4. Install: pip install sendgrid")
print("  5. Done!")
print("")
print("Current setup:")
print(f"  Mailgun: {'✅ Configured' if os.path.exists('mailgun_config.py') else '❌ Not configured'}")
print(f"  SendGrid: {'✅ Available' if os.environ.get('SENDGRID_API_KEY') else '❌ Not set'}")
print("")
print("To switch:")
print("  1. Get SendGrid API key")
print("  2. Set environment variable:")
print("     export SENDGRID_API_KEY='SG.your-key-here'")
print("  3. email_api.py will automatically use SendGrid")
print("")
print("==========================================")

