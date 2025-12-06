#!/bin/bash
# Add a .deb package to the PhazeVPN APT repository

set -e

REPO_DIR="/var/www/phazevpn-repo"
PACKAGE_FILE="$1"

if [ -z "$PACKAGE_FILE" ]; then
    echo "Usage: $0 <package.deb>"
    echo "Example: $0 phaze-vpn_1.0.1_amd64.deb"
    exit 1
fi

if [ ! -f "$PACKAGE_FILE" ]; then
    echo "❌ Error: Package file not found: $PACKAGE_FILE"
    exit 1
fi

if [ "$EUID" -ne 0 ]; then 
    echo "❌ Error: This script must be run as root (use sudo)"
    exit 1
fi

if [ ! -d "$REPO_DIR" ]; then
    echo "❌ Error: Repository not set up. Run setup-apt-repository.sh first"
    exit 1
fi

echo "=========================================="
echo "Adding Package to Repository"
echo "=========================================="
echo ""
echo "Package: $PACKAGE_FILE"
echo ""

# Extract package info
PACKAGE_NAME=$(dpkg-deb -f "$PACKAGE_FILE" Package)
VERSION=$(dpkg-deb -f "$PACKAGE_FILE" Version)
ARCH=$(dpkg-deb -f "$PACKAGE_FILE" Architecture)

echo "Package: $PACKAGE_NAME"
echo "Version: $VERSION"
echo "Architecture: $ARCH"
echo ""

# Remove old version if exists
echo "Removing old versions..."
reprepro -b "$REPO_DIR" remove stable "$PACKAGE_NAME" 2>/dev/null || true

# Add new package
echo "Adding new package..."
reprepro -b "$REPO_DIR" includedeb stable "$PACKAGE_FILE"

echo ""
echo "✅ Package added to repository!"
echo ""
echo "Repository updated. Users can now:"
echo "  sudo apt update"
echo "  sudo apt install $PACKAGE_NAME"
echo ""
echo "Or upgrade existing installations:"
echo "  sudo apt update && sudo apt upgrade $PACKAGE_NAME"

