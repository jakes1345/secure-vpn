#!/usr/bin/env python3
"""
Outlook SMTP with OAuth2 Authentication
Requires: pip install msal requests
"""

import smtplib
import base64
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from msal import ConfidentialClientApplication
    MSAL_AVAILABLE = True
except ImportError:
    MSAL_AVAILABLE = False

# OAuth2 Configuration
# Get these from Azure Portal: https://portal.azure.com
# Try to load from config file
try:
    from outlook_oauth2_config import (
        CLIENT_ID as CFG_CLIENT_ID,
        CLIENT_SECRET as CFG_CLIENT_SECRET,
        TENANT_ID as CFG_TENANT_ID
    )
    CLIENT_ID = CFG_CLIENT_ID
    CLIENT_SECRET = CFG_CLIENT_SECRET
    TENANT_ID = CFG_TENANT_ID or "common"
except ImportError:
    import os
    CLIENT_ID = os.environ.get('OUTLOOK_CLIENT_ID', '')
    CLIENT_SECRET = os.environ.get('OUTLOOK_CLIENT_SECRET', '')
    TENANT_ID = os.environ.get('OUTLOOK_TENANT_ID', 'common')

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
# Use Microsoft Graph API instead of SMTP - works better with OAuth2
SCOPE = ["https://graph.microsoft.com/.default"]
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

# Email account - try to load from config
try:
    from outlook_oauth2_config import SMTP_USER as CFG_SMTP_USER, SMTP_HOST as CFG_SMTP_HOST, SMTP_PORT as CFG_SMTP_PORT
    SMTP_USER = CFG_SMTP_USER
    SMTP_HOST = CFG_SMTP_HOST
    SMTP_PORT = CFG_SMTP_PORT
except ImportError:
    SMTP_USER = "phazevpn@outlook.com"
    SMTP_HOST = "smtp-mail.outlook.com"
    SMTP_PORT = 587

# Token cache file
TOKEN_CACHE_FILE = "/tmp/outlook_token_cache.json"


def get_access_token():
    """
    Get OAuth2 access token for Outlook SMTP using client credentials flow
    """
    if not MSAL_AVAILABLE:
        return None, "msal library not installed. Run: pip install msal"
    
    if not CLIENT_ID or not CLIENT_SECRET:
        return None, "CLIENT_ID and CLIENT_SECRET not configured. See outlook_oauth2_config.py"
    
    try:
        # Create MSAL app with client credentials
        app = ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=CLIENT_SECRET,
            authority=AUTHORITY
        )
        
        # Try to get token from cache first
        accounts = app.get_accounts()
        result = None
        
        if accounts:
            # Try silent token acquisition
            result = app.acquire_token_silent(SCOPE, account=accounts[0])
        
        if not result:
            # Need to acquire new token using client credentials
            # For SMTP, we use client credentials flow (no user interaction)
            result = app.acquire_token_for_client(scopes=SCOPE)
        
        if "access_token" in result:
            # Cache token
            try:
                with open(TOKEN_CACHE_FILE, 'w') as f:
                    json.dump(result, f)
            except Exception:
                pass  # Cache is optional
            return result["access_token"], None
        else:
            error = result.get("error_description", result.get("error", "Unknown error"))
            return None, f"Failed to get access token: {error}"
    
    except Exception as e:
        return None, f"OAuth2 error: {str(e)}"


def send_email_oauth2(to_email, subject, html_content, text_content=None):
    """
    Send email via Microsoft Graph API using OAuth2 (better than SMTP for OAuth2)
    """
    if not to_email:
        return False, "No recipient email provided"
    
    # Get access token
    access_token, error = get_access_token()
    if not access_token:
        return False, error or "Failed to get OAuth2 access token"
    
    try:
        # Prepare email message for Graph API
        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": html_content or text_content or ""
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email
                        }
                    }
                ]
            }
        }
        
        # Send email via Microsoft Graph API
        url = f"{GRAPH_API_ENDPOINT}/users/{SMTP_USER}/sendMail"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json=message, timeout=10)
        
        if response.status_code == 202:
            return True, f"Email sent successfully via Outlook OAuth2 (Graph API)"
        else:
            error_msg = response.text
            return False, f"Graph API error ({response.status_code}): {error_msg}"
    
    except requests.exceptions.RequestException as e:
        return False, f"Request error: {str(e)}"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"


if __name__ == "__main__":
    print("=" * 60)
    print("📧 OUTLOOK OAUTH2 SMTP SETUP")
    print("=" * 60)
    print("")
    print("Requirements:")
    print("  1. Register app in Azure Portal: https://portal.azure.com")
    print("  2. Get Client ID and Client Secret")
    print("  3. Configure CLIENT_ID and CLIENT_SECRET above")
    print("  4. Install: pip install msal")
    print("")
    print("Current status:")
    print(f"  MSAL available: {MSAL_AVAILABLE}")
    print(f"  CLIENT_ID configured: {bool(CLIENT_ID)}")
    print(f"  CLIENT_SECRET configured: {bool(CLIENT_SECRET)}")
    print("")

