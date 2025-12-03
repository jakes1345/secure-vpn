#!/bin/bash
# Automated VPS Update Script
# Syncs files and restarts services cleanly

set -e

VPS_IP="15.204.11.19"
VPS_USER="root"
VPS_PASS="Jakes1328!@"

BASE_DIR="/opt/phaze-vpn"
REMOTE_BASE="/opt/phaze-vpn"

echo "============================================================"
echo "🔄 PHASEVPN VPS UPDATE SCRIPT"
echo "============================================================"

# Function to run command on VPS
run_vps() {
    sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "$1"
}

# Function to sync file
sync_file() {
    local local_file="$1"
    local remote_file="$2"
    if [ -f "$local_file" ]; then
        sshpass -p "$VPS_PASS" scp -o StrictHostKeyChecking=no "$local_file" "$VPS_USER@$VPS_IP:$remote_file"
        echo "✅ Synced: $(basename $local_file)"
        return 0
    else
        echo "⚠️  Not found: $local_file"
        return 1
    fi
}

echo ""
echo "1️⃣  CLEANING UP OLD PROCESSES"
echo "------------------------------------------------------------"
run_vps "pkill -9 -f gunicorn || true"
run_vps "fuser -k 5000/tcp 2>/dev/null || true"
sleep 2
echo "✅ Cleaned up processes"

echo ""
echo "2️⃣  SYNCING FILES TO VPS"
echo "------------------------------------------------------------"

# Web portal files
sync_file "$BASE_DIR/debian/phaze-vpn/opt/phaze-vpn/web-portal/app.py" \
          "$REMOTE_BASE/web-portal/app.py"

sync_file "$BASE_DIR/debian/phaze-vpn/opt/phaze-vpn/web-portal/email_api.py" \
          "$REMOTE_BASE/web-portal/email_api.py"

sync_file "$BASE_DIR/debian/phaze-vpn/opt/phaze-vpn/web-portal/email_smtp.py" \
          "$REMOTE_BASE/web-portal/email_smtp.py"

sync_file "$BASE_DIR/debian/phaze-vpn/opt/phaze-vpn/web-portal/templates/base.html" \
          "$REMOTE_BASE/web-portal/templates/base.html"

sync_file "$BASE_DIR/debian/phaze-vpn/opt/phaze-vpn/web-portal/templates/home.html" \
          "$REMOTE_BASE/web-portal/templates/home.html"

# Service file
sync_file "$BASE_DIR/debian/phaze-vpn/opt/phaze-vpn/web-portal/phazevpn-portal.service" \
          "/etc/systemd/system/phazevpn-portal.service"

echo ""
echo "3️⃣  RELOADING SYSTEMD"
echo "------------------------------------------------------------"
run_vps "systemctl daemon-reload"
echo "✅ Systemd reloaded"

echo ""
echo "4️⃣  RESTARTING SERVICES"
echo "------------------------------------------------------------"
run_vps "systemctl stop phazevpn-portal || true"
sleep 2
run_vps "systemctl start phazevpn-portal"
sleep 5
echo "✅ Service restarted"

echo ""
echo "5️⃣  VERIFYING SERVICE STATUS"
echo "------------------------------------------------------------"
STATUS=$(run_vps "systemctl is-active phazevpn-portal")
if [ "$STATUS" = "active" ]; then
    echo "✅ Service is active"
else
    echo "❌ Service is not active: $STATUS"
    echo ""
    echo "Checking service logs..."
    run_vps "journalctl -u phazevpn-portal --no-pager -n 20"
    exit 1
fi

echo ""
echo "6️⃣  TESTING ENDPOINTS"
echo "------------------------------------------------------------"
sleep 2

test_endpoint() {
    local route="$1"
    local name="$2"
    HTTP_CODE=$(run_vps "curl -s -o /dev/null -w '%{http_code}' http://localhost:5000$route")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "301" ]; then
        echo "✅ $name: $HTTP_CODE"
        return 0
    else
        echo "❌ $name: $HTTP_CODE"
        return 1
    fi
}

test_endpoint "/" "Homepage"
test_endpoint "/login" "Login"
test_endpoint "/signup" "Signup"

echo ""
echo "============================================================"
echo "✅ UPDATE COMPLETE!"
echo "============================================================"

