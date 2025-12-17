#!/usr/bin/env python3
"""
Email API - Uses PhazeVPN's own email service first!
Falls back to Mailjet, SendGrid, Mailgun, or SMTP if needed
"""

import os
import requests
from pathlib import Path

# Try SendGrid first (easiest, free)
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

# Fallback: Mailgun
try:
    import requests
    MAILGUN_AVAILABLE = True
except ImportError:
    MAILGUN_AVAILABLE = False

# Try SMTP first (simplest - just need email credentials)
SMTP_AVAILABLE = False
send_email_smtp = None

try:
    from email_smtp import send_email as send_email_smtp_func
    send_email_smtp = send_email_smtp_func
    
    # Check if SMTP is configured
    import os
    if os.environ.get('SMTP_USER') and os.environ.get('SMTP_PASSWORD'):
        SMTP_AVAILABLE = True
except ImportError:
    pass

# Try Mailjet second (automatic emails, no authorization needed!)
MAILJET_AVAILABLE = False
send_email_mailjet = None

try:
    from email_mailjet import send_email as send_email_mailjet_func
    send_email_mailjet = send_email_mailjet_func
    
    # Check if Mailjet is actually configured
    try:
        from mailjet_config import MAILJET_API_KEY, MAILJET_SECRET_KEY
        if MAILJET_API_KEY and MAILJET_SECRET_KEY and len(MAILJET_API_KEY) > 10 and len(MAILJET_SECRET_KEY) > 10:
            MAILJET_AVAILABLE = True
    except ImportError:
        # Try environment variables
        import os
        if os.environ.get('MAILJET_API_KEY') and os.environ.get('MAILJET_SECRET_KEY'):
            MAILJET_AVAILABLE = True
except ImportError:
    pass

# Try to load Mailgun config
try:
    from mailgun_config import (
        MAILGUN_API_KEY, MAILGUN_DOMAIN, FROM_EMAIL, FROM_NAME
    )
except ImportError:
    # Fallback to environment variables
    MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY', '')
    MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN', 'mg.phazevpn.com')
    FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@phazevpn.com')
    FROM_NAME = os.environ.get('FROM_NAME', 'PhazeVPN')

# SendGrid (optional)
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')

# PhazeVPN's own email service (running on VPS)
EMAIL_SERVICE_URL = os.environ.get('EMAIL_SERVICE_URL', 'http://localhost:5005/api/v1/email')
EMAIL_SERVICE_USER = os.environ.get('EMAIL_SERVICE_USER', 'admin@phazevpn.duckdns.org')
# SECURITY: Default password removed - MUST be set via environment variable
EMAIL_SERVICE_PASSWORD = os.environ.get('EMAIL_SERVICE_PASSWORD', '')
if not EMAIL_SERVICE_PASSWORD:
    print("⚠️  WARNING: EMAIL_SERVICE_PASSWORD not set!")
    print("   Set it with: export EMAIL_SERVICE_PASSWORD='your-secure-password'")

def send_via_phazevpn_email_service(to_email, subject, html_content, text_content=None):
    """
    Send email via PhazeVPN's own email service (Postfix/Dovecot on VPS)
    This is the BEST option - uses our own infrastructure!
    """
    try:
        # Extract text from HTML if not provided
        if not text_content and html_content:
            import re
            text_content = re.sub(r'<[^>]+>', '', html_content)
            text_content = text_content.replace('&nbsp;', ' ').replace('&amp;', '&')
            text_content = text_content.replace('&lt;', '<').replace('&gt;', '>')
        
        # Send via our email service API
        response = requests.post(
            f"{EMAIL_SERVICE_URL}/send",
            json={
                'from': EMAIL_SERVICE_USER,
                'to': to_email,
                'subject': subject,
                'body': text_content or html_content,
                'html_body': html_content,
                'password': EMAIL_SERVICE_PASSWORD
            },
            headers={'Authorization': 'Bearer phazevpn-internal'},
            timeout=10
        )
        
        if response.status_code == 200:
            return True, f"Email sent via PhazeVPN Email Service"
        else:
            return False, f"Email service error: {response.status_code} - {response.text}"
    
    except requests.exceptions.ConnectionError:
        return False, "Email service not reachable (may be on different server)"
    except requests.exceptions.Timeout:
        return False, "Email service timeout"
    except Exception as e:
        return False, f"Email service error: {str(e)}"

