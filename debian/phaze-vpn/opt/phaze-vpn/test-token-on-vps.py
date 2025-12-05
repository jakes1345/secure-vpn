#!/usr/bin/env python3
"""
Test OAuth2 token and check permissions
"""

from paramiko import SSHClient, AutoAddPolicy

VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = "Jakes1328!@"

try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    print("=" * 60)
    print("🔍 TESTING OAUTH2 TOKEN")
    print("=" * 60)
    print("")
    
    # Test token acquisition
    test_cmd = """cd /opt/secure-vpn/web-portal && python3 -c "
import sys
sys.path.insert(0, '/opt/secure-vpn/web-portal')
from email_outlook_oauth2 import get_access_token
import json

print('Getting access token...')
token, error = get_access_token()

if token:
    print('✅ Token obtained!')
    print(f'   Token (first 20 chars): {token[:20]}...')
    
    # Decode token to see claims (basic check)
    import base64
    try:
        parts = token.split('.')
        if len(parts) >= 2:
            payload = parts[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            claims = json.loads(decoded)
            print(f'   Scopes: {claims.get(\"scp\", \"N/A\")}')
            print(f'   Roles: {claims.get(\"roles\", \"N/A\")}')
            print(f'   App ID: {claims.get(\"appid\", \"N/A\")}')
    except Exception as e:
        print(f'   Could not decode token: {e}')
else:
    print('❌ Failed to get token')
    print(f'   Error: {error}')
"
"""
    
    stdin, stdout, stderr = ssh.exec_command(test_cmd)
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    print(output)
    if error:
        print("Errors:")
        print(error)
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

