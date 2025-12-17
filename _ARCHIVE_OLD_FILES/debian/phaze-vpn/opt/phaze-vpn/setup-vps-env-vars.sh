#!/bin/bash
# Set environment variables on VPS and restart web portal

VPS="root@15.204.11.19"
VPS_DIR="/opt/phaze-vpn"

echo "🔧 Setting up environment variables on VPS..."
echo ""

# Check if secrets are provided
if [ -z "$OUTLOOK_CLIENT_SECRET" ] || [ -z "$EMAIL_SERVICE_PASSWORD" ]; then
    echo "⚠️  Environment variables not set!"
    echo ""
    echo "Set them first:"
    echo "  export OUTLOOK_CLIENT_SECRET='your-secret'"
    echo "  export EMAIL_SERVICE_PASSWORD='your-secure-password'"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "📝 Creating environment file on VPS..."
ssh $VPS << EOF
cat > $VPS_DIR/.env << ENVFILE
# Outlook OAuth2 Configuration
export OUTLOOK_CLIENT_SECRET='$OUTLOOK_CLIENT_SECRET'
export OUTLOOK_CLIENT_ID='e2a8a108-98d6-49c1-ac99-048ac8576883'
export OUTLOOK_TENANT_ID='1fae0e6a-58b6-4259-8cc8-c3d77317ce09'

# Email Service
export EMAIL_SERVICE_PASSWORD='$EMAIL_SERVICE_PASSWORD'

# Other email services (if needed)
export MAILJET_API_KEY=\${MAILJET_API_KEY:-''}
export MAILJET_SECRET_KEY=\${MAILJET_SECRET_KEY:-''}
export SENDGRID_API_KEY=\${SENDGRID_API_KEY:-''}
export MAILGUN_API_KEY=\${MAILGUN_API_KEY:-''}
export SMTP_PASSWORD=\${SMTP_PASSWORD:-''}
ENVFILE

echo "✅ Environment file created"
chmod 600 $VPS_DIR/.env
echo "✅ Permissions set (read-only for owner)"
EOF

echo ""
echo "🔄 Restarting web portal with new environment..."
ssh $VPS << EOF
# Source environment file and restart
source $VPS_DIR/.env

# Restart web portal service
systemctl restart phaze-vpn-web 2>/dev/null || \
systemctl restart gunicorn 2>/dev/null || \
(cd $VPS_DIR/web-portal && pkill -f 'python.*app.py' && \
 source $VPS_DIR/.env && \
 nohup python3 app.py > /dev/null 2>&1 &)

sleep 2

# Verify it's running
if pgrep -f 'python.*app.py' > /dev/null; then
    echo "✅ Web portal restarted successfully"
else
    echo "⚠️  Web portal may not be running - check manually"
fi
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "Environment variables are now set on VPS."
echo "The web portal has been restarted with the new configuration."

