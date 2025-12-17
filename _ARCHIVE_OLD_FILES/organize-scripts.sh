#!/bin/bash
# Organize scripts into proper directory structure
# This script moves scripts from root directory into organized folders

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Organizing Scripts"
echo "=========================================="
echo ""

# Create directory structure
mkdir -p scripts/{setup,deploy,check,build,connect,maintenance,utils}

# Move setup scripts
echo "Moving setup scripts..."
mv setup-*.py scripts/setup/ 2>/dev/null || true
mv setup-*.sh scripts/setup/ 2>/dev/null || true
mv auto-setup*.py scripts/setup/ 2>/dev/null || true
mv auto-setup*.sh scripts/setup/ 2>/dev/null || true
mv complete-setup.py scripts/setup/ 2>/dev/null || true
mv install.sh scripts/setup/ 2>/dev/null || true

# Move deploy scripts
echo "Moving deploy scripts..."
mv deploy-*.py scripts/deploy/ 2>/dev/null || true
mv deploy-*.sh scripts/deploy/ 2>/dev/null || true
mv DEPLOY-*.sh scripts/deploy/ 2>/dev/null || true
mv sync-*.py scripts/deploy/ 2>/dev/null || true
mv sync-*.sh scripts/deploy/ 2>/dev/null || true
mv SYNC-*.sh scripts/deploy/ 2>/dev/null || true

# Move check scripts
echo "Moving check scripts..."
mv check-*.py scripts/check/ 2>/dev/null || true
mv check-*.sh scripts/check/ 2>/dev/null || true
mv CHECK-*.py scripts/check/ 2>/dev/null || true
mv CHECK-*.sh scripts/check/ 2>/dev/null || true
mv verify-*.py scripts/check/ 2>/dev/null || true
mv final-verify-*.py scripts/check/ 2>/dev/null || true

# Move build scripts
echo "Moving build scripts..."
mv build-*.py scripts/build/ 2>/dev/null || true
mv build-*.sh scripts/build/ 2>/dev/null || true
mv build-*.bat scripts/build/ 2>/dev/null || true
mv BUILD-*.bat scripts/build/ 2>/dev/null || true

# Move connect scripts
echo "Moving connect scripts..."
mv connect-*.sh scripts/connect/ 2>/dev/null || true
mv connect-*.py scripts/connect/ 2>/dev/null || true

# Move maintenance scripts
echo "Moving maintenance scripts..."
mv cleanup-*.py scripts/maintenance/ 2>/dev/null || true
mv cleanup-*.sh scripts/maintenance/ 2>/dev/null || true
mv aggressive-disk-cleanup.py scripts/maintenance/ 2>/dev/null || true
mv optimize-*.py scripts/maintenance/ 2>/dev/null || true
mv optimize-*.sh scripts/maintenance/ 2>/dev/null || true
mv optimize-*.bat scripts/maintenance/ 2>/dev/null || true
mv update-*.py scripts/maintenance/ 2>/dev/null || true
mv update-*.sh scripts/maintenance/ 2>/dev/null || true

# Move utility scripts
echo "Moving utility scripts..."
mv add-*.py scripts/utils/ 2>/dev/null || true
mv add-*.sh scripts/utils/ 2>/dev/null || true
mv create-*.py scripts/utils/ 2>/dev/null || true
mv get-*.py scripts/utils/ 2>/dev/null || true
mv get-*.sh scripts/utils/ 2>/dev/null || true
mv finalize-*.py scripts/utils/ 2>/dev/null || true

# Move Windows-specific scripts
mkdir -p scripts/windows
mv *.bat scripts/windows/ 2>/dev/null || true

echo ""
echo "=========================================="
echo "Script Organization Complete"
echo "=========================================="
echo ""
echo "Scripts organized into:"
echo "  scripts/setup/       - Setup and installation"
echo "  scripts/deploy/      - Deployment and sync"
echo "  scripts/check/       - Verification and checks"
echo "  scripts/build/       - Build scripts"
echo "  scripts/connect/     - Connection scripts"
echo "  scripts/maintenance/ - Cleanup and optimization"
echo "  scripts/utils/       - Utility scripts"
echo "  scripts/windows/     - Windows-specific scripts"
echo ""
