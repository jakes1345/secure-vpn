# 🔑 Mailgun API Key Information

## 📋 Your API Keys

### ✅ Main API Key (Currently Active)
**Key:** `YOUR_MAILGUN_API_KEY_HERE`
- **Source:** Created from API Keys section in Mailgun dashboard
- **Status:** ✅ This is the one you created manually
- **Location:** Set as `MAILGUN_API_KEY` in `mailgun_config.py`

### ❓ Alternative API Key (Backup)
**Key:** `YOUR_MAILGUN_API_KEY_BACKUP_HERE`
- **Source:** Unknown (might be from webhook or another source)
- **Status:** Stored as backup
- **Location:** Set as `MAILGUN_API_KEY_ALT` in `mailgun_config.py`

---

## 🧪 Testing Which Key Works

### Run Test Script:
```bash
cd web-portal
python3 test-both-api-keys.py
```

This will:
1. Test both API keys
2. Show which one works (returns 200 status)
3. Show which one fails (and why)

### Manual Test:
```python
from email_api import send_welcome_email

# Test with main key (currently configured)
success, msg = send_welcome_email('your-authorized-email@example.com', 'testuser')
print(f"{'✅' if success else '❌'} {msg}")
```

---

## 🔄 Switching Keys

If the main key doesn't work, switch to the alternative:

### Option 1: Edit `mailgun_config.py`
```python
# Swap them
MAILGUN_API_KEY = "YOUR_MAILGUN_API_KEY_HERE"  # Alternative
MAILGUN_API_KEY_ALT = "YOUR_MAILGUN_API_KEY_BACKUP_HERE"  # Original
```

### Option 2: Use Environment Variable
```bash
export MAILGUN_API_KEY="YOUR_MAILGUN_API_KEY_HERE"
```

---

## 📝 Current Configuration

**Active Key:** Main API key (from API Keys section)
**Domain:** `sandboxd86c8b1ae85c4017a1ac33054d44e726.mailgun.org`
**Webhook Key:** `a5bad5a2e609358c834ba0e0573ba489`

---

## ⚠️ Important Notes

1. **Account Activation:** Make sure your Mailgun account is activated (check email)
2. **Authorized Recipients:** Sandbox domain can only send to authorized recipients
3. **Key Security:** Never commit `mailgun_config.py` to git (already in `.gitignore`)

---

## 🎯 Next Steps

1. **Activate Mailgun account** (if not done)
2. **Authorize test recipients** in Mailgun dashboard
3. **Run test script** to verify which key works
4. **Use the working key** in production

---

**The main key (from API Keys section) should be the correct one!** ✅

