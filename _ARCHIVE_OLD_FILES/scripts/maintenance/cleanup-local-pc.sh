#!/bin/bash
# Clean up PhazeVPN files from local PC
# Only keeps essential files for building/deploying

set -e

echo "=========================================="
echo "Cleaning Up PhazeVPN Files from Local PC"
echo "=========================================="
echo ""
echo "This will remove:"
echo "  - GUI executables and build artifacts"
echo "  - Local test files"
echo "  - Temporary files"
echo ""
echo "This will KEEP:"
echo "  - Source code files"
echo "  - Build scripts"
echo "  - Deployment scripts"
echo "  - Documentation"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo "🧹 Cleaning up..."

# Remove GUI executables
rm -f PhazeVPN-Client-*
rm -f phazevpn-client
rm -f vpn-gui
rm -rf gui-build/
rm -rf build/
rm -rf dist/
rm -f *.spec

# Remove Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Remove test files
rm -f test-*.py
rm -f *-test.py
rm -f test_*.py

# Remove temporary files
rm -f *.log
rm -f *.tmp
rm -f .*.swp
rm -f *~

# Remove old backups (keep recent ones)
find . -name "*.bak" -mtime +7 -delete 2>/dev/null || true
find . -name "*backup*" -type f -mtime +30 -delete 2>/dev/null || true

# Remove desktop launchers (they're on VPS)
rm -f *.desktop
rm -f phazevpn-client.desktop

echo "✅ Cleanup complete!"
echo ""
echo "Remaining files are for building/deploying only."
echo "All runtime files should be on the VPS."

