# Fix EMAIL_SERVICE_PASSWORD Error

## 🐛 Problem

The signup page shows:
```
⚠️ Account created but failed to send verification email. 
Please contact support. Error: EMAIL_SERVICE_PASSWORD not set. 
Email service requires authentication.
```

## ✅ Solution

The `EMAIL_SERVICE_PASSWORD` environment variable needs to be set on the VPS where the web portal is running.

### Quick Fix (Run on VPS)

SSH into your VPS and run:

```bash
# Generate a secure password
export EMAIL_SERVICE_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

# Create .env file
cat > /opt/phazevpn/.env << EOF
export EMAIL_SERVICE_PASSWORD='$EMAIL_SERVICE_PASSWORD'
export EMAIL_SERVICE_URL='http://localhost:5005/api/v1/email'
export EMAIL_SERVICE_USER='noreply@mail.phazevpn.com'
export FROM_EMAIL='noreply@phazevpn.com'
EOF

# Source it
source /opt/phazevpn/.env

# Restart web portal
cd /opt/phazevpn/web-portal
pkill -f "python3.*app.py.*web-portal"
source /opt/phazevpn/.env
nohup ../venv/bin/python3 app.py > /var/log/phazeweb.log 2>&1 &

echo "Password: $EMAIL_SERVICE_PASSWORD"
echo "Save this password!"
```

### Using the Setup Script

From your local machine:

```bash
cd /media/jack/Liunux/secure-vpn
./setup_email_password.sh
```

Or with a custom password:

```bash
./setup_email_password.sh "your-secure-password-here"
```

## 🔧 Permanent Fix (Systemd Service)

If you're using systemd, update the service file:

```bash
# Edit service file
sudo nano /etc/systemd/system/phazevpn-web.service

# Add this line in [Service] section:
EnvironmentFile=/opt/phazevpn/.env

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart phazevpn-web
```

## 📋 What This Password Does

The `EMAIL_SERVICE_PASSWORD` is used to authenticate requests from the web portal to the email service API (running on port 5005). It's sent in the `password` field when calling the email service.

## 🔒 Security Notes

1. **Keep it secret**: This password should be kept secure
2. **Use strong password**: At least 32 characters, random
3. **Don't commit to git**: Add `.env` to `.gitignore`
4. **Rotate periodically**: Change it every few months

## ✅ Verify It Works

After setting the password, test signup:

1. Go to `https://phazevpn.com/signup`
2. Create a test account
3. Check if verification email is sent
4. Check email service logs: `tail -f /var/log/phazeemail.log`

---

**After fixing, email verification should work!** 📧
