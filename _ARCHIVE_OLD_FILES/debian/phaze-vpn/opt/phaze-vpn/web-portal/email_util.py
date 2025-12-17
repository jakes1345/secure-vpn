#!/usr/bin/env python3
"""
Simple email utility for SecureVPN
Uses system sendmail/postfix - no external services needed!
"""

import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import sys

# Default settings
FROM_EMAIL = "noreply@securevpn.local"
FROM_NAME = "SecureVPN"
SMTP_HOST = "localhost"
SMTP_PORT = 25

def send_email(to_email, subject, body_html="", body_text="", from_email=None, from_name=None):
    """
    Send email using system mail server
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML email body (optional)
        body_text: Plain text email body (optional)
        from_email: Sender email (default: noreply@securevpn.local)
        from_name: Sender name (default: SecureVPN)
    
    Returns:
        (success: bool, message: str)
    """
    if not to_email:
        return False, "No recipient email provided"
    
    from_email = from_email or FROM_EMAIL
    from_name = from_name or FROM_NAME
    
    # Use text body if HTML not provided
    if not body_text and body_html:
        # Simple HTML to text conversion
        body_text = body_html.replace('<br>', '\n').replace('<br/>', '\n')
        body_text = body_text.replace('<p>', '').replace('</p>', '\n\n')
        import re
        body_text = re.sub('<[^<]+?>', '', body_text).strip()
    elif not body_text:
        body_text = body_html
    
    # Try method 1: Use sendmail command (simplest)
    try:
        return send_via_sendmail(to_email, subject, body_html or body_text, from_email, from_name)
    except:
        pass
    
    # Try method 2: Use Python SMTP to localhost
    try:
        return send_via_smtp(to_email, subject, body_html, body_text, from_email, from_name)
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"


def send_via_sendmail(to_email, subject, body, from_email, from_name):
    """Send email using system sendmail command"""
    msg = MIMEText(body, 'html' if '<' in body else 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = to_email
    
    # Use sendmail command
    result = subprocess.run(
        ['/usr/sbin/sendmail', '-t', '-i'],
        input=msg.as_string(),
        text=True,
        capture_output=True,
        timeout=10
    )
    
    if result.returncode == 0:
        return True, "Email sent successfully"
    else:
        raise Exception(f"sendmail failed: {result.stderr.decode()}")


def send_via_smtp(to_email, subject, body_html, body_text, from_email, from_name):
    """Send email using SMTP to localhost"""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = to_email
    
    if body_text:
        msg.attach(MIMEText(body_text, 'plain'))
    if body_html:
        msg.attach(MIMEText(body_html, 'html'))
    
    # Connect to local SMTP server
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
    server.sendmail(from_email, [to_email], msg.as_string())
    server.quit()
    
    return True, "Email sent successfully"


def send_welcome_email(to_email, username):
    """Send welcome email to new user"""
    subject = "Welcome to SecureVPN!"
    
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #4a9eff;">Welcome to SecureVPN!</h1>
            <p>Hi <strong>{username}</strong>,</p>
            <p>Your account has been successfully created!</p>
            <p>You can now:</p>
            <ul>
                <li>Login to the dashboard</li>
                <li>Create VPN client configurations</li>
                <li>Download config files or QR codes</li>
            </ul>
            <p><a href="http://15.204.11.19:5000/login" style="background: #4a9eff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Login Now</a></p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">This is an automated message from SecureVPN</p>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, body_html=body_html)


def send_password_reset_email(to_email, username, reset_token):
    """Send password reset email"""
    subject = "SecureVPN Password Reset"
    
    reset_url = f"http://15.204.11.19:5000/reset-password?token={reset_token}&user={username}"
    
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #4a9eff;">Password Reset Request</h1>
            <p>Hi <strong>{username}</strong>,</p>
            <p>You requested a password reset for your SecureVPN account.</p>
            <p><a href="{reset_url}" style="background: #4a9eff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Reset Password</a></p>
            <p style="color: #666; font-size: 12px;">This link will expire in 1 hour.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">If you didn't request this, please ignore this email.</p>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, body_html=body_html)


def test_email_config():
    """Test if email is configured correctly"""
    print("Testing email configuration...")
    
    # Check if sendmail exists
    sendmail_path = Path('/usr/sbin/sendmail')
    if not sendmail_path.exists():
        print("⚠️  sendmail not found. Installing postfix...")
        return False
    
    # Test sending to local user
    try:
        result = subprocess.run(['which', 'sendmail'], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✅ sendmail found")
            return True
    except:
        pass
    
    # Check if we can connect to SMTP
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 25))
        sock.close()
        if result == 0:
            print("✅ SMTP server (localhost:25) is available")
            return True
    except:
        pass
    
    print("⚠️  No email server found. Need to install postfix.")
    return False


if __name__ == "__main__":
    # Test email functionality
    if len(sys.argv) > 1:
        test_email = sys.argv[1]
        print(f"Sending test email to {test_email}...")
        success, msg = send_email(test_email, "Test Email", "This is a test email from SecureVPN!")
        print(f"{'✅' if success else '❌'} {msg}")
    else:
        # Just test configuration
        test_email_config()

