#!/usr/bin/env python3
"""
Outlook OAuth2 Configuration
Get these values from Azure Portal: https://portal.azure.com

Steps:
1. Go to Azure Portal -> Azure Active Directory -> App registrations
2. Register new app (or use existing)
3. Copy Application (client) ID -> CLIENT_ID below
4. Go to Certificates & secrets -> Create new client secret
5. Copy the secret Value -> CLIENT_SECRET below
6. For personal accounts, TENANT_ID can be "common"
"""
import os

# Azure App Registration Details
# SECURITY: Use environment variables - never hardcode secrets!
CLIENT_ID = os.environ.get('OUTLOOK_CLIENT_ID', 'e2a8a108-98d6-49c1-ac99-048ac8576883')
CLIENT_SECRET = os.environ.get('OUTLOOK_CLIENT_SECRET', '')  # MUST be set via environment variable
TENANT_ID = os.environ.get('OUTLOOK_TENANT_ID', '1fae0e6a-58b6-4259-8cc8-c3d77317ce09')

if not CLIENT_SECRET:
    print("⚠️  WARNING: OUTLOOK_CLIENT_SECRET not set in environment variables!")
    print("   Set it with: export OUTLOOK_CLIENT_SECRET='your-secret'")

# Email account
SMTP_USER = "phazevpn@outlook.com"
SMTP_HOST = "smtp-mail.outlook.com"
SMTP_PORT = 587

# Instructions:
# 1. Register app: https://portal.azure.com -> Azure Active Directory -> App registrations
# 2. Get Client ID from Overview page
# 3. Get Client Secret from Certificates & secrets page
# 4. Configure API permissions: Mail.Send, offline_access, openid, User.Read
# 5. Set environment variables: OUTLOOK_CLIENT_ID, OUTLOOK_CLIENT_SECRET, OUTLOOK_TENANT_ID
# 6. Never commit secrets to git!

