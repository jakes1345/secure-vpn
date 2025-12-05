#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/secure-vpn/web-portal")
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
        <body style="font-family: Arial, sans-serif;">
            <h1 style="color: #4a9eff;">Welcome to PhazeVPN!</h1>
            <p>Hi <strong>FlapJack212</strong>,</p>
            <p>Your account has been successfully created!</p>
            <p>You can now login at: <a href="https://phazevpn.duckdns.org/login">phazevpn.duckdns.org</a></p>
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

