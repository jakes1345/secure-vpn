#!/usr/bin/env python3
"""
Test Outlook SMTP connection directly
"""

import smtplib
import ssl
from email.mime.text import MIMEText

SMTP_HOST = "smtp-mail.outlook.com"
SMTP_PORT = 587
SMTP_USER = "phazevpn@outlook.com"
SMTP_PASSWORD = "tchgqccdozierauo"

print("=" * 60)
print("🧪 TESTING OUTLOOK SMTP CONNECTION")
print("=" * 60)
print("")
print(f"Host: {SMTP_HOST}")
print(f"Port: {SMTP_PORT}")
print(f"User: {SMTP_USER}")
print(f"Password: {SMTP_PASSWORD[:4]}... (hidden)")
print("")

try:
    print("1️⃣ Connecting to SMTP server...")
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
    print("   ✅ Connected")
    
    print("2️⃣ Starting TLS...")
    server.starttls(context=ssl.create_default_context())
    print("   ✅ TLS started")
    
    print("3️⃣ Logging in...")
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("   ✅ Login successful!")
    
    print("4️⃣ Creating test message...")
    msg = MIMEText("Test email from PhazeVPN Outlook SMTP!")
    msg['Subject'] = "PhazeVPN Test - Outlook SMTP"
    msg['From'] = SMTP_USER
    msg['To'] = "aceisgaming369@gmail.com"
    
    print("5️⃣ Sending email...")
    server.send_message(msg)
    print("   ✅ Email sent!")
    
    server.quit()
    
    print("")
    print("=" * 60)
    print("✅ SUCCESS! Outlook SMTP is working!")
    print("=" * 60)
    
except smtplib.SMTPAuthenticationError as e:
    print(f"   ❌ Authentication failed: {e}")
    print("")
    print("Possible issues:")
    print("  1. App Password might be incorrect")
    print("  2. 2-Step Verification might not be enabled")
    print("  3. App Password might have been revoked")
    print("  4. Account might be locked")
    print("")
    print("Try:")
    print("  1. Go to: https://account.microsoft.com/security")
    print("  2. Check if 2-Step Verification is enabled")
    print("  3. Generate a NEW App Password")
    print("  4. Make sure you copy it correctly (no spaces)")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