def send_email(to_email, subject, html_content, text_content=None):
    """
    Send email - Tries PhazeVPN's own email service FIRST, then Mailjet, SendGrid, Mailgun, SMTP
    
    Priority:
    1. PhazeVPN Email Service (our own Postfix/Dovecot - BEST option!)
    2. Mailjet (professional, 6,000 emails/month free)
    3. SendGrid (100 emails/day free)
    4. Mailgun (5,000 emails/month free)
    5. SMTP (Gmail/Outlook - personal email, last resort only)
    """
    if not to_email:
        return False, "No recipient email provided"
    
    # Try PhazeVPN's own email service FIRST (best option - our own infrastructure!)
    try:
        result = send_via_phazevpn_email_service(to_email, subject, html_content, text_content)
        if result[0]:  # Success
            return result
        # If failed, log why but continue to next option
        print(f"PhazeVPN email service failed: {result[1]}")
    except Exception as e:
        print(f"PhazeVPN email service error: {e}")
    
    # Try Mailjet second (professional service, already configured!)
    if send_email_mailjet and MAILJET_AVAILABLE:
        try:
            result = send_email_mailjet(to_email, subject, html_content, text_content)
            if result[0]:  # Success
                return result
            # If failed but function exists, log why
            if not result[0] and "not configured" not in result[1].lower():
                print(f"Mailjet returned: {result[1]}")
        except Exception as e:
            print(f"Mailjet failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Try SendGrid second (no domain verification needed!)
    if SENDGRID_AVAILABLE and SENDGRID_API_KEY:
        try:
            result = send_via_sendgrid(to_email, subject, html_content)
            if result[0]:  # Success
                return result
        except Exception as e:
            print(f"SendGrid failed: {e}")
    
    # Try Mailgun third (requires domain verification or authorized recipients)
    if MAILGUN_AVAILABLE and MAILGUN_API_KEY:
        try:
            result = send_via_mailgun(to_email, subject, html_content)
            if result[0]:  # Success
                return result
        except Exception as e:
            print(f"Mailgun failed: {e}")
    
    # Try SMTP LAST (personal Gmail - only as fallback, not recommended for production!)
    if send_email_smtp:
        try:
            # Check if SMTP is configured
            try:
                from smtp_config import SMTP_USER, SMTP_PASSWORD
                if SMTP_USER and SMTP_PASSWORD:
                    print("⚠️  Using Gmail SMTP as fallback (not recommended for production)")
                    result = send_email_smtp(to_email, subject, html_content, text_content)
                    if result[0]:  # Success
                        return result
                    # If failed, log why but continue
                    print(f"SMTP failed: {result[1]}")
            except ImportError:
                pass
        except Exception as e:
            print(f"SMTP error: {e}")
    
    # Skip if not configured (don't break signup)
    print(f"⚠️  Email not configured - would send to {to_email}: {subject}")
    return True, "Email skipped (not configured)"


def send_via_sendgrid(to_email, subject, html_content):
    """Send via SendGrid API - NO SMTP, NO PERSONAL EMAIL!"""
    if not SENDGRID_AVAILABLE:
        return False, "SendGrid not installed (pip install sendgrid)"
    
    if not SENDGRID_API_KEY:
        return False, "SENDGRID_API_KEY not set"
    
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return True, f"Email sent (status: {response.status_code})"
    except Exception as e:
        return False, str(e)


def send_via_mailgun(to_email, subject, html_content):
    """Send via Mailgun API - NO SMTP, NO PERSONAL EMAIL!"""
    if not MAILGUN_AVAILABLE:
        return False, "requests not installed"
    
    if not MAILGUN_API_KEY:
        return False, "MAILGUN_API_KEY not set"
    
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"{FROM_NAME} <{FROM_EMAIL}>",
            "to": to_email,
            "subject": subject,
            "html": html_content
        }
    )
    
    if response.status_code == 200:
        return True, "Email sent via Mailgun"
    else:
        return False, f"Mailgun error: {response.text}"


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


