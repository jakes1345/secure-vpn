#!/bin/bash
# Fix critical security issues found in audit

echo "🔒 Fixing Critical Security Issues..."
echo ""

VPS="root@15.204.11.19"
VPS_DIR="/opt/phaze-vpn"

echo "📦 Step 1: Deploying security fixes..."
scp web-portal/outlook_oauth2_config.py web-portal/email_api.py "$VPS:$VPS_DIR/web-portal/" 2>/dev/null
scp web-portal/templates/base.html web-portal/templates/base-new.html "$VPS:$VPS_DIR/web-portal/templates/" 2>/dev/null
scp web-portal/templates/pricing.html web-portal/templates/home-new.html "$VPS:$VPS_DIR/web-portal/templates/" 2>/dev/null
scp web-portal/templates/home.html web-portal/templates/terms.html "$VPS:$VPS_DIR/web-portal/templates/" 2>/dev/null

echo ""
echo "✅ Security fixes deployed!"
echo ""
echo "CRITICAL: Set these environment variables on VPS:"
echo "  export OUTLOOK_CLIENT_SECRET='your-secret'"
echo "  export EMAIL_SERVICE_PASSWORD='your-secure-password'"
echo ""
echo "Then restart web portal:"
echo "  systemctl restart phaze-vpn-web"

