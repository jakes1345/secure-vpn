#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/secure-vpn/web-portal")
from mailjet_rest import Client
from mailjet_config import MAILJET_API_KEY, MAILJET_SECRET_KEY, FROM_EMAIL, FROM_NAME

print("="*60)
print("📧 TESTING EMAIL SEND")
print("="*60)
print("")
print(f"API Key: {MAILJET_API_KEY[:20]}...")
print(f"Secret: {MAILJET_SECRET_KEY[:20]}...")
print(f"From: {FROM_EMAIL}")
print(f"To: bigjacob710@gmail.com")
print("")

mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_SECRET_KEY), version="v3.1")

data = {
    "Messages": [{
        "From": {"Email": FROM_EMAIL, "Name": FROM_NAME},
        "To": [{"Email": "bigjacob710@gmail.com"}],
        "Subject": "Welcome to PhazeVPN - FlapJack212",
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
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #666; font-size: 12px;">This is an automated message from PhazeVPN</p>
            </div>
        </body>
        </html>
        """
    }]
}

try:
    result = mailjet.send.create(data=data)
    print(f"Status Code: {result.status_code}")
    print("")
    
    if result.status_code == 200:
        response = result.json()
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print("")
        msg = response.get("Messages", [{}])[0]
        to_info = msg.get("To", [{}])[0]
        print(f"Message ID: {to_info.get('MessageID', 'N/A')}")
        print(f"To: {to_info.get('Email', 'N/A')}")
        print("")
        print("📬 Check your inbox (and spam folder): bigjacob710@gmail.com")
        print("")
        print("Full response:")
        print(response)
    else:
        print(f"❌ FAILED!")
        print(f"Response: {result.text}")
        print("")
        print("This might mean:")
        print("  - FROM email not verified in Mailjet")
        print("  - Account issue")
        print("  - API key issue")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("")
print("="*60)

