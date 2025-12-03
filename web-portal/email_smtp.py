#!/usr/bin/env python3
"""
Simple SMTP Email - Works with Gmail, Outlook, or any SMTP server
No API keys needed, just email credentials!
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import ssl
import secrets

# SMTP Configuration - Try config file first, then environment variables
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = ''
SMTP_PASSWORD = ''
FROM_EMAIL = ''
FROM_NAME = 'PhazeVPN'

# Try to load from config file
try:
    from smtp_config import (
        SMTP_HOST as CFG_HOST,
        SMTP_PORT as CFG_PORT,
        SMTP_USER as CFG_USER,
        SMTP_PASSWORD as CFG_PASSWORD,
        FROM_EMAIL as CFG_FROM,
        FROM_NAME as CFG_NAME
    )
    SMTP_HOST = CFG_HOST
    SMTP_PORT = CFG_PORT
    SMTP_USER = CFG_USER
    SMTP_PASSWORD = CFG_PASSWORD
    FROM_EMAIL = CFG_FROM or CFG_USER
    FROM_NAME = CFG_NAME
except ImportError:
    # Fallback to environment variables
    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    FROM_EMAIL = os.environ.get('FROM_EMAIL', SMTP_USER)
    FROM_NAME = os.environ.get('FROM_NAME', 'PhazeVPN')

def send_email(to_email, subject, html_content, text_content=None, retries=3):
    """
    Send email via SMTP (Gmail, Outlook, etc.) with retry logic
    
    Setup:
    1. For Gmail: Use App Password (not regular password)
       - Go to Google Account → Security → 2-Step Verification → App Passwords
       - Generate app password for "Mail"
    2. Set environment variables:
       export SMTP_USER='your-email@gmail.com'
       export SMTP_PASSWORD='your-app-password'
       export SMTP_HOST='smtp.gmail.com'
       export SMTP_PORT='587'
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email content
        text_content: Plain text version (optional, auto-generated from HTML if not provided)
        retries: Number of retry attempts (default: 3)
    """
    if not to_email:
        return False, "No recipient email provided"
    
    if not SMTP_USER or not SMTP_PASSWORD:
        return False, "SMTP_USER and SMTP_PASSWORD not set. See email_smtp.py for setup."
    
    # Retry logic for reliability
    last_error = None
    for attempt in range(retries):
        try:
            # Create message with proper headers to avoid spam
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{FROM_NAME} <{FROM_EMAIL or SMTP_USER}>"
            msg['To'] = to_email
            msg['Reply-To'] = FROM_EMAIL or SMTP_USER
            msg['List-Unsubscribe'] = f"<mailto:{FROM_EMAIL or SMTP_USER}?subject=unsubscribe>"
            msg['X-Mailer'] = 'PhazeVPN'
            msg['X-Priority'] = '3'  # Normal priority
            msg['Message-ID'] = f"<{secrets.token_hex(16)}@phazevpn.duckdns.org>"
            msg['Date'] = __import__('email.utils').utils.formatdate(localtime=True)
            msg['MIME-Version'] = '1.0'
            
            # Always add text version first (better for spam filters)
            if text_content:
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            elif html_content:
                # Generate text version from HTML if not provided
                import re
                text_from_html = re.sub(r'<[^>]+>', '', html_content)
                text_from_html = text_from_html.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                msg.attach(MIMEText(text_from_html, 'plain', 'utf-8'))
            
            # Add HTML version
            if html_content:
                msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # Connect to SMTP server
            if SMTP_PORT == 465:
                # Use SSL for port 465
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10, context=context)
            else:
                # Use STARTTLS for port 587
                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
                server.starttls(context=ssl.create_default_context())  # Enable encryption
            
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            return True, f"Email sent successfully via {SMTP_HOST}"
        
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed. "
            if 'outlook.com' in SMTP_HOST.lower() or 'hotmail.com' in SMTP_HOST.lower():
                error_msg += "Outlook requires an App Password (not your regular password). "
                error_msg += "Get one at: https://account.microsoft.com/security → Advanced security options → App passwords"
            else:
                error_msg += "Check username/password. For Gmail, use App Password."
            return False, error_msg
        
        except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
            last_error = e
            if attempt < retries - 1:
                # Wait before retry (exponential backoff)
                import time
                wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                time.sleep(wait_time)
                continue
            else:
                # Last attempt failed
                return False, f"SMTP error after {retries} attempts: {str(e)}"
        
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                import time
                wait_time = (attempt + 1) * 2
                time.sleep(wait_time)
                continue
            else:
                return False, f"Failed to send email after {retries} attempts: {str(e)}"
    
    # Should not reach here, but just in case
    return False, f"Failed to send email: {str(last_error) if last_error else 'Unknown error'}"


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
    print("=" * 60)
    print("📧 SMTP EMAIL SETUP")
    print("=" * 60)
    print("")
    print("✅ Gmail Setup (Easiest):")
    print("   1. Go to: https://myaccount.google.com/apppasswords")
    print("   2. Generate App Password for 'Mail'")
    print("   3. Set on VPS:")
    print("      export SMTP_USER='your-email@gmail.com'")
    print("      export SMTP_PASSWORD='your-16-char-app-password'")
    print("      export SMTP_HOST='smtp.gmail.com'")
    print("      export SMTP_PORT='587'")
    print("")
    print("✅ Outlook/Hotmail Setup:")
    print("   export SMTP_USER='your-email@outlook.com'")
    print("   export SMTP_PASSWORD='your-password'")
    print("   export SMTP_HOST='smtp-mail.outlook.com'")
    print("   export SMTP_PORT='587'")
    print("")
    print("✅ Yahoo Setup:")
    print("   export SMTP_USER='your-email@yahoo.com'")
    print("   export SMTP_PASSWORD='your-app-password'")
    print("   export SMTP_HOST='smtp.mail.yahoo.com'")
    print("   export SMTP_PORT='587'")
    print("")
    print("Test email:")
    print("  python3 email_smtp.py test@example.com")
    print("")
    
    if len(os.sys.argv) > 1:
        test_email = os.sys.argv[1]
        print(f"Sending test email to {test_email}...")
        success, msg = send_email(test_email, "Test Email", "This is a test email from PhazeVPN!")
        print(f"{'✅' if success else '❌'} {msg}")

