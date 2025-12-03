#!/bin/bash
# Setup Payment Credentials for PhazeVPN

VPN_DIR="/opt/secure-vpn"
SETTINGS_FILE="$VPN_DIR/logs/payment-settings.json"

echo "=========================================="
echo "Setting up Payment Credentials"
echo "=========================================="
echo ""

# Create settings file with credentials
mkdir -p "$VPN_DIR/logs"

cat > "$SETTINGS_FILE" << 'EOF'
{
  "venmo_username": "@jakes1328",
  "cashapp_username": "$jakes1328",
  "cashapp_tag": "$jakes1328",
  "stripe_enabled": true,
  "stripe_publishable_key": "pk_live_51RuicO0VrYrqUK2QujhpNXosg4Y7b9ZXCW3zuT8wVgV2Y1Uvil5mUWvQm3QuD8EMcRYuOkoPwgfetairsnMCNE9J00wy2dNEqk",
  "stripe_secret_key": "YOUR_SECRET_KEY_HERE"
}
EOF

echo "✅ Payment settings file created: $SETTINGS_FILE"
echo ""
echo "⚠️  IMPORTANT: You need to add your Stripe SECRET key!"
echo ""
echo "Your Stripe publishable key is already added (safe to share)"
echo "But you need your SECRET key (starts with sk_live_) for backend processing"
echo ""
echo "To add your secret key:"
echo "1. Go to: https://dashboard.stripe.com/apikeys"
echo "2. Copy your SECRET key (starts with sk_live_)"
echo "3. Edit: $SETTINGS_FILE"
echo "4. Replace 'YOUR_SECRET_KEY_HERE' with your actual secret key"
echo ""
echo "OR run this script with your secret key as argument:"
echo "  ./SETUP-PAYMENT-CREDENTIALS.sh YOUR_SECRET_KEY"
echo ""

# If secret key provided as argument
if [ ! -z "$1" ]; then
    SECRET_KEY="$1"
    echo "Adding secret key to settings..."
    
    # Update the secret key in the file
    python3 << PYEOF
import json
import sys

settings_file = "$SETTINGS_FILE"
secret_key = "$SECRET_KEY"

try:
    with open(settings_file, 'r') as f:
        settings = json.load(f)
    
    settings['stripe_secret_key'] = secret_key
    
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)
    
    print("✅ Secret key added successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
PYEOF
fi

echo ""
echo "Current settings:"
cat "$SETTINGS_FILE" | python3 -m json.tool 2>/dev/null || cat "$SETTINGS_FILE"
echo ""

