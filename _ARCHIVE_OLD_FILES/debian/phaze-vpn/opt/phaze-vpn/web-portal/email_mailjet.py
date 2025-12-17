#!/usr/bin/env python3
"""
Mailjet Email API - Automatic emails, no authorization needed!
Free: 6,000 emails/month
"""

import os
import json

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from mailjet_rest import Client
    MAILJET_PACKAGE_AVAILABLE = True
except ImportError:
    MAILJET_PACKAGE_AVAILABLE = False

# Try to load Mailjet config
try:
    from mailjet_config import (
        MAILJET_API_KEY, MAILJET_SECRET_KEY, FROM_EMAIL, FROM_NAME
    )
except ImportError:
    # Fallback to environment variables
    MAILJET_API_KEY = os.environ.get('MAILJET_API_KEY', '')
    MAILJET_SECRET_KEY = os.environ.get('MAILJET_SECRET_KEY', '')
    FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@phazevpn.com')
    FROM_NAME = os.environ.get('FROM_NAME', 'PhazeVPN')

def send_email(to_email, subject, html_content, text_content=None):
    """
    Send email via Mailjet - Automatic, no authorization needed!
    """
    if not to_email:
        return False, "No recipient email provided"
    
    if not MAILJET_API_KEY or not MAILJET_SECRET_KEY:
        return False, "MAILJET_API_KEY and MAILJET_SECRET_KEY not set"
    
    try:
        # Use direct HTTP API call to /v3.1/send endpoint
        url = 'https://api.mailjet.com/v3.1/send'
        
        # Prepare email data
        email_data = {
            'Messages': [{
                'From': {
                    'Email': FROM_EMAIL,
                    'Name': FROM_NAME
                },
                'To': [{
                    'Email': to_email
                }],
                'Subject': subject,
                'HTMLPart': html_content,
                'TextPart': text_content or html_content.replace('<br>', '\n').replace('</p>', '\n\n').replace('<h1>', '').replace('</h1>', '\n').replace('<h3>', '').replace('</h3>', '\n')
            }]
        }
        
        # Try using requests library first (direct HTTP)
        if REQUESTS_AVAILABLE:
            response = requests.post(
                url,
                auth=(MAILJET_API_KEY, MAILJET_SECRET_KEY),
                headers={'Content-Type': 'application/json'},
                json=email_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result_data = response.json()
                message_id = result_data.get('Messages', [{}])[0].get('To', [{}])[0].get('MessageID', 'N/A')
                return True, f"Email sent via Mailjet (Message ID: {message_id})"
            else:
                return False, f"Mailjet error: {response.status_code} - {response.text}"
        
        # Fallback to mailjet-rest library
        elif MAILJET_PACKAGE_AVAILABLE:
            mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_SECRET_KEY), version='v3.1')
            result = mailjet.send.create(data=email_data)
            
            if result.status_code == 200:
                return True, f"Email sent via Mailjet (Message ID: {result.json()['Messages'][0]['To'][0]['MessageID']})"
            else:
                return False, f"Mailjet error: {result.status_code} - {result.text}"
        else:
            return False, "Neither requests nor mailjet-rest installed"
            
    except Exception as e:
        return False, f"Mailjet error: {str(e)}"


def send_welcome_email(to_email, username):
    """Send welcome email to new user"""
    subject = "Welcome to PhazeVPN!"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #4a9eff;">Welcome to PhazeVPN!</h1>
            <p>Hi <strong>{username}</strong>,</p>
            <p>Your account has been successfully created!</p>
            <p>You can now:</p>
            <ul>
                <li>Login to the dashboard</li>
                <li>Create VPN client configurations</li>
                <li>Download config files or QR codes</li>
            </ul>
            <p><a href="https://phazevpn.duckdns.org/login" style="background: #4a9eff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Login Now</a></p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">This is an automated message from PhazeVPN</p>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_content)


def send_password_reset_email(to_email, username, reset_token):
    """Send password reset email"""
    subject = "PhazeVPN Password Reset"
    
    reset_url = f"https://phazevpn.duckdns.org/reset-password?token={reset_token}&user={username}"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #4a9eff;">Password Reset Request</h1>
            <p>Hi <strong>{username}</strong>,</p>
            <p>You requested a password reset for your PhazeVPN account.</p>
            <p><a href="{reset_url}" style="background: #4a9eff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Reset Password</a></p>
            <p style="color: #666; font-size: 12px;">This link will expire in 1 hour.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">If you didn't request this, please ignore this email.</p>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_content)


if __name__ == "__main__":
    print("==========================================")
    print("📧 MAILJET EMAIL API")
    print("==========================================")
    print("")
    print("Setup:")
    print("  1. Sign up: https://www.mailjet.com")
    print("  2. Get API key and Secret key")
    print("  3. Set: export MAILJET_API_KEY='your-key'")
    print("  4. Set: export MAILJET_SECRET_KEY='your-secret'")
    print("  5. Install: pip install mailjet-rest")
    print("  6. Done!")
    print("")
    print("Benefits:")
    print("  ✅ 6,000 emails/month free")
    print("  ✅ No domain verification needed")
    print("  ✅ Automatic emails to anyone")
    print("  ✅ No authorization required")
    print("")

