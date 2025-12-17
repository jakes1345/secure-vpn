#!/bin/bash
# Update package version for new release

if [ -z "$1" ]; then
    echo "Usage: $0 <new-version>"
    echo "Example: $0 1.0.3"
    exit 1
fi

NEW_VERSION="$1"
DATE=$(date -R)

echo "📦 Updating package version to $NEW_VERSION..."

# Update control file
sed -i "s/^Version: .*/Version: $NEW_VERSION/" debian/phaze-vpn/DEBIAN/control
echo "✅ Updated debian/phaze-vpn/DEBIAN/control"

# Add to changelog
sed -i "1i\\
phaze-vpn ($NEW_VERSION) unstable; urgency=medium\\
\\
  * Update: $(date +%Y-%m-%d)\\
\\
 -- PhazeVPN Team <admin@phazevpn.com>  $DATE\\
\\
" debian/changelog
echo "✅ Updated debian/changelog"

echo ""
echo "✅ Version updated to $NEW_VERSION"
echo ""
echo "Next steps:"
echo "  1. Build package: ./build-deb.sh"
echo "  2. Update repo: ./setup-auto-updates.sh"
echo "  3. Users can update: sudo apt update && sudo apt upgrade phaze-vpn"
echo ""

