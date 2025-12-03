#!/bin/bash
# Build macOS .app bundle

set -e

APP_NAME="PhazeVPN"
APP_DIR="$APP_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

echo "Building macOS app bundle..."

# Create app bundle structure
rm -rf "$APP_DIR"
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Copy executable or Python script
if [ -f dist/phazevpn-client ]; then
    cp dist/phazevpn-client "$MACOS_DIR/$APP_NAME"
    chmod +x "$MACOS_DIR/$APP_NAME"
else
    # Create launcher script
    cat > "$MACOS_DIR/$APP_NAME" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../Resources"
python3 phazevpn-client.py
EOF
    chmod +x "$MACOS_DIR/$APP_NAME"
    cp phazevpn-client.py "$RESOURCES_DIR/"
fi

# Create Info.plist
cat > "$CONTENTS_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.phazevpn.client</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create DMG
echo "Creating DMG..."
hdiutil create -volname "$APP_NAME" -srcfolder "$APP_DIR" -ov -format UDZO "installers/$APP_NAME.dmg" 2>/dev/null || {
    echo "⚠ DMG creation failed, but .app bundle created: $APP_DIR"
    cp -r "$APP_DIR" "dist/macos/"
}

echo "✅ macOS app bundle created: $APP_DIR"
echo "✅ DMG created: installers/$APP_NAME.dmg (if successful)"

