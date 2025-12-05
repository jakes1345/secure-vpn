#!/usr/bin/env python3
"""
Test PhazeVPN Email Service and Create Test Account
"""
import requests
import json
import hashlib
import secrets
from datetime import datetime, timedelta
import sys
import os

# Add web portal to path
sys.path.insert(0, '/opt/secure-vpn/web-portal')

print('=' * 60)
print('📧 Testing PhazeVPN Email Service')
print('=' * 60)
print()

# Test 1: Send test email directly via email service API
print('1. Testing email service API...')
try:
    response = requests.post(
        'http://localhost:5005/api/v1/email/send',
        json={
            'from': 'admin@phazevpn.duckdns.org',
            'to': 'bigjacob710@gmail.com',
            'subject': 'PhazeVPN Test Email - Email Service Working!',
            'body': 'This is a test email from PhazeVPN email service. If you receive this, our email service is working correctly!',
            'html_body': '<html><body><h1>PhazeVPN Email Service Test</h1><p>This is a test email from PhazeVPN\'s own email service!</p><p>If you receive this email, it means our Postfix SMTP server is working correctly.</p></body></html>',
            'password': 'admin123'
        },
        headers={'Authorization': 'Bearer phazevpn-internal'},
        timeout=10
    )
    
    if response.status_code == 200:
        print('✅ Test email sent successfully!')
        print(f'   Response: {response.json()}')
    else:
        print(f'❌ Email send failed: {response.status_code}')
        print(f'   Response: {response.text}')
except Exception as e:
    print(f'❌ Error sending test email: {e}')
    import traceback
    traceback.print_exc()

print()
print('=' * 60)
print('👤 Creating Test Account')
print('=' * 60)
print()

# Load users
users_file = '/opt/secure-vpn/web-portal/users.json'
try:
    with open(users_file, 'r') as f:
        users_data = json.load(f)
except FileNotFoundError:
    users_data = {'users': {}, 'roles': {}}
except json.JSONDecodeError:
    print('⚠️  users.json is corrupted, creating new one...')
    users_data = {'users': {}, 'roles': {}}

# Create test account
test_username = 'testuser'
test_email = 'bigjacob710@gmail.com'
test_password = 'testpass123'

def hash_password(password):
    """Hash password using SHA256 (matches app.py)"""
    return hashlib.sha256(password.encode()).hexdigest()

if test_username in users_data.get('users', {}):
    print(f'⚠️  User {test_username} already exists')
    user_data = users_data['users'][test_username]
    verification_token = user_data.get('verification_token', secrets.token_urlsafe(32))
else:
    # Create user
    verification_token = secrets.token_urlsafe(32)
    users_data.setdefault('users', {})[test_username] = {
        'password': hash_password(test_password),
        'role': 'user',
        'email': test_email,
        'email_verified': False,
        'verification_token': verification_token,
        'verification_expires': (datetime.now() + timedelta(hours=24)).isoformat(),
        'created': datetime.now().isoformat(),
        'clients': [],
        'subscription': {
            'tier': 'free',
            'status': 'active',
            'created': datetime.now().isoformat(),
            'expires': None
        },
        'usage': {
            'bandwidth_used_gb': 0,
            'month_start': datetime.now().replace(day=1).isoformat()
        }
    }
    
    # Save users.json
    with open(users_file, 'w') as f:
        json.dump(users_data, f, indent=2)
    
    print(f'✅ Test account created!')
    print(f'   Username: {test_username}')
    print(f'   Email: {test_email}')
    print(f'   Password: {test_password}')

print(f'   Verification token: {verification_token}')
print()

# Test 2: Send verification email using email_api
print('=' * 60)
print('📧 Sending Verification Email via email_api')
print('=' * 60)
print()

try:
    from email_api import send_verification_email
    
    success, msg = send_verification_email(test_email, test_username, verification_token)
    if success:
        print(f'✅ Verification email sent successfully!')
        print(f'   Message: {msg}')
    else:
        print(f'❌ Failed to send verification email: {msg}')
except Exception as e:
    print(f'❌ Error sending verification email: {e}')
    import traceback
    traceback.print_exc()

print()
print('=' * 60)
print('✅ Test Complete!')
print('=' * 60)
print()
print('Summary:')
print(f'  • Test account: {test_username} / {test_password}')
print(f'  • Email: {test_email}')
print(f'  • Check your email inbox for test emails!')
print()

