#!/bin/bash
# Manual setup - prompts for secrets interactively

VPS="root@15.204.11.19"
VPS_DIR="/opt/phaze-vpn"

echo "🔧 Setting up environment variables on VPS..."
echo ""

# Prompt for secrets
read -sp "Enter OUTLOOK_CLIENT_SECRET: " OUTLOOK_SECRET
echo ""
read -sp "Enter EMAIL_SERVICE_PASSWORD: " EMAIL_PASS
echo ""

if [ -z "$OUTLOOK_SECRET" ] || [ -z "$EMAIL_PASS" ]; then
    echo "❌ Both values are required!"
    exit 1
fi

echo ""
echo "📝 Creating environment file on VPS..."

ssh $VPS << EOF
cat > $VPS_DIR/.env << ENVFILE
# Outlook OAuth2 Configuration
export OUTLOOK_CLIENT_SECRET='$OUTLOOK_SECRET'
export OUTLOOK_CLIENT_ID='e2a8a108-98d6-49c1-ac99-048ac8576883'
export OUTLOOK_TENANT_ID='1fae0e6a-58b6-4259-8cc8-c3d77317ce09'

# Email Service
export EMAIL_SERVICE_PASSWORD='$EMAIL_PASS'
ENVFILE

chmod 600 $VPS_DIR/.env
echo "✅ Environment file created with secure permissions"
EOF

echo ""
echo "🔄 Restarting web portal..."
ssh $VPS "cd $VPS_DIR/web-portal && source $VPS_DIR/.env && systemctl restart phaze-vpn-web 2>/dev/null || systemctl restart gunicorn 2>/dev/null || (pkill -f 'python.*app.py' && nohup python3 app.py > /dev/null 2>&1 &)"

echo ""
echo "✅ Environment variables set and web portal restarted!"

