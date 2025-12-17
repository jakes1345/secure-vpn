# Quick Fix: EMAIL_SERVICE_PASSWORD Error

## 🚀 Fastest Fix (Run on VPS)

SSH into your VPS and run these commands:

```bash
# Generate password and create .env file
EMAIL_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
cat > /opt/phazevpn/.env << EOF
export EMAIL_SERVICE_PASSWORD='$EMAIL_PASS'
export EMAIL_SERVICE_URL='http://localhost:5005/api/v1/email'
export EMAIL_SERVICE_USER='noreply@mail.phazevpn.com'
export FROM_EMAIL='noreply@phazevpn.com'
EOF

# Restart web portal
cd /opt/phazevpn/web-portal
pkill -f "python3.*app.py.*web-portal"
source /opt/phazevpn/.env
nohup ../venv/bin/python3 app.py > /var/log/phazeweb.log 2>&1 &

echo "Password: $EMAIL_PASS"
```

**Or use the script:**

```bash
# Upload fix_email_password_vps.sh to VPS, then:
chmod +x fix_email_password_vps.sh
./fix_email_password_vps.sh
```

## ✅ What This Does

1. Generates a secure random password
2. Creates `/opt/phazevpn/.env` with the password
3. Restarts the web portal with the password loaded
4. Shows you the password to save

## 🧪 Test It

After running the fix:

1. Go to `https://phazevpn.com/signup`
2. Create a test account
3. Check if verification email is sent (no error message)

## 📝 Notes

- The password is saved in `/opt/phazevpn/.env`
- The web portal loads it on startup
- Keep the password secure - don't share it publicly

---

**This should fix the email verification issue immediately!** 📧
