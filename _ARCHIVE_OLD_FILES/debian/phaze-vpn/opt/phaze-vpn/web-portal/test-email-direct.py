#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/secure-vpn/web-portal")
from email_api import send_welcome_email

success, msg = send_welcome_email("bigjacob710@gmail.com", "FlapJack212")
print(f"SUCCESS: {success}")
print(f"MESSAGE: {msg}")

