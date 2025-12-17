#!/bin/bash
# Create easy-to-use installer that works with Ubuntu Software Center

set -e

echo "================================================================================"
echo "📦 CREATING EASY INSTALLER FOR UBUNTU SOFTWARE CENTER"
echo "================================================================================"
echo ""

# Build the .deb package
echo "1️⃣ Building .deb package..."
cd phazevpn-client

# Check if rebuild script exists, otherwise use dpkg-deb directly
if [ -f "rebuild-linux-package.sh" ]; then
    ./rebuild-linux-package.sh || {
    echo "❌ Package build failed!"
    exit 1
}

# Find the built package
PACKAGE=$(find installers -name "phazevpn-client_*.deb" | head -1)

if [ -z "$PACKAGE" ]; then
    echo "❌ Package not found!"
    exit 1
fi

echo ""
echo "✅ Package built: $PACKAGE"
echo ""

# Create install instructions
cat > installers/INSTALL-INSTRUCTIONS.txt << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔒 PhazeVPN Client - Easy Installation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 EASY INSTALLATION (3 WAYS):

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
METHOD 1: Double-Click Installation (Easiest!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Double-click the .deb file
2. Click "Install" in Ubuntu Software
3. Enter your password
4. Done! Updates will show automatically!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
METHOD 2: Command Line (Quick)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

sudo apt install ./phazevpn-client_*.deb

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
METHOD 3: Via Repository (Best for Updates)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The installer automatically adds the repository, so updates appear automatically!

To install via repository:
   sudo apt update
   sudo apt install phazevpn-client

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ WHAT HAPPENS AFTER INSTALLATION:

✅ PhazeVPN Client installed
✅ Repository automatically added
✅ Future updates show in Update Manager automatically
✅ Can update via Ubuntu Software Center
✅ Can update via Software Updater
✅ Can update via: sudo apt update && sudo apt upgrade

🎉 NO MANUAL STEPS NEEDED - IT'S AUTOMATIC!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

echo ""
echo "================================================================================"
echo "✅ EASY INSTALLER READY!"
echo "================================================================================"
echo ""
echo "📦 Package: $PACKAGE"
echo ""
echo "📱 USERS CAN NOW:"
echo "   1. Double-click .deb file → Install via Ubuntu Software"
echo "   2. Repository is automatically added"
echo "   3. Updates show in Update Manager automatically!"
echo ""
echo "✨ No manual commands needed - it's all automatic!"
echo ""

