#!/usr/bin/env python3
"""
Email API - Uses ONLY PhazeVPN's own email service!
No fallbacks - we use our own infrastructure exclusively.
"""

import os
import requests
from pathlib import Path

# PhazeVPN's own email service (running on VPS)
# Default to VPS IP if running on VPS, otherwise localhost for local dev
VPS_IP = os.environ.get('VPS_IP', '15.204.11.19')
EMAIL_SERVICE_URL = os.environ.get('EMAIL_SERVICE_URL', f'http://{VPS_IP}:5005/api/v1/email')
EMAIL_SERVICE_USER = os.environ.get('EMAIL_SERVICE_USER', 'admin@phazevpn.duckdns.org')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@phazevpn.com')
FROM_NAME = os.environ.get('FROM_NAME', 'PhazeVPN')

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
    Send email - Uses ONLY PhazeVPN's own email service!
    No fallbacks - we use our own infrastructure exclusively.
    """
    if not to_email:
        return False, "No recipient email provided"
    
    if not EMAIL_SERVICE_PASSWORD:
        return False, "EMAIL_SERVICE_PASSWORD not set. Email service requires authentication."
    
    # Use ONLY PhazeVPN's own email service
    try:
        result = send_via_phazevpn_email_service(to_email, subject, html_content, text_content)
        if result[0]:  # Success
            return result
        # If failed, return error (no fallbacks)
        return False, f"PhazeVPN email service failed: {result[1]}"
    except Exception as e:
        return False, f"PhazeVPN email service error: {str(e)}"


# Removed SendGrid and Mailgun functions - we only use PhazeVPN email service now!


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
    print("📧 PHAZEVPN EMAIL API")
    print("==========================================")
    print("")
    print("✅ Using ONLY PhazeVPN's own email service!")
    print("   - No third-party services (Mailgun, SendGrid, Gmail)")
    print("   - Uses our own Postfix/Dovecot email server")
    print("   - Full control over deliverability")
    print("")
    print("📋 Setup:")
    print("   1. Set EMAIL_SERVICE_PASSWORD:")
    print("      export EMAIL_SERVICE_PASSWORD='your-secure-password'")
    print("")
    print("   2. Set EMAIL_SERVICE_URL (if not using default):")
    print("      export EMAIL_SERVICE_URL='http://your-vps-ip:5005/api/v1/email'")
    print("")
    print("   3. Email service should be running on VPS at port 5005")
    print("")
    print("⚠️  If emails aren't working:")
    print("   - Check if email service is running: systemctl status email-service")
    print("   - Check email service logs")
    print("   - Verify EMAIL_SERVICE_PASSWORD is set correctly")
    print("   - Check if domain/IP is blacklisted (may need to get unbanned)")
    print("")

