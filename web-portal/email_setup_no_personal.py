#!/usr/bin/env python3
"""
Email Setup - NO Personal Email Needed!
Uses API services (SendGrid, Mailgun, etc.) - no SMTP, no personal email
"""

# Option 1: SendGrid (Recommended - Easiest)
# Free: 100 emails/day forever
# No personal email needed - just API key

SENDGRID_SETUP = """
# Install: pip install sendgrid

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Get API key from sendgrid.com (free account)
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', 'your-api-key-here')

def send_email_sendgrid(to_email, subject, html_content):
    '''Send email via SendGrid API - NO SMTP, NO PERSONAL EMAIL!'''
    message = Mail(
        from_email='noreply@phazevpn.com',  # Can be any email (doesn't need to exist)
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return True, "Email sent"
    except Exception as e:
        return False, str(e)
"""

# Option 2: Mailgun (Also Easy)
# Free: 5,000 emails/month
MAILGUN_SETUP = """
# Install: pip install requests

import requests

MAILGUN_API_KEY = 'your-mailgun-api-key'
MAILGUN_DOMAIN = 'mg.phazevpn.com'  # Your domain or use sandbox domain

def send_email_mailgun(to_email, subject, html_content):
    '''Send email via Mailgun API - NO SMTP, NO PERSONAL EMAIL!'''
    return requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"PhazeVPN <noreply@{MAILGUN_DOMAIN}>",
            "to": to_email,
            "subject": subject,
            "html": html_content
        }
    )
"""

# Option 3: AWS SES (If you have AWS account)
# Free: 62,000 emails/month (if on EC2)
AWS_SES_SETUP = """
# Install: pip install boto3

import boto3
from botocore.exceptions import ClientError

def send_email_ses(to_email, subject, html_content):
    '''Send email via AWS SES - NO SMTP, NO PERSONAL EMAIL!'''
    client = boto3.client('ses', region_name='us-east-1')
    
    try:
        response = client.send_email(
            Source='noreply@phazevpn.com',
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Html': {'Data': html_content}}
            }
        )
        return True, response['MessageId']
    except ClientError as e:
        return False, str(e)
"""

# Option 4: Skip Email Entirely (Easiest!)
SKIP_EMAIL = """
# Just don't send emails - store email for account recovery only
# No email service needed at all!

def send_email_skip(to_email, subject, html_content):
    '''Don't actually send - just log it'''
    print(f"Would send email to {to_email}: {subject}")
    return True, "Email skipped (not configured)"
"""

print("==========================================")
print("📧 EMAIL SETUP - NO PERSONAL EMAIL NEEDED!")
print("==========================================")
print("")
print("✅ Best Option: SendGrid (Free, Easy, No Personal Email)")
print("")
print("Steps:")
print("1. Go to: https://sendgrid.com")
print("2. Sign up (free - 100 emails/day)")
print("3. Get API key (Settings → API Keys)")
print("4. Set environment variable:")
print("   export SENDGRID_API_KEY='your-key-here'")
print("5. Done! No SMTP, no personal email needed!")
print("")
print("Alternative: Mailgun (5,000 emails/month free)")
print("Alternative: AWS SES (62,000 emails/month free on EC2)")
print("Alternative: Skip emails entirely (just store for recovery)")
print("")

