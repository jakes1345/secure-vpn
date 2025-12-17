#!/bin/bash
# Verify all commercial features are included in build

echo "=========================================="
echo "🔍 Verifying Commercial Features"
echo "=========================================="
echo ""

ERRORS=0

# Check payment files
echo "📦 Checking Payment System..."
if [ -f "web-portal/payment_integrations.py" ]; then
    echo "  ✅ payment_integrations.py"
else
    echo "  ❌ MISSING: payment_integrations.py"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "web-portal/templates/payment.html" ]; then
    echo "  ✅ payment.html template"
else
    echo "  ❌ MISSING: payment.html template"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "web-portal/templates/admin/payment-settings.html" ]; then
    echo "  ✅ payment-settings.html template"
else
    echo "  ❌ MISSING: payment-settings.html template"
    ERRORS=$((ERRORS + 1))
fi

# Check subscription files
echo ""
echo "📦 Checking Subscription System..."
if [ -f "subscription-manager.py" ]; then
    echo "  ✅ subscription-manager.py"
else
    echo "  ❌ MISSING: subscription-manager.py"
    ERRORS=$((ERRORS + 1))
fi

# Check email files
echo ""
echo "📦 Checking Email System..."
EMAIL_FILES=(
    "web-portal/email_api.py"
    "web-portal/email_mailjet.py"
    "web-portal/email_smtp.py"
    "web-portal/email_util.py"
    "web-portal/mailjet_config.py"
    "web-portal/smtp_config.py"
)

for file in "${EMAIL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $(basename $file)"
    else
        echo "  ❌ MISSING: $file"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check CMakeLists.txt includes
echo ""
echo "📦 Checking CMake Build System..."
if grep -q "payment_integrations.py" web-portal/CMakeLists.txt; then
    echo "  ✅ payment_integrations.py in CMakeLists.txt"
else
    echo "  ⚠️  payment_integrations.py not explicitly listed (may be included via directory)"
fi

if grep -q "subscription-manager.py" CMakeLists.txt; then
    echo "  ✅ subscription-manager.py in CMakeLists.txt"
else
    echo "  ⚠️  subscription-manager.py not explicitly listed (may be included via directory)"
fi

# Check app.py has payment routes
echo ""
echo "📦 Checking Web Portal Routes..."
if grep -q "@app.route.*payment" web-portal/app.py; then
    echo "  ✅ Payment routes found in app.py"
else
    echo "  ❌ MISSING: Payment routes in app.py"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "SUBSCRIPTION_TIERS" web-portal/app.py; then
    echo "  ✅ Subscription tiers found in app.py"
else
    echo "  ❌ MISSING: Subscription tiers in app.py"
    ERRORS=$((ERRORS + 1))
fi

# Summary
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ All commercial features verified!"
    echo "=========================================="
    exit 0
else
    echo "❌ Found $ERRORS missing features!"
    echo "=========================================="
    exit 1
fi

