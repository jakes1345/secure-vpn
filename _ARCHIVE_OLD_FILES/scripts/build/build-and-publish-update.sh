#!/bin/bash
# Build new package version and publish to repository

set -e

echo "=========================================="
echo "Building & Publishing PhazeVPN Update"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "debian/changelog" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Step 1: Build the package
echo "[1/4] Building Debian package..."
./build-deb.sh

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

# Find the built package
PACKAGE_FILE=$(ls -t ../phaze-vpn_*.deb | head -1)
if [ -z "$PACKAGE_FILE" ]; then
    echo "❌ Package file not found!"
    exit 1
fi

echo "✅ Package built: $PACKAGE_FILE"
echo ""

# Step 2: Copy to repository
echo "[2/4] Copying to local repository..."
REPO_DIR="/opt/phazevpn-repo"

if [ ! -d "$REPO_DIR" ]; then
    echo "⚠️  Repository directory doesn't exist. Creating it..."
    sudo mkdir -p "$REPO_DIR"
    sudo chown $USER:$USER "$REPO_DIR"
fi

# Copy package
cp "$PACKAGE_FILE" "$REPO_DIR/"
echo "✅ Package copied to repository"
echo ""

# Step 3: Update repository index
echo "[3/4] Updating repository index..."
cd "$REPO_DIR"
dpkg-scanpackages . /dev/null > Packages
gzip -k -f Packages
echo "✅ Repository index updated"
echo ""

# Step 4: Create/update Release file
echo "[4/4] Creating Release file..."
cat > Release << EOF
Architectures: all
Date: $(date -R)
Description: PhazeVPN Local Repository
Label: PhazeVPN
Origin: PhazeVPN
Suite: stable
Version: 1.0
EOF

# Add MD5, SHA1, SHA256 hashes
echo "MD5Sum:" >> Release
for file in Packages Packages.gz; do
    if [ -f "$file" ]; then
        size=$(stat -c%s "$file")
        md5=$(md5sum "$file" | cut -d' ' -f1)
        echo " $md5 $size $file" >> Release
    fi
done

echo "SHA1:" >> Release
for file in Packages Packages.gz; do
    if [ -f "$file" ]; then
        size=$(stat -c%s "$file")
        sha1=$(sha1sum "$file" | cut -d' ' -f1)
        echo " $sha1 $size $file" >> Release
    fi
done

echo "SHA256:" >> Release
for file in Packages Packages.gz; do
    if [ -f "$file" ]; then
        size=$(stat -c%s "$file")
        sha256=$(sha256sum "$file" | cut -d' ' -f1)
        echo " $sha256 $size $file" >> Release
    fi
done

echo "✅ Release file created"
echo ""

# Summary
echo "=========================================="
echo "✅ UPDATE PUBLISHED!"
echo "=========================================="
echo ""
echo "Package: $PACKAGE_FILE"
echo "Repository: $REPO_DIR"
echo ""
echo "To install/upgrade:"
echo "  sudo apt update"
echo "  sudo apt upgrade phaze-vpn"
echo ""
echo "Or install directly:"
echo "  sudo dpkg -i $PACKAGE_FILE"
echo "  sudo apt-get install -f"
echo ""