def send_verification_email(to_email, username, verification_token):
    """Send email verification email - optimized to avoid spam filters"""
    subject = "Verify Your PhazeVPN Account"
    
    verification_url = f"https://phazevpn.duckdns.org/verify-email?token={verification_token}&user={username}"
    
    # Improved HTML with better spam avoidance
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, Helvetica, sans-serif; line-height: 1.6; color: #333333; background-color: #f4f4f4; margin: 0; padding: 0;">
        <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f4f4f4;">
            <tr>
                <td style="padding: 20px 0;">
                    <table role="presentation" style="width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <tr>
                            <td style="padding: 40px 30px; text-align: center; background: linear-gradient(135deg, #4a9eff 0%, #10b981 100%); border-radius: 8px 8px 0 0;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px;">PhazeVPN</h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 14px;">Email Verification</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px 30px;">
                                <h2 style="color: #333333; margin: 0 0 20px 0; font-size: 24px;">Verify Your Email Address</h2>
                                <p style="color: #666666; margin: 0 0 20px 0; font-size: 16px;">Hi <strong>{username}</strong>,</p>
                                <p style="color: #666666; margin: 0 0 30px 0; font-size: 16px;">Welcome to PhazeVPN! Please verify your email address to activate your account and start using our secure VPN service.</p>
                                
                                <table role="presentation" style="width: 100%; margin: 30px 0;">
                                    <tr>
                                        <td style="text-align: center;">
                                            <a href="{verification_url}" style="background-color: #4a9eff; color: #ffffff; padding: 15px 40px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; font-size: 16px;">Verify Email Address</a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="color: #999999; margin: 30px 0 10px 0; font-size: 14px;">Or copy and paste this link into your browser:</p>
                                <p style="color: #4a9eff; margin: 0 0 30px 0; font-size: 12px; word-break: break-all; background-color: #f9f9f9; padding: 10px; border-radius: 4px;">{verification_url}</p>
                                
                                <p style="color: #999999; margin: 30px 0 0 0; font-size: 12px; border-top: 1px solid #eeeeee; padding-top: 20px;">This verification link will expire in 24 hours for security reasons.</p>
                                <p style="color: #999999; margin: 10px 0 0 0; font-size: 12px;">If you didn't create this account, you can safely ignore this email.</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 20px 30px; background-color: #f9f9f9; border-radius: 0 0 8px 8px; text-align: center;">
                                <p style="color: #999999; margin: 0; font-size: 12px;">This is an automated message from PhazeVPN. Please do not reply to this email.</p>
                                <p style="color: #999999; margin: 10px 0 0 0; font-size: 12px;">© 2025 PhazeVPN. All rights reserved.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    text_content = f"""
    Verify Your PhazeVPN Account
    
    Hi {username},
    
    Welcome to PhazeVPN! Please verify your email address to activate your account.
    
    Click this link to verify: {verification_url}
    
    This link will expire in 24 hours.
    
    If you didn't create this account, please ignore this email.
    """
    
    return send_email(to_email, subject, html_content, text_content)


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
    print("📧 EMAIL API SETUP")
    print("==========================================")
    print("")
    print("✅ Option 1: SendGrid (Recommended)")
    print("   1. Go to: https://sendgrid.com")
    print("   2. Sign up (free - 100 emails/day)")
    print("   3. Get API key (Settings → API Keys)")
    print("   4. Set: export SENDGRID_API_KEY='your-key'")
    print("")
    print("✅ Option 2: Mailgun (5,000 emails/month)")
    print("   1. Go to: https://mailgun.com")
    print("   2. Sign up (free tier)")
    print("   3. Get API key and domain")
    print("   4. Set: export MAILGUN_API_KEY='your-key'")
    print("   5. Set: export MAILGUN_DOMAIN='mg.yourdomain.com'")
    print("")
    print("✅ Option 3: Skip emails (current)")
    print("   - Emails are optional")
    print("   - Just stores email for account recovery")
    print("   - No emails sent if not configured")
    print("")

