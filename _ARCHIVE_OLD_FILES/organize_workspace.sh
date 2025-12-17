#!/bin/bash

# Define the Cleanup Target
ARCHIVE_DIR="_ARCHIVE_OLD_FILES"

echo "================================================"
echo "    PhazeVPN Workspace Cleanup & Audit Tool"
echo "================================================"
echo "This script will organize your workspace."
echo "CRITICAL: No files will be deleted. They are moved to $ARCHIVE_DIR"
echo ""

mkdir -p "$ARCHIVE_DIR"

# 1. Define what we KEEP (The "Source of Truth")
# - phazevpn-protocol-go (The Real Go Server + Native GUI)
# - web-portal (The Website)
# - email-service-api (The Email Service)
# - phazebrowser.py (The Browser)
# - deploy_all_to_vps.sh (The Deployment Script)
# - build_native_installer.sh (The Installer Builder)
# - HOW_TO_RUN_EVERYTHING.md (The Guide)
# - OVH-VPS-CREDENTIALS.txt (Credentials)

# 2. Everything else goes to archive
echo "1. Archiving loose scripts and old files..."

# Move all root .py files (except the browser)
mv *.py "$ARCHIVE_DIR/" 2>/dev/null
# Restore phazebrowser.py (we want to keep this one)
mv "$ARCHIVE_DIR/phazebrowser.py" . 2>/dev/null

# Move all root .sh files (except our critical ones)
mv *.sh "$ARCHIVE_DIR/" 2>/dev/null
# Restore critical scripts
mv "$ARCHIVE_DIR/deploy_all_to_vps.sh" . 2>/dev/null
mv "$ARCHIVE_DIR/build_native_installer.sh" . 2>/dev/null
mv "$ARCHIVE_DIR/deploy_to_vps.sh" . 2>/dev/null

# Move all root .md files (except the guide)
mv *.md "$ARCHIVE_DIR/" 2>/dev/null
# Restore guide
mv "$ARCHIVE_DIR/HOW_TO_RUN_EVERYTHING.md" . 2>/dev/null

# Move all root .txt files (except credentials)
mv *.txt "$ARCHIVE_DIR/" 2>/dev/null
mv "$ARCHIVE_DIR/OVH-VPS-CREDENTIALS.txt" . 2>/dev/null

# Move miscellaneous
mv *.json *.log *.xml *.csproj "$ARCHIVE_DIR/" 2>/dev/null

# 3. Handle Directories
echo "2. Archiving old directories..."

# Move legacy folders
mv legacy-python-client "$ARCHIVE_DIR/" 2>/dev/null
mv phazevpn-client "$ARCHIVE_DIR/" 2>/dev/null # This is the old python client structure
mv mobile-app "$ARCHIVE_DIR/" 2>/dev/null
mv debian "$ARCHIVE_DIR/" 2>/dev/null
mv build "$ARCHIVE_DIR/" 2>/dev/null
mv dist "$ARCHIVE_DIR/" 2>/dev/null
mv scripts "$ARCHIVE_DIR/" 2>/dev/null
mv tests "$ARCHIVE_DIR/" 2>/dev/null
mv logs "$ARCHIVE_DIR/" 2>/dev/null
mv certs "$ARCHIVE_DIR/" 2>/dev/null
mv config "$ARCHIVE_DIR/" 2>/dev/null
mv cmake "$ARCHIVE_DIR/" 2>/dev/null
mv unified-web-portal "$ARCHIVE_DIR/" 2>/dev/null # Redundant
mv web-admin "$ARCHIVE_DIR/" 2>/dev/null

echo "3. Organizing Project Structure..."
# Ensuring the clean state looks good
echo "   - phazevpn-protocol-go (NATIVE SERVER & CLIENT)"
echo "   - web-portal           (WEBSITE)"
echo "   - email-service-api    (EMAIL)"
echo "   - phazebrowser.py      (BROWSER)"

ls -F

echo ""
echo "================================================"
echo "✅ CLEANUP COMPLETE"
echo "Your workspace now only contains the active, real projects."
echo "All old junk is in: $ARCHIVE_DIR"
echo "================================================"
