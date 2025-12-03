#!/usr/bin/env python3
import json
import sys
sys.path.insert(0, "/opt/secure-vpn/web-portal")

# Fix user account
with open('/opt/secure-vpn/users.json', 'r') as f:
    users_data = json.load(f)

if 'users' in users_data:
    users = users_data['users']
else:
    users = users_data

if 'FlapJack212' in users:
    users['FlapJack212']['email'] = 'bigjacob710@gmail.com'
    print('✅ Email added to account')
    
    if 'users' in users_data:
        users_data['users'] = users
        with open('/opt/secure-vpn/users.json', 'w') as f:
            json.dump(users_data, f, indent=2)
    else:
        with open('/opt/secure-vpn/users.json', 'w') as f:
            json.dump(users, f, indent=2)
    
    print('✅ Account saved')
else:
    print('❌ User not found')
    sys.exit(1)

# Send email
print('')
print('📧 Sending welcome email...')
from mailjet_rest import Client
from mailjet_config import MAILJET_API_KEY, MAILJET_SECRET_KEY, FROM_EMAIL, FROM_NAME

mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_SECRET_KEY), version="v3.1")

data = {
    "Messages": [{
        "From": {"Email": FROM_EMAIL, "Name": FROM_NAME},
        "To": [{"Email": "bigjacob710@gmail.com"}],
        "Subject": "Welcome to PhazeVPN!",
        "HTMLPart": """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #4a9eff;">Welcome to PhazeVPN!</h1>
                <p>Hi <strong>FlapJack212</strong>,</p>
                <p>Your account has been successfully created!</p>
                <p>You can now:</p>
                <ul>
                    <li>Login to the dashboard</li>
                    <li>Create VPN client configurations</li>
                    <li>Download config files or QR codes</li>
                </ul>
                <p><a href="https://phazevpn.duckdns.org/login" style="background: #4a9eff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Login Now</a></p>
            </div>
        </body>
        </html>
        """
    }]
}

result = mailjet.send.create(data=data)
print(f"Status: {result.status_code}")
if result.status_code == 200:
    print("✅ Email sent successfully!")
    print(f"Message ID: {result.json()['Messages'][0]['To'][0]['MessageID']}")
else:
    print(f"❌ Error: {result.text}")

