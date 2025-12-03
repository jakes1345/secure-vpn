#!/usr/bin/env python3
"""
SMTP Configuration - Outlook
Store your SMTP credentials here

IMPORTANT: This file contains passwords - DO NOT commit to git!
"""

# Gmail SMTP Settings
# Get App Password: https://myaccount.google.com/apppasswords
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587  # Use 587 for STARTTLS (recommended)
SMTP_USER = "aceisgaming369@gmail.com"
SMTP_PASSWORD = "tncklobfrjhxydes"  # Gmail App Password (16 characters, no spaces)

# Alternative: Yahoo
# SMTP_HOST = "smtp.mail.yahoo.com"
# SMTP_PORT = 587
# SMTP_USER = ""  # Your Yahoo email
# SMTP_PASSWORD = ""  # Your Yahoo App Password

# Email display settings
FROM_EMAIL = SMTP_USER  # Will use SMTP_USER if not set
FROM_NAME = "PhazeVPN"

# Instructions:
# 1. For Gmail: Go to https://myaccount.google.com/apppasswords
# 2. Generate App Password for "Mail"
# 3. Copy the 16-character password
# 4. Paste it in SMTP_PASSWORD above
# 5. Set SMTP_USER to your Gmail address
# 6. Save this file
# 7. Test: python3 email_smtp.py test@example.com

