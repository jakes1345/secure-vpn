#!/bin/bash
# Quick ISO Rebuild - Uses /tmp to avoid NTFS mount issues

echo "🔄 Quick PhazeOS ISO Rebuild"
echo "Building in /tmp (native Linux FS) to avoid mount issues..."

# Use /tmp for build (native Linux filesystem)
BUILD_DIR="/tmp/phazeos-build-$(date +%s)"
SOURCE_DIR="/media/jack/Liunux/secure-vpn/phazeos-build"

mkdir -p "$BUILD_DIR/out"

# Copy build files to /tmp
# Copy build files to /tmp
echo "📋 Copying build configuration..."
cp -r "$SOURCE_DIR"/* "$BUILD_DIR/"

# Copy Artifacts from Project Root
PROJECT_ROOT="/media/jack/Liunux/secure-vpn"
cp "$PROJECT_ROOT/PhazeBrowser-v1.0-Linux.tar.xz" "$BUILD_DIR/" 2>/dev/null || echo "Warning: Browser tarball missing"
cp "$PROJECT_ROOT/phazeos_customize.sh" "$BUILD_DIR/"
cp "$PROJECT_ROOT/setup-ai-pod.sh" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/phazeos-construct" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/phazeos-setup-gui" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/phazevpn-protocol-go" "$BUILD_DIR/"


# Run Docker build with /tmp mount
echo "🐳 Starting Docker build..."
docker run --privileged --rm \
  -v "$BUILD_DIR:/build" \
  phazeos-builder /build/entrypoint.sh | tee /media/jack/Liunux/secure-vpn/phazeos_rebuild.log

# Copy ISO back to original location
echo "📦 Copying ISO to project directory..."
if [ -f "$BUILD_DIR/out"/*.iso ]; then
  cp "$BUILD_DIR/out"/*.iso "/media/jack/Liunux/secure-vpn/phazeos-build/out/"
  ISO_FILE=$(ls "$BUILD_DIR/out"/*.iso)
  ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)
  
  echo "=========================================="
  echo "✅ SUCCESS! ISO Created!"
  echo "📦 Size: $ISO_SIZE"
  echo "📁 Location: /media/jack/Liunux/secure-vpn/phazeos-build/out/"
  echo "=========================================="
  
  # Cleanup /tmp
  rm -rf "$BUILD_DIR"
else
  echo "❌ ISO not found in $BUILD_DIR/out/"
  echo "Check log: /media/jack/Liunux/secure-vpn/phazeos_rebuild.log"
  ls -lah "$BUILD_DIR/out/"
fi
