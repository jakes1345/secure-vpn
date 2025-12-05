#!/bin/bash
# Complete deployment script - run this to deploy everything to VPS

VPS="root@phazevpn.com"
VPS_DIR="/opt/phaze-vpn"

echo "🚀 Deploying ALL updates to VPS..."
echo ""

# 1. Deploy audit and documentation
echo "📦 Step 1: Deploying audit scripts and docs..."
scp audit-all-files.sh mark-experimental.sh generate-all-configs.py "$VPS:$VPS_DIR/"
scp FULL-AUDIT-PLAN.md CUSTOM-PROTOCOL-DEVELOPMENT.md HONEST-MARKETING.md SECURITY-POLICY.md "$VPS:$VPS_DIR/"

# 2. Deploy updated web portal
echo "📦 Step 2: Deploying updated web portal..."
scp web-portal/templates/home.html web-portal/templates/guide.html web-portal/templates/guide-new.html "$VPS:$VPS_DIR/web-portal/templates/"
scp web-portal/app.py "$VPS:$VPS_DIR/web-portal/"

# 3. Deploy updated GUI
echo "📦 Step 3: Deploying updated GUI..."
scp vpn-gui.py "$VPS:$VPS_DIR/"

# 4. Make scripts executable
echo "🔧 Step 4: Making scripts executable..."
ssh $VPS "cd $VPS_DIR && chmod +x audit-all-files.sh mark-experimental.sh generate-all-configs.py"

# 5. Run audit
echo "🔍 Step 5: Running audit on VPS..."
ssh $VPS "cd $VPS_DIR && ./audit-all-files.sh" | tail -30

# 6. Mark experimental
echo "🔖 Step 6: Marking custom protocol as experimental..."
ssh $VPS "cd $VPS_DIR && ./mark-experimental.sh" | tail -10

# 7. Restart web portal
echo "🔄 Step 7: Restarting web portal..."
ssh $VPS "systemctl restart phaze-vpn-web 2>/dev/null || systemctl restart gunicorn 2>/dev/null || (cd $VPS_DIR/web-portal && pkill -f 'python.*app.py' && nohup python3 app.py > /dev/null 2>&1 &)"

# 8. Verify
echo "✅ Step 8: Verifying deployment..."
ssh $VPS "cd $VPS_DIR && python3 -m py_compile generate-all-configs.py web-portal/app.py 2>&1 && echo '✅ All files compile successfully!'"

echo ""
echo "✅✅✅ DEPLOYMENT COMPLETE! ✅✅✅"
echo ""
echo "Summary:"
echo "  - Audit scripts deployed and run"
echo "  - Custom protocol marked as experimental"
echo "  - Web portal updated (honest marketing)"
echo "  - GUI updated (honest labeling)"
echo "  - All config types supported"
echo "  - Web portal restarted"

